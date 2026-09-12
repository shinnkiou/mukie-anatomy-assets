from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ACTION_NAME = "csmc_observer_capture"
TARGET_EXE = "CLIPStudioModeler.exe"
SIDECAR_BASENAME = "CSMC_MODELER_OBSERVER_ONESHOT.exe"
RESULT_PREFIX = "UKIE_CSMC_OBSERVER_RESULT="
MAX_STDOUT_CHARS = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 300


class CsmcObserverActionError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _local_app_data() -> Path:
    root = os.environ.get("LOCALAPPDATA")
    if not root:
        raise CsmcObserverActionError("LOCALAPPDATA_MISSING", "LOCALAPPDATA is unavailable")
    return Path(root)


def capture_root() -> Path:
    """Fixed worker-owned output root. Cloud jobs cannot override this path."""
    return _local_app_data() / "UKIE_AI_BRIDGE" / "csmc_observer" / "captures"


def worker_binary_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def observer_sidecar_path() -> Path:
    """Fixed sidecar path. It is never supplied by a cloud job."""
    return worker_binary_dir() / SIDECAR_BASENAME


def _modeler_running_tasklist() -> bool:
    if os.name != "nt":
        return False
    completed = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {TARGET_EXE}", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        return False
    rows = list(csv.reader(completed.stdout.splitlines()))
    return any(row and row[0].strip().lower() == TARGET_EXE.lower() for row in rows)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _validated_zip(raw_path: str) -> Path:
    root = capture_root().resolve()
    candidate = Path(raw_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise CsmcObserverActionError("OBSERVER_OUTPUT_OUTSIDE_FIXED_ROOT", "observer output escaped the fixed capture root") from exc
    if candidate.suffix.lower() != ".zip" or not candidate.is_file():
        raise CsmcObserverActionError("OBSERVER_ZIP_MISSING", "observer did not produce a ZIP artifact")
    return candidate


def _parse_result(stdout: str) -> dict[str, Any]:
    if len(stdout) > MAX_STDOUT_CHARS:
        raise CsmcObserverActionError("OBSERVER_STDOUT_TOO_LARGE", "observer stdout exceeded the bounded contract")
    payload_text = None
    for line in stdout.splitlines():
        if line.startswith(RESULT_PREFIX):
            payload_text = line[len(RESULT_PREFIX):]
    if payload_text is None:
        raise CsmcObserverActionError("OBSERVER_RESULT_MISSING", "observer did not emit its bounded result record")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise CsmcObserverActionError("OBSERVER_RESULT_INVALID", "observer result JSON was invalid") from exc
    if not isinstance(payload, dict):
        raise CsmcObserverActionError("OBSERVER_RESULT_INVALID", "observer result must be an object")
    return payload


def run_capture(
    *,
    process_checker: Callable[[], bool] = _modeler_running_tasklist,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    sidecar: Path | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run one fixed, non-interactive CSMC observer capture.

    This capability intentionally accepts no cloud-supplied command, executable,
    path, key sequence, or arbitrary argument. MODELER must already be running;
    this action never launches MODELER, loads a model, changes focus, or performs
    generic keyboard/mouse automation.
    """
    if os.name != "nt" and process_checker is _modeler_running_tasklist:
        raise CsmcObserverActionError("WINDOWS_REQUIRED", "CSMC observer capture is Windows-only")
    if not process_checker():
        raise CsmcObserverActionError("MODELER_NOT_RUNNING", "CLIP STUDIO MODELER is not already running")

    tool = (sidecar or observer_sidecar_path()).resolve()
    if not tool.is_file() or tool.name != SIDECAR_BASENAME:
        raise CsmcObserverActionError("OBSERVER_SIDECAR_MISSING", "fixed one-shot observer sidecar is missing")

    root = capture_root()
    root.mkdir(parents=True, exist_ok=True)
    completed = runner(
        [str(tool), "--oneshot"],
        check=False,
        capture_output=True,
        text=True,
        timeout=max(30, min(int(timeout_seconds), DEFAULT_TIMEOUT_SECONDS)),
        cwd=str(tool.parent),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        env={**os.environ, "UKIE_CSMC_OBSERVER_CAPTURE_ROOT": str(root)},
    )
    if completed.returncode != 0:
        raise CsmcObserverActionError("OBSERVER_FAILED", f"one-shot observer exited with code {completed.returncode}")

    payload = _parse_result(completed.stdout or "")
    zip_path = _validated_zip(str(payload.get("zip_path") or ""))

    # Only bounded metadata crosses the control plane. Private capture bytes stay local.
    return {
        "schema_version": "ukie_csmc_observer_capture_v1",
        "action": ACTION_NAME,
        "target": TARGET_EXE,
        "existing_modeler_session_used": True,
        "modeler_launch_performed": False,
        "model_load_performed": False,
        "focus_change_performed": False,
        "scan_reason": str(payload.get("scan_reason") or "unknown")[:120],
        "candidate_count": max(0, int(payload.get("candidate_count") or 0)),
        "read_failures": max(0, int(payload.get("read_failures") or 0)),
        "search_seconds": max(0.0, float(payload.get("search_seconds") or 0.0)),
        "payload_dumped": bool(payload.get("payload_dumped", False)),
        "zip_name": zip_path.name,
        "zip_size": zip_path.stat().st_size,
        "zip_sha256": _sha256(zip_path),
        "artifact_transfer": "LOCAL_FIXED_ROOT_ONLY",
    }
