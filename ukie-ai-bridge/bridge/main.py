"""UKIE AI BRIDGE P0.2 executable entrypoint.

This prototype stays intentionally narrow. It exposes local diagnostics, bounded
tool discovery, frozen Tool Scout approval validation, historical failure guards,
a fail-closed pre-flight engine, artifact-contract validation, and a manual local
Blender ANALYZE_ONLY test. It does NOT accept arbitrary shell commands,
PowerShell, registry changes, arbitrary executables, or whole-PC file operations.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from bridge.validator import JobValidationError, load_and_validate, sha256_file
    from bridge.install_manifest import (
        InstallManifestError,
        validate_approval_manifest,
        validate_resolved_manifest,
    )
    from bridge.toolchain import discover_toolchain
    from bridge.known_failures import (
        classify_debugger_line,
        validate_batch_bytes,
        validate_target_identity,
    )
    from bridge.preflight import run_foundation_preflight, write_preflight_report
    from bridge.artifact_validation import (
        ArtifactValidationError,
        analyze_only_contract,
        validate_artifact_contract,
    )
except ModuleNotFoundError:
    # Direct execution (`python bridge/main.py`) puts bridge/ on sys.path instead
    # of the project root. Keep this narrow fallback so source and packaged EXE
    # entrypoints exercise the same fail-closed modules.
    from validator import JobValidationError, load_and_validate, sha256_file
    from install_manifest import (
        InstallManifestError,
        validate_approval_manifest,
        validate_resolved_manifest,
    )
    from toolchain import discover_toolchain
    from known_failures import classify_debugger_line, validate_batch_bytes, validate_target_identity
    from preflight import run_foundation_preflight, write_preflight_report
    from artifact_validation import ArtifactValidationError, analyze_only_contract, validate_artifact_contract

BRIDGE_VERSION = "0.3.0-p0.2"
PROTOCOL_VERSION = "ukie_job_v1"
BROWSER_PROTOCOL_VERSION = "ukie_browser_v1"
BP3D_BLENDER_PIN = "4.2.23"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def bundle_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


def memory_status() -> dict:
    if os.name != "nt":
        return {"supported": False}

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    if not ok:
        return {"supported": True, "error": "GlobalMemoryStatusEx failed"}
    return {
        "supported": True,
        "load_percent": int(stat.dwMemoryLoad),
        "total_bytes": int(stat.ullTotalPhys),
        "available_bytes": int(stat.ullAvailPhys),
    }


def blender_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.environ.get("UKIE_BLENDER_EXE")
    if env_path:
        candidates.append(Path(env_path))

    if os.name == "nt":
        roots = [
            os.environ.get("ProgramFiles"),
            os.environ.get("LOCALAPPDATA"),
        ]
        for root in filter(None, roots):
            base = Path(root)
            explicit = [
                base / "Blender Foundation" / "Blender 4.2" / "blender.exe",
                base / "Blender Foundation" / "Blender 4.2 LTS" / "blender.exe",
                base / "Blender Foundation" / "Blender 5.2" / "blender.exe",
            ]
            candidates.extend(explicit)
            bf = base / "Blender Foundation"
            if bf.is_dir():
                try:
                    for child in bf.iterdir():
                        candidate = child / "blender.exe"
                        candidates.append(candidate)
                except OSError:
                    pass

    seen = set()
    unique = []
    for c in candidates:
        key = str(c).lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def detect_blender() -> dict:
    for candidate in blender_candidates():
        try:
            if not candidate.is_file():
                continue
            proc = subprocess.run(
                [str(candidate), "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
                check=False,
            )
            output = (proc.stdout or proc.stderr or "").strip().splitlines()
            first = output[0] if output else ""
            return {
                "found": proc.returncode == 0,
                "path": str(candidate),
                "version_line": first,
                "return_code": proc.returncode,
            }
        except Exception as exc:
            return {"found": False, "path": str(candidate), "error": str(exc)}
    return {"found": False, "path": None, "error": "Blender executable not found in allowlisted discovery paths"}


def device_status() -> dict:
    blender = detect_blender()
    return {
        "schema_version": "ukie_device_status_v1",
        "generated_at": utc_now(),
        "bridge_version": BRIDGE_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "browser_protocol_version": BROWSER_PROTOCOL_VERSION,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(),
            "python": platform.python_version(),
        },
        "memory": memory_status(),
        "blender": blender,
        "gpu": {
            "status": "P1_NOT_IMPLEMENTED",
            "note": "P0.2 does not claim GPU_READY until Windows + Blender + render verification exists.",
        },
        "capabilities": [
            "device_status",
            "analyze_blend",
            "upload_results",
            "tool_discovery",
            "validate_install_approval",
            "validate_install_resolution",
            "preflight",
            "artifact_contract_validation",
            "known_failure_classification",
            "target_identity_guard",
            "batch_encoding_guard",
        ],
        "installation_execution": {
            "status": "NOT_IMPLEMENTED",
            "note": "P0.2 validates user-frozen manifests but does not run installers yet.",
        },
        "ready_for_ai": bool(blender.get("found")),
    }


def safe_job_dir(root: Path, job_id: str) -> Path:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    job_dir = (root / job_id).resolve()
    if root != job_dir and root not in job_dir.parents:
        raise RuntimeError("resolved job directory escaped workspace")
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def run_local_analyze(job_json: Path, local_input: Path, workspace: Path) -> dict:
    """Manual P0 fixture path for the first Windows round-trip.

    This is not a remote arbitrary-path API. The user explicitly supplies the input
    locally. The original is copied into an ASCII-named job directory and never saved.
    """
    job = load_and_validate(job_json)
    if job.action != "analyze_blend":
        raise JobValidationError("local-analyze requires action=analyze_blend")
    if local_input.suffix.lower() != ".blend":
        raise JobValidationError("local-analyze accepts only .blend input")
    if not local_input.is_file():
        raise FileNotFoundError(local_input)

    analyzer = bundle_root() / "blender" / "analyze_scene.py"
    if not analyzer.is_file():
        raise RuntimeError(f"bundled analyzer missing: {analyzer}")

    required_free = max(local_input.stat().st_size * 3 + (128 * 1024 * 1024), 256 * 1024 * 1024)
    preflight = run_foundation_preflight(
        workspace=workspace,
        input_file=local_input,
        expected_sha256=job.input_sha256,
        script_file=analyzer,
        script_mode="ANALYZE_ONLY",
        python_role="BLENDER_INTERNAL",
        required_free_bytes=required_free,
    )
    preflight_fallback = workspace / f"{job.job_id}_preflight.json"
    write_preflight_report(preflight, preflight_fallback)
    if preflight["status"] != "PASS":
        raise RuntimeError(f"preflight blocked job; report={preflight_fallback}")

    input_sha = sha256_file(local_input)
    blender = detect_blender()
    if not blender.get("found"):
        raise RuntimeError(blender.get("error") or "Blender not found")

    job_dir = safe_job_dir(workspace, job.job_id)
    preflight_path = job_dir / "preflight.json"
    write_preflight_report(preflight, preflight_path)
    input_copy = job_dir / "input.blend"
    working_copy = job_dir / "working.blend"
    scene_json = job_dir / "scene_before.json"
    stdout_log = job_dir / "stdout.log"
    stderr_log = job_dir / "stderr.log"
    manifest_path = job_dir / "manifest.json"

    shutil.copy2(local_input, input_copy)
    shutil.copy2(input_copy, working_copy)

    command = [
        blender["path"],
        "-b",
        str(working_copy),
        "--python",
        str(analyzer),
        "--",
        "--output",
        str(scene_json),
    ]

    started = utc_now()
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=job.timeout_seconds,
            check=False,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        proc = None
        timed_out = True
        stdout_log.write_text((exc.stdout or "") if isinstance(exc.stdout, str) else "", encoding="utf-8")
        stderr_log.write_text((exc.stderr or "") if isinstance(exc.stderr, str) else "", encoding="utf-8")

    if proc is not None:
        stdout_log.write_text(proc.stdout or "", encoding="utf-8", newline="\n")
        stderr_log.write_text(proc.stderr or "", encoding="utf-8", newline="\n")

    source_sha_after = sha256_file(local_input)
    source_unchanged = source_sha_after.lower() == input_sha.lower()
    artifact_validation = None
    if proc is not None and proc.returncode == 0:
        artifact_validation = validate_artifact_contract(job_dir, analyze_only_contract())

    success = bool(
        proc is not None
        and proc.returncode == 0
        and artifact_validation is not None
        and artifact_validation.get("status") == "PASS"
        and source_unchanged
    )
    manifest = {
        "schema_version": "ukie_job_manifest_v1",
        "job_id": job.job_id,
        "action": job.action,
        "mode": "ANALYZE_ONLY",
        "started_at": started,
        "finished_at": utc_now(),
        "status": "TIMEOUT" if timed_out else ("LOCAL_SAVED" if success else "FAILED"),
        "source": {
            "original_filename": job.original_filename,
            "local_input_basename": local_input.name,
            "input_sha256_before": input_sha,
            "input_sha256_after": source_sha_after,
            "source_unchanged": source_unchanged,
        },
        "copies": {
            "input": {"name": input_copy.name, "sha256": sha256_file(input_copy)},
            "working": {"name": working_copy.name, "sha256": sha256_file(working_copy)},
        },
        "preflight": preflight,
        "artifact_validation": artifact_validation,
        "blender": blender,
        "bridge_version": BRIDGE_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "process": {
            "timed_out": timed_out,
            "return_code": proc.returncode if proc is not None else None,
        },
        "artifacts": {
            "preflight": preflight_path.name,
            "scene_before": scene_json.name if scene_json.is_file() else None,
            "stdout": stdout_log.name,
            "stderr": stderr_log.name,
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _load_json(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise InstallManifestError("JSON root must be an object")
    return value


def cmd_self_test(_: argparse.Namespace) -> int:
    result = {
        "status": "PASS",
        "bridge_version": BRIDGE_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "browser_protocol_version": BROWSER_PROTOCOL_VERSION,
        "frozen": bool(getattr(sys, "frozen", False)),
        "generated_at": utc_now(),
        "safety": {
            "arbitrary_shell": False,
            "arbitrary_powershell": False,
            "arbitrary_exe": False,
            "install_execution": False,
            "frozen_install_approval_validation": True,
            "preflight_engine": True,
            "artifact_contract_validation": True,
            "known_failure_guards": True,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_device_status(_: argparse.Namespace) -> int:
    print(json.dumps(device_status(), ensure_ascii=False, indent=2))
    return 0


def cmd_tool_discovery(args: argparse.Namespace) -> int:
    result = discover_toolchain(include_hash=bool(args.hash))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_validate_job(args: argparse.Namespace) -> int:
    job = load_and_validate(args.job)
    print(json.dumps(job.__dict__, ensure_ascii=False, indent=2))
    return 0


def cmd_validate_install_manifest(args: argparse.Namespace) -> int:
    manifest = _load_json(args.manifest)
    validated = validate_approval_manifest(manifest)
    print(json.dumps({
        "status": "VALID",
        "batch_key": validated.batch_key,
        "approved_at": validated.approved_at,
        "tool_keys": list(validated.tool_keys),
        "manifest_sha256": validated.manifest_sha256,
        "requires_uac": validated.requires_uac,
        "requires_driver": validated.requires_driver,
        "installation_started": False,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_validate_resolved_manifest(args: argparse.Namespace) -> int:
    approval = _load_json(args.approval)
    resolved = _load_json(args.resolved)
    result = validate_resolved_manifest(resolved, approval)
    result["installation_started"] = False
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    report = run_foundation_preflight(
        workspace=Path(args.workspace),
        input_file=Path(args.input) if args.input else None,
        expected_sha256=args.expected_sha256,
        script_file=Path(args.script) if args.script else None,
        script_mode=args.mode,
        python_role=args.python_role,
        required_free_bytes=max(0, int(args.required_free_mb)) * 1024 * 1024,
    )
    if args.output:
        write_preflight_report(report, Path(args.output))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


def cmd_classify_debugger_line(args: argparse.Namespace) -> int:
    match = classify_debugger_line(args.line)
    payload = {"status": "NO_MATCH"} if match is None else match.__dict__
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_validate_batch(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_file():
        raise FileNotFoundError(path)
    result = validate_batch_bytes(path.read_bytes())
    result["file_basename"] = path.name
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


def cmd_validate_target(args: argparse.Namespace) -> int:
    result = validate_target_identity(
        observer_pid=args.observer_pid,
        target_pid=args.target_pid,
        target_exe_name=args.target_exe_name,
        expected_exe_name=args.expected_exe_name,
        target_path=args.target_path,
        target_sha256=args.target_sha256,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


def cmd_local_analyze(args: argparse.Namespace) -> int:
    manifest = run_local_analyze(Path(args.job), Path(args.input), Path(args.workspace))
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest["status"] == "LOCAL_SAVED" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("self-test")
    p.set_defaults(func=cmd_self_test)

    p = sub.add_parser("device-status")
    p.set_defaults(func=cmd_device_status)

    p = sub.add_parser("tool-discovery")
    p.add_argument("--hash", action="store_true", help="Also hash discovered executable files")
    p.set_defaults(func=cmd_tool_discovery)

    p = sub.add_parser("validate-job")
    p.add_argument("job")
    p.set_defaults(func=cmd_validate_job)

    p = sub.add_parser("validate-install-manifest")
    p.add_argument("manifest")
    p.set_defaults(func=cmd_validate_install_manifest)

    p = sub.add_parser("validate-resolved-manifest")
    p.add_argument("--approval", required=True)
    p.add_argument("--resolved", required=True)
    p.set_defaults(func=cmd_validate_resolved_manifest)

    p = sub.add_parser("preflight")
    p.add_argument("--workspace", required=True)
    p.add_argument("--input")
    p.add_argument("--expected-sha256")
    p.add_argument("--script")
    p.add_argument("--mode", default="ANALYZE_ONLY")
    p.add_argument("--python-role", default="BLENDER_INTERNAL")
    p.add_argument("--required-free-mb", type=int, default=0)
    p.add_argument("--output")
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("classify-debugger-line")
    p.add_argument("line")
    p.set_defaults(func=cmd_classify_debugger_line)

    p = sub.add_parser("validate-batch")
    p.add_argument("file")
    p.set_defaults(func=cmd_validate_batch)

    p = sub.add_parser("validate-target")
    p.add_argument("--observer-pid", type=int, required=True)
    p.add_argument("--target-pid", type=int, required=True)
    p.add_argument("--target-exe-name", required=True)
    p.add_argument("--expected-exe-name", default="CLIPStudioModeler.exe")
    p.add_argument("--target-path", required=True)
    p.add_argument("--target-sha256")
    p.set_defaults(func=cmd_validate_target)

    p = sub.add_parser("local-analyze")
    p.add_argument("--job", required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--workspace", required=True)
    p.set_defaults(func=cmd_local_analyze)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except (JobValidationError, InstallManifestError, ArtifactValidationError, FileNotFoundError, RuntimeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc), "bridge_version": BRIDGE_VERSION}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
