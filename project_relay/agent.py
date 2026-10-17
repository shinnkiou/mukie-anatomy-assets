from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
RUNTIME = BASE / "runtime"
INBOX = RUNTIME / "queue" / "inbox"
PROCESSING = RUNTIME / "queue" / "processing"
REJECTED = RUNTIME / "queue" / "rejected"
JOBS = RUNTIME / "jobs"
AGENT_STOP = RUNTIME / "STOP_AGENT"
CONFIG_DEFAULT = BASE / "config" / "runners.json"
CONFIG_EXAMPLE = BASE / "config" / "runners.example.json"
COMMAND_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,120}$")
FINAL_STATES = {"SUCCESS", "FAILED", "BLOCKED", "INCOMPLETE", "STOPPED"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_deadline(value: Any) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("deadline must include timezone offset")
    return dt


def expand(value: str, context: dict[str, str]) -> str:
    return value.format_map(context)


def ensure_runtime() -> None:
    for p in (INBOX, PROCESSING, REJECTED, JOBS):
        p.mkdir(parents=True, exist_ok=True)
    if not CONFIG_DEFAULT.exists() and CONFIG_EXAMPLE.exists():
        shutil.copy2(CONFIG_EXAMPLE, CONFIG_DEFAULT)


def load_runners(config_path: Path) -> dict[str, Any]:
    raw = load_json(config_path)
    runners = raw.get("runners")
    if not isinstance(runners, dict) or not runners:
        raise ValueError("config has no runners")
    return runners


def write_status(job_dir: Path, status: str, **extra: Any) -> None:
    current: dict[str, Any] = {}
    path = job_dir / "job_state.json"
    if path.exists():
        try:
            current = load_json(path)
        except Exception:
            current = {}
    current.update(extra)
    current["status"] = status
    current["updated_at"] = now_iso()
    atomic_json(path, current)


def pump_stream(stream: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", errors="replace", buffering=1) as out:
        while True:
            line = stream.readline()
            if line == "":
                break
            out.write(line)
            out.flush()


def kill_process_tree(proc: subprocess.Popen[str], force: bool) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        args = ["taskkill", "/PID", str(proc.pid), "/T"]
        if force:
            args.append("/F")
        subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGKILL if force else signal.SIGTERM)
    except ProcessLookupError:
        pass


def marker_state(paths: list[Path]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for p in paths:
        item: dict[str, Any] = {"path": str(p), "exists": p.exists()}
        if p.is_file():
            try:
                item["size"] = p.stat().st_size
                item["mtime"] = datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat()
            except OSError:
                pass
        result.append(item)
    return result


def validate_fresh_outputs(paths: list[Path], started_epoch: float) -> tuple[bool, list[dict[str, Any]]]:
    evidence = marker_state(paths)
    ok = True
    for item in evidence:
        if not item.get("exists"):
            ok = False
            continue
        p = Path(item["path"])
        try:
            # one-second tolerance for filesystems with coarse timestamps
            if p.stat().st_mtime < started_epoch - 1.0:
                item["fresh"] = False
                ok = False
            else:
                item["fresh"] = True
        except OSError:
            item["fresh"] = False
            ok = False
    return ok, evidence


def collect_stop_request(stop_path: Path) -> str | None:
    if not stop_path.exists():
        return None
    try:
        data = load_json(stop_path)
        return str(data.get("mode", "SOFT")).upper()
    except Exception:
        return "SOFT"


def request_stop(stop_path: Path, mode: str, reason: str) -> None:
    if stop_path.exists():
        return
    atomic_json(stop_path, {"mode": mode.upper(), "reason": reason, "requested_at": now_iso()})


def preflight(job: dict[str, Any], runner: dict[str, Any], job_dir: Path) -> tuple[bool, list[str], dict[str, str]]:
    errors: list[str] = []
    input_obj = job.get("input") or {}
    input_path = input_obj.get("path")
    context = {
        "job_dir": str(job_dir.resolve()),
        "input_path": str(Path(input_path).expanduser().resolve()) if input_path else "",
        "project": str(job.get("project", "")),
        "command_id": str(job.get("command_id", "")),
    }

    argv = runner.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
        errors.append("runner.argv must be a non-empty string array")

    success_markers = runner.get("success_markers") or []
    required_outputs = runner.get("required_outputs") or []
    if not success_markers and not required_outputs:
        errors.append("runner must define success_markers or required_outputs; exit-code-only success is prohibited")

    if input_path and not Path(context["input_path"]).exists():
        errors.append(f"input path does not exist: {context['input_path']}")

    for raw in runner.get("required_inputs") or []:
        p = Path(expand(str(raw), context))
        if not p.exists():
            errors.append(f"required input missing: {p}")

    try:
        parse_deadline(job.get("deadline"))
    except Exception as exc:
        errors.append(f"invalid deadline: {exc}")

    return (not errors), errors, context


def run_job(job_path: Path, runners: dict[str, Any]) -> None:
    job = load_json(job_path)
    command_id = str(job.get("command_id", ""))
    if not COMMAND_ID_RE.fullmatch(command_id):
        raise ValueError("invalid command_id")

    job_dir = JOBS / command_id
    job_dir.mkdir(parents=True, exist_ok=True)
    state_path = job_dir / "job_state.json"
    if state_path.exists():
        old = load_json(state_path)
        if old.get("status") in FINAL_STATES:
            raise RuntimeError(f"duplicate command_id already finalized: {command_id}")

    (job_dir / "logs").mkdir(exist_ok=True)
    (job_dir / "result").mkdir(exist_ok=True)
    (job_dir / "error").mkdir(exist_ok=True)
    shutil.copy2(job_path, job_dir / "command.json")

    runner_name = str(job.get("runner", ""))
    runner = runners.get(runner_name)
    if not isinstance(runner, dict):
        write_status(job_dir, "BLOCKED", command_id=command_id, runner=runner_name, reason="RUNNER_NOT_ALLOWLISTED")
        atomic_json(job_dir / "error" / "error.json", {"reason": "RUNNER_NOT_ALLOWLISTED", "runner": runner_name})
        return

    ok, errors, context = preflight(job, runner, job_dir)
    if not ok:
        write_status(job_dir, "BLOCKED", command_id=command_id, runner=runner_name, preflight_errors=errors)
        atomic_json(job_dir / "error" / "error.json", {"reason": "PREFLIGHT_FAILED", "errors": errors})
        return

    argv = [expand(x, context) for x in runner["argv"]]
    cwd_raw = runner.get("cwd")
    cwd = Path(expand(str(cwd_raw), context)).resolve() if cwd_raw else BASE
    if not cwd.exists():
        write_status(job_dir, "BLOCKED", command_id=command_id, reason=f"cwd missing: {cwd}")
        return

    env = os.environ.copy()
    for k, v in (runner.get("env") or {}).items():
        env[str(k)] = expand(str(v), context)
    stop_path = job_dir / "STOP_REQUESTED.json"
    env.update({
        "PROJECT_RELAY_COMMAND_ID": command_id,
        "PROJECT_RELAY_JOB_DIR": str(job_dir.resolve()),
        "PROJECT_RELAY_STOP_FILE": str(stop_path.resolve()),
    })

    success_paths = [Path(expand(str(x), context)) for x in (runner.get("success_markers") or [])]
    failure_paths = [Path(expand(str(x), context)) for x in (runner.get("failure_markers") or [])]
    output_paths = [Path(expand(str(x), context)) for x in (runner.get("required_outputs") or [])]

    started_epoch = time.time()
    started_at = now_iso()
    write_status(
        job_dir,
        "RUNNING",
        command_id=command_id,
        project=job.get("project"),
        runner=runner_name,
        started_at=started_at,
        argv=argv,
        cwd=str(cwd),
    )

    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    proc = subprocess.Popen(
        argv,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        shell=False,
        creationflags=creationflags,
        start_new_session=(os.name != "nt"),
    )

    stdout_thread = threading.Thread(target=pump_stream, args=(proc.stdout, job_dir / "logs" / "stdout.log"), daemon=True)
    stderr_thread = threading.Thread(target=pump_stream, args=(proc.stderr, job_dir / "logs" / "stderr.log"), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    deadline = parse_deadline(job.get("deadline"))
    deadline_mode = str(job.get("stop_mode_at_deadline", "SOFT")).upper()
    grace = max(0, int(runner.get("stop_grace_seconds", 15)))
    allow_hard = bool(runner.get("allow_hard_after_soft", True))
    stop_seen_at: float | None = None
    stop_mode: str | None = None
    stop_reason: str | None = None

    while proc.poll() is None:
        atomic_json(job_dir / "heartbeat.json", {
            "command_id": command_id,
            "pid": proc.pid,
            "status": "RUNNING" if not stop_mode else "STOPPING",
            "updated_at": now_iso(),
        })

        if deadline and datetime.now(timezone.utc) >= deadline.astimezone(timezone.utc) and not stop_path.exists():
            request_stop(stop_path, deadline_mode, "deadline")

        observed_mode = collect_stop_request(stop_path)
        if observed_mode and not stop_mode:
            stop_mode = observed_mode if observed_mode in {"SOFT", "HARD", "EMERGENCY"} else "SOFT"
            stop_reason = "external_or_deadline_request"
            stop_seen_at = time.time()
            write_status(job_dir, "STOPPING", stop_mode=stop_mode, stop_requested_at=now_iso())
            if stop_mode == "HARD":
                kill_process_tree(proc, force=False)
            elif stop_mode == "EMERGENCY":
                kill_process_tree(proc, force=True)

        if stop_mode == "SOFT" and stop_seen_at is not None and proc.poll() is None:
            if time.time() - stop_seen_at >= grace and allow_hard:
                kill_process_tree(proc, force=True)
                stop_mode = "HARD_AFTER_SOFT_TIMEOUT"

        time.sleep(1.0)

    stdout_thread.join(timeout=5)
    stderr_thread.join(timeout=5)
    rc = proc.returncode

    failure_evidence = marker_state(failure_paths)
    failure_marker_present = any(x.get("exists") for x in failure_evidence)
    success_ok, success_evidence = validate_fresh_outputs(success_paths, started_epoch) if success_paths else (True, [])
    outputs_ok, output_evidence = validate_fresh_outputs(output_paths, started_epoch) if output_paths else (True, [])

    if stop_mode:
        final_status = "STOPPED"
    elif rc == 0 and not failure_marker_present and success_ok and outputs_ok:
        final_status = "SUCCESS"
    else:
        final_status = "FAILED"

    result = {
        "schema": "project-relay-result-v1",
        "command_id": command_id,
        "project": job.get("project"),
        "runner": runner_name,
        "status": final_status,
        "started_at": started_at,
        "finished_at": now_iso(),
        "exit_code": rc,
        "pid": proc.pid,
        "stop_mode": stop_mode,
        "stop_reason": stop_reason,
        "success_markers": success_evidence,
        "failure_markers": failure_evidence,
        "required_outputs": output_evidence,
        "logs": {
            "stdout": str((job_dir / "logs" / "stdout.log").resolve()),
            "stderr": str((job_dir / "logs" / "stderr.log").resolve()),
        },
    }
    atomic_json(job_dir / "result" / "result.json", result)

    if final_status == "SUCCESS":
        (job_dir / "result" / "SUCCESS").write_text("SUCCESS\n", encoding="ascii")
    elif final_status == "FAILED":
        (job_dir / "error" / "FAILED").write_text("FAILED\n", encoding="ascii")
        atomic_json(job_dir / "error" / "error.json", result)
    elif final_status == "STOPPED":
        atomic_json(job_dir / "checkpoint.json", {
            "command_id": command_id,
            "status": "STOPPED",
            "resume_supported": bool(job.get("resume", False)),
            "stopped_at": now_iso(),
        })

    write_status(job_dir, final_status, exit_code=rc, stop_mode=stop_mode, finished_at=now_iso())


def reject(path: Path, exc: BaseException) -> None:
    REJECTED.mkdir(parents=True, exist_ok=True)
    target = REJECTED / path.name
    try:
        if path.exists():
            os.replace(path, target)
    except OSError:
        target = path
    atomic_json(target.with_suffix(target.suffix + ".error.json"), {
        "error": repr(exc),
        "traceback": traceback.format_exc(),
        "rejected_at": now_iso(),
    })


def process_one(path: Path, runners: dict[str, Any]) -> None:
    claimed = PROCESSING / path.name
    try:
        os.replace(path, claimed)
        run_job(claimed, runners)
        claimed.unlink(missing_ok=True)
    except BaseException as exc:
        reject(claimed if claimed.exists() else path, exc)


def agent_loop(config_path: Path, poll_seconds: float) -> None:
    ensure_runtime()
    runners = load_runners(config_path)
    atomic_json(RUNTIME / "agent_state.json", {"status": "ONLINE", "pid": os.getpid(), "started_at": now_iso()})
    AGENT_STOP.unlink(missing_ok=True)

    while not AGENT_STOP.exists():
        atomic_json(RUNTIME / "agent_heartbeat.json", {"status": "ONLINE", "pid": os.getpid(), "updated_at": now_iso()})
        for path in sorted(INBOX.glob("*.json"), key=lambda p: p.stat().st_mtime):
            process_one(path, runners)
            if AGENT_STOP.exists():
                break
        time.sleep(poll_seconds)

    atomic_json(RUNTIME / "agent_state.json", {"status": "STOPPED", "pid": os.getpid(), "stopped_at": now_iso()})


def submit_selftest() -> Path:
    ensure_runtime()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    command_id = f"selftest-{stamp}"
    path = INBOX / f"{command_id}.json"
    atomic_json(path, {
        "schema": "project-relay-job-v1",
        "command_id": command_id,
        "project": "project_relay",
        "action": "run",
        "runner": "selftest",
        "deadline": None,
        "resume": False,
    })
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="PROJECT RELAY AGENT bootstrap")
    parser.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    parser.add_argument("--poll", type=float, default=2.0)
    parser.add_argument("--selftest", action="store_true", help="enqueue a self-test command and exit")
    args = parser.parse_args()

    ensure_runtime()
    if args.selftest:
        print(submit_selftest())
        return 0
    try:
        agent_loop(args.config, max(0.2, args.poll))
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
