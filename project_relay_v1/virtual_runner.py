#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List

SCHEMA_VERSION = "relay-virtual-job-v1"
RUNNER_KEY = "VIRTUAL_FLOW_V1"
MAX_REPAIRS_HARD = 3
ALLOWED_ACTIONS = {"WRITE_TEXT", "WRITE_JSON", "VALIDATE_EXISTS", "VALIDATE_NONZERO", "PACKAGE_ZIP"}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def bounded_path(root: Path, rel: str) -> Path:
    if not rel or rel.startswith(("/", "\\")) or ":" in rel:
        raise ValueError(f"unsafe relative path: {rel!r}")
    out = (root / rel).resolve()
    rr = root.resolve()
    if out != rr and rr not in out.parents:
        raise ValueError(f"path escapes output root: {rel!r}")
    return out


def validate_job(job: Dict[str, Any]) -> None:
    required = ["schema_version", "command_id", "project_key", "runner", "actions"]
    missing = [k for k in required if not job.get(k)]
    if missing:
        raise ValueError("missing required fields: " + ", ".join(missing))
    if job["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    if job["runner"] != RUNNER_KEY:
        raise ValueError(f"runner must be {RUNNER_KEY}")
    if not isinstance(job["actions"], list):
        raise ValueError("actions must be a list")
    for action in job["actions"]:
        if action.get("type") not in ALLOWED_ACTIONS:
            raise ValueError(f"action not allowlisted: {action.get('type')!r}")


def classify_failure(exc: Exception) -> str:
    msg = str(exc).lower()
    if "missing required" in msg or "schema" in msg:
        return "INPUT"
    if "unsafe" in msg or "escapes" in msg or "allowlisted" in msg:
        return "RUNNER"
    if "does not exist" in msg or "zero-byte" in msg:
        return "OUTPUT"
    if "zip" in msg:
        return "VALIDATION"
    return "UNKNOWN"


def build_repair_plan(job: Dict[str, Any], failure_class: str, attempt_no: int) -> Dict[str, Any] | None:
    if attempt_no >= min(int(job.get("auto_repair_limit", 1)), MAX_REPAIRS_HARD) + 1:
        return None
    rel = job.get("required_output", "result/result.txt")
    if failure_class == "OUTPUT" and job.get("repair_hint") == "CREATE_MISSING_REQUIRED_OUTPUT":
        return {
            "created_by": "RULE_ENGINE",
            "diagnosis": "必須成果物が存在しないためvalidationに失敗した。",
            "changes": [{"op": "prepend_action", "action": {"type": "WRITE_TEXT", "path": rel, "text": "auto-repaired virtual artifact\n"}}],
            "safety_checks": ["bounded output path", "no arbitrary shell", "no source-of-truth modification"],
            "confidence": 0.98,
        }
    if failure_class == "OUTPUT" and job.get("repair_hint") == "REWRITE_ZERO_BYTE":
        return {
            "created_by": "RULE_ENGINE",
            "diagnosis": "必須成果物がzero-byteのためvalidationに失敗した。",
            "changes": [{"op": "prepend_action", "action": {"type": "WRITE_TEXT", "path": rel, "text": "auto-repaired nonzero artifact\n"}}],
            "safety_checks": ["bounded output path", "no policy weakening"],
            "confidence": 0.98,
        }
    return None


def apply_repair(job: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    repaired = json.loads(json.dumps(job))
    for change in plan.get("changes", []):
        if change.get("op") == "prepend_action" and change.get("action"):
            repaired["actions"].insert(0, change["action"])
        elif change.get("op") == "append_action" and change.get("action"):
            repaired["actions"].append(change["action"])
        else:
            raise ValueError(f"unsupported repair operation: {change.get('op')}")
    return repaired


def execute_actions(job: Dict[str, Any], out_root: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for idx, action in enumerate(job["actions"], 1):
        t = action["type"]
        event = {"seq": idx, "type": t, "started_at": now_iso()}
        if t == "WRITE_TEXT":
            p = bounded_path(out_root, action["path"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(action.get("text", "")), encoding="utf-8")
            event.update({"path": action["path"], "size_bytes": p.stat().st_size})
        elif t == "WRITE_JSON":
            p = bounded_path(out_root, action["path"])
            atomic_json(p, action.get("data", {}))
            event.update({"path": action["path"], "size_bytes": p.stat().st_size})
        elif t == "VALIDATE_EXISTS":
            p = bounded_path(out_root, action["path"])
            if not p.exists():
                raise FileNotFoundError(f"required output does not exist: {action['path']}")
            event.update({"path": action["path"], "exists": True})
        elif t == "VALIDATE_NONZERO":
            p = bounded_path(out_root, action["path"])
            if not p.exists():
                raise FileNotFoundError(f"required output does not exist: {action['path']}")
            if p.stat().st_size <= 0:
                raise ValueError(f"zero-byte output: {action['path']}")
            event.update({"path": action["path"], "size_bytes": p.stat().st_size})
        elif t == "PACKAGE_ZIP":
            p = bounded_path(out_root, action.get("path", "RESULTS.zip"))
            p.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(p, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for rel in action.get("include", []):
                    src = bounded_path(out_root, rel)
                    if not src.exists() or not src.is_file():
                        raise FileNotFoundError(f"zip input does not exist: {rel}")
                    zf.write(src, arcname=rel)
            with zipfile.ZipFile(p, "r") as zf:
                bad = zf.testzip()
                if bad:
                    raise ValueError(f"zip reopen validation failed: {bad}")
            event.update({"path": action.get("path", "RESULTS.zip"), "size_bytes": p.stat().st_size, "sha256": sha256_file(p)})
        event["finished_at"] = now_iso()
        events.append(event)
    return events


def run(job: Dict[str, Any], base_root: Path) -> Dict[str, Any]:
    validate_job(job)
    command_id = job["command_id"]
    job_root = base_root.resolve() / command_id
    if job_root.exists():
        shutil.rmtree(job_root)
    job_root.mkdir(parents=True, exist_ok=True)
    lifecycle: Dict[str, Any] = {
        "schema_version": "relay-virtual-result-v1",
        "command_id": command_id,
        "project_key": job["project_key"],
        "runner": RUNNER_KEY,
        "virtual": True,
        "started_at": now_iso(),
        "attempts": [],
        "failures": [],
        "repair_plans": [],
        "final_status": "RUNNING",
    }
    current_job = job
    max_attempts = 1 + min(int(job.get("auto_repair_limit", 1)), MAX_REPAIRS_HARD)
    for attempt_no in range(1, max_attempts + 1):
        attempt_root = job_root / f"attempt_{attempt_no:02d}"
        attempt_root.mkdir(parents=True, exist_ok=True)
        attempt = {"attempt_no": attempt_no, "attempt_key": f"{command_id}-attempt-{attempt_no:02d}", "status": "RUNNING", "started_at": now_iso(), "events": []}
        lifecycle["attempts"].append(attempt)
        try:
            attempt["events"] = execute_actions(current_job, attempt_root)
            attempt["status"] = "SUCCESS"
            attempt["finished_at"] = now_iso()
            lifecycle["final_status"] = "SUCCESS"
            lifecycle["successful_attempt"] = attempt_no
            break
        except Exception as exc:
            failure_class = classify_failure(exc)
            attempt.update({"status": "FAILED", "error_class": failure_class, "error_summary": str(exc), "finished_at": now_iso()})
            failure_key = f"{command_id}-failure-{attempt_no:02d}"
            failure = {"failure_key": failure_key, "attempt_no": attempt_no, "failure_class": failure_class, "summary": str(exc), "status": "OPEN", "created_at": now_iso()}
            lifecycle["failures"].append(failure)
            plan = build_repair_plan(current_job, failure_class, attempt_no)
            if not plan:
                failure["status"] = "ESCALATED"
                lifecycle["final_status"] = "FAILED"
                lifecycle["escalation_reason"] = "no safe allowlisted repair plan"
                break
            plan_key = f"{command_id}-repair-{attempt_no:02d}"
            plan.update({"plan_key": plan_key, "failure_key": failure_key, "status": "APPROVED_AUTO", "created_at": now_iso()})
            lifecycle["repair_plans"].append(plan)
            failure.update({"status": "RETRYING", "repair_plan_key": plan_key})
            current_job = apply_repair(current_job, plan)
    lifecycle["finished_at"] = now_iso()
    final_dir = job_root / "final"
    final_dir.mkdir(exist_ok=True)
    result_path = final_dir / "result.json"
    atomic_json(result_path, lifecycle)
    marker = final_dir / ("SUCCESS" if lifecycle["final_status"] == "SUCCESS" else "FAILED")
    marker.write_text(lifecycle["final_status"] + "\n", encoding="utf-8")
    manifest = {"command_id": command_id, "files": [{"path": "result.json", "size_bytes": result_path.stat().st_size, "sha256": sha256_file(result_path)}, {"path": marker.name, "size_bytes": marker.stat().st_size, "sha256": sha256_file(marker)}]}
    atomic_json(final_dir / "artifact_manifest.json", manifest)
    return lifecycle


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--root", default="artifacts/project_relay_virtual")
    args = ap.parse_args()
    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    lifecycle = run(job, Path(args.root))
    print(json.dumps(lifecycle, ensure_ascii=False, indent=2))
    return 0 if lifecycle["final_status"] == "SUCCESS" else 2


if __name__ == "__main__":
    sys.exit(main())
