from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Callable, Iterable

ACTION_NAME = "csmc_observer_capture"
TARGET_EXE = "CLIPStudioModeler.exe"
SIDECAR_BASENAME = "BP3D_ModelerObserver_P4_1.ps1"
POWERSHELL_EXE = "powershell.exe"
CAPTURE_DIRNAME = "BP3D_ModelerObserver_P4_1_Captures"
CAPTURE_GLOB = "CAPTURE_*_P4_1.zip"
MAX_METADATA_BYTES = 256 * 1024
DEFAULT_TIMEOUT_SECONDS = 300


class CsmcObserverActionError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def worker_binary_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def observer_sidecar_path() -> Path:
    """Fixed sidecar path. It is never supplied by a cloud job."""
    return worker_binary_dir() / SIDECAR_BASENAME


def capture_roots() -> list[Path]:
    """Roots hard-coded by P4.1. Cloud jobs cannot override them."""
    roots: list[Path] = []
    user = os.environ.get("USERPROFILE")
    if user:
        desktop = Path(user) / "Desktop"
        if desktop.exists():
            roots.append(desktop / CAPTURE_DIRNAME)
    temp = os.environ.get("TEMP")
    if temp:
        roots.append(Path(temp) / CAPTURE_DIRNAME)
    # Preserve order while removing duplicates.
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root.resolve(strict=False)).lower()
        if key not in seen:
            seen.add(key)
            out.append(root)
    if not out:
        raise CsmcObserverActionError("CAPTURE_ROOT_UNAVAILABLE", "fixed P4.1 capture roots are unavailable")
    return out


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


def _zip_snapshot(roots: Iterable[Path]) -> dict[str, tuple[int, int]]:
    snap: dict[str, tuple[int, int]] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.glob(CAPTURE_GLOB):
            try:
                st = path.stat()
            except OSError:
                continue
            snap[str(path.resolve())] = (st.st_size, st.st_mtime_ns)
    return snap


def _new_zip(before: dict[str, tuple[int, int]], roots: Iterable[Path]) -> Path:
    after = _zip_snapshot(roots)
    changed: list[Path] = []
    for raw, sig in after.items():
        if before.get(raw) != sig:
            changed.append(Path(raw))
    if not changed:
        raise CsmcObserverActionError("OBSERVER_ZIP_MISSING", "P4.1 observer did not create a new capture ZIP")
    changed.sort(key=lambda p: p.stat().st_mtime_ns, reverse=True)
    newest_time = changed[0].stat().st_mtime_ns
    newest = [p for p in changed if p.stat().st_mtime_ns == newest_time]
    if len(newest) != 1:
        raise CsmcObserverActionError("OBSERVER_ZIP_AMBIGUOUS", "multiple new P4.1 ZIP artifacts have the same newest timestamp")
    return newest[0]


def _read_zip_json(zf: zipfile.ZipFile, basename: str) -> dict[str, Any]:
    matches = [n for n in zf.namelist() if Path(n).name == basename]
    if len(matches) != 1:
        raise CsmcObserverActionError("OBSERVER_METADATA_MISSING", f"ZIP must contain exactly one {basename}")
    info = zf.getinfo(matches[0])
    if info.file_size > MAX_METADATA_BYTES:
        raise CsmcObserverActionError("OBSERVER_METADATA_TOO_LARGE", f"{basename} exceeded metadata cap")
    raw = zf.read(info)
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CsmcObserverActionError("OBSERVER_METADATA_INVALID", f"{basename} is invalid JSON") from exc
    if not isinstance(value, dict):
        raise CsmcObserverActionError("OBSERVER_METADATA_INVALID", f"{basename} must contain an object")
    return value


def _bounded_metadata(zip_path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            diag = _read_zip_json(zf, "runtime_memory_diagnostic.json")
            manifest = _read_zip_json(zf, "capture_manifest.json")
    except zipfile.BadZipFile as exc:
        raise CsmcObserverActionError("OBSERVER_ZIP_INVALID", "P4.1 output is not a valid ZIP") from exc
    return {
        "scan_reason": str(diag.get("search_reason") or "unknown")[:120],
        "candidate_count": max(0, int(diag.get("accepted_count") or 0)),
        "magic_hit_count": max(0, int(diag.get("magic_hit_count") or 0)),
        "read_failures": max(0, int(diag.get("search_failures") or 0)),
        "search_seconds": max(0.0, float(diag.get("search_seconds") or 0.0)),
        "payload_dumped": bool(manifest.get("contains_private_runtime_payload", False)),
        "observer_version": str(manifest.get("version") or "unknown")[:80],
    }


def run_capture(
    *,
    process_checker: Callable[[], bool] = _modeler_running_tasklist,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    sidecar: Path | None = None,
    roots: list[Path] | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run the fixed P4.1 AUTO observer and detect its new ZIP.

    The cloud job supplies only the action name. It cannot provide a command,
    executable, filesystem path, argument, key sequence, model path, or upload
    destination. MODELER must already be running. P4.1 performs its own read-only
    attach/scan/package flow, so no B/Q keyboard automation is needed.
    """
    if os.name != "nt" and process_checker is _modeler_running_tasklist:
        raise CsmcObserverActionError("WINDOWS_REQUIRED", "CSMC observer capture is Windows-only")
    if not process_checker():
        raise CsmcObserverActionError("MODELER_NOT_RUNNING", "CLIP STUDIO MODELER is not already running")

    tool = (sidecar or observer_sidecar_path()).resolve()
    if not tool.is_file() or tool.name != SIDECAR_BASENAME:
        raise CsmcObserverActionError("OBSERVER_SIDECAR_MISSING", "fixed P4.1 observer sidecar is missing")

    fixed_roots = roots if roots is not None else capture_roots()
    before = _zip_snapshot(fixed_roots)
    completed = runner(
        [
            POWERSHELL_EXE,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(tool),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=max(30, min(int(timeout_seconds), DEFAULT_TIMEOUT_SECONDS)),
        cwd=str(tool.parent),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        raise CsmcObserverActionError("OBSERVER_FAILED", f"P4.1 observer exited with code {completed.returncode}")

    zip_path = _new_zip(before, fixed_roots)
    meta = _bounded_metadata(zip_path)

    # Only bounded metadata crosses the control plane. Private ZIP/runtime bytes stay local.
    return {
        "schema_version": "ukie_csmc_observer_capture_v2",
        "action": ACTION_NAME,
        "target": TARGET_EXE,
        "existing_modeler_session_used": True,
        "modeler_launch_performed": False,
        "model_load_performed": False,
        "focus_change_performed": False,
        "observer_launch_automated": True,
        "b_q_input_required": False,
        "zip_detection_automated": True,
        **meta,
        "zip_name": zip_path.name,
        "zip_size": zip_path.stat().st_size,
        "zip_sha256": _sha256(zip_path),
        "artifact_transfer": "LOCAL_FIXED_ROOT_ONLY",
    }
