"""Fixed read-only diagnose_v1 action for the isolated CSMC canary.

No cloud-supplied path, command, argument, process name, or key sequence is
accepted. The sidecar uses the existing MODELER session and writes only bounded
diagnostic metadata; it never dumps runtime payload bytes.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

ACTION_NAME = "csmc_observer_diagnose_v1"
TARGET_PROCESS = "CLIPStudioModeler.exe"
SIDECAR_NAME = "BP3D_ModelerObserver_P4_1_DIAG_V1.ps1"
CAPTURE_GLOB = "CAPTURE_*_P4_1_DIAG.zip"
STAGING_SUBDIR = Path("UKIE_AI_BRIDGE") / "csmc-canary" / "artifacts"

class CsmcObserverDiagnoseError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sidecar_path() -> Path:
    roots = []
    if getattr(sys, "frozen", False):
        roots.append(Path(sys.executable).resolve().parent)
    roots.extend([Path.cwd(), Path(__file__).resolve().parents[1]])
    for root in roots:
        p = root / SIDECAR_NAME
        if p.is_file():
            return p
    raise CsmcObserverDiagnoseError("CSMC_DIAG_SIDECAR_MISSING", "fixed diagnose_v1 sidecar is missing")


def _capture_roots() -> list[Path]:
    roots: list[Path] = []
    profile = os.environ.get("USERPROFILE")
    temp = os.environ.get("TEMP")
    if profile:
        roots.append(Path(profile) / "Desktop" / "BP3D_ModelerObserver_P4_1_Captures")
    if temp:
        roots.append(Path(temp) / "BP3D_ModelerObserver_P4_1_Captures")
    return roots


def _snapshot() -> dict[Path, tuple[int, int]]:
    out: dict[Path, tuple[int, int]] = {}
    for root in _capture_roots():
        if not root.is_dir():
            continue
        for p in root.glob(CAPTURE_GLOB):
            if p.is_file():
                st = p.stat(); out[p.resolve()] = (st.st_mtime_ns, st.st_size)
    return out


def _new_zip(before: dict[Path, tuple[int, int]]) -> Path:
    candidates: list[Path] = []
    for root in _capture_roots():
        if not root.is_dir():
            continue
        for p in root.glob(CAPTURE_GLOB):
            if not p.is_file():
                continue
            rp = p.resolve(); st = p.stat()
            old = before.get(rp)
            if old is None or old != (st.st_mtime_ns, st.st_size):
                candidates.append(rp)
    if len(candidates) != 1:
        raise CsmcObserverDiagnoseError("CSMC_DIAG_OUTPUT_AMBIGUOUS", f"expected exactly one new diagnostic ZIP, got {len(candidates)}")
    return candidates[0]


def _read_json(z: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        raw = z.read(name)
    except KeyError as exc:
        raise CsmcObserverDiagnoseError("CSMC_DIAG_METADATA_MISSING", f"missing {name}") from exc
    if len(raw) > 256 * 1024:
        raise CsmcObserverDiagnoseError("CSMC_DIAG_METADATA_TOO_LARGE", f"{name} is too large")
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise CsmcObserverDiagnoseError("CSMC_DIAG_METADATA_INVALID", f"invalid {name}") from exc
    if not isinstance(value, dict):
        raise CsmcObserverDiagnoseError("CSMC_DIAG_METADATA_INVALID", f"{name} root must be object")
    return value


def _stage_fixed(zip_path: Path) -> tuple[Path, str]:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise CsmcObserverDiagnoseError("CSMC_LOCALAPPDATA_MISSING", "LOCALAPPDATA is unavailable")
    root = (Path(local) / STAGING_SUBDIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / zip_path.name).resolve()
    if target.parent != root:
        raise CsmcObserverDiagnoseError("CSMC_STAGE_PATH_REJECTED", "staging path escaped fixed root")
    expected = _sha256(zip_path)
    if target.exists():
        if target.is_file() and target.stat().st_size == zip_path.stat().st_size and _sha256(target) == expected:
            return target, expected
        raise CsmcObserverDiagnoseError("CSMC_STAGE_COLLISION", "different artifact already exists at fixed staging name")
    partial = target.with_name(target.name + ".partial")
    if partial.exists(): partial.unlink()
    shutil.copyfile(zip_path, partial)
    if partial.stat().st_size != zip_path.stat().st_size or _sha256(partial) != expected:
        partial.unlink(missing_ok=True)
        raise CsmcObserverDiagnoseError("CSMC_STAGE_VERIFY_FAILED", "fixed-root staging hash/size mismatch")
    os.replace(partial, target)
    return target, expected


def run_diagnose() -> dict[str, Any]:
    sidecar = _sidecar_path()
    before = _snapshot()
    powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    if not powershell.is_file():
        raise CsmcObserverDiagnoseError("CSMC_POWERSHELL_MISSING", "fixed Windows PowerShell path is unavailable")
    completed = subprocess.run(
        [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(sidecar)],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=360, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "diagnose_v1 failed").strip()[-1200:]
        raise CsmcObserverDiagnoseError("CSMC_DIAG_SIDECAR_FAILED", detail)
    zip_path = _new_zip(before)
    with zipfile.ZipFile(zip_path, "r") as z:
        diag = _read_json(z, "runtime_memory_diagnostic.json")
        manifest = _read_json(z, "capture_manifest.json")
    if diag.get("schema_version") != "csmc_observer_diagnose_v1" or diag.get("diagnostic_only") is not True:
        raise CsmcObserverDiagnoseError("CSMC_DIAG_SCHEMA_REJECTED", "diagnostic schema/flag mismatch")
    if manifest.get("payload_dump_allowed") is not False or manifest.get("contains_private_runtime_payload") is not False:
        raise CsmcObserverDiagnoseError("CSMC_DIAG_PAYLOAD_POLICY_REJECTED", "diagnostic ZIP violates no-payload policy")
    staged, sha = _stage_fixed(zip_path)
    pipeline = diag.get("predicate_pipeline") if isinstance(diag.get("predicate_pipeline"), dict) else {}
    regions = diag.get("regions") if isinstance(diag.get("regions"), dict) else {}
    rf = diag.get("read_failures") if isinstance(diag.get("read_failures"), dict) else {}
    details = rf.get("details") if isinstance(rf.get("details"), list) else []
    safe_details = []
    for row in details[:64]:
        if isinstance(row, dict):
            safe_details.append({k: row.get(k) for k in ("region_base","region_size","offset","type","type_raw","protect","requested_bytes","win32_error")})
    return {
        "schema_version": "csmc_observer_diagnose_result_v1",
        "action": ACTION_NAME,
        "target": TARGET_PROCESS,
        "existing_modeler_session_used": bool(manifest.get("target_already_running")),
        "modeler_launch_performed": False,
        "model_load_performed": False,
        "focus_change_performed": False,
        "scan_reason": str(diag.get("search_reason") or "")[:120],
        "search_seconds": float(diag.get("search_seconds") or 0),
        "regions": {k: max(0, int(regions.get(k) or 0)) for k in ("scanned_committed_readable","readable_mem_private","mapped","image","other")},
        "predicate_pipeline": {k: max(0, int(pipeline.get(k) or 0)) for k in ("prefix_hits","mem_private_prefix_hits","kind_character","expected_guid","version_2","size_sanity","stored_align8_logical_eq_8","accepted")},
        "read_failures": {"count": max(0, int(rf.get("count") or 0)), "details_truncated": bool(rf.get("details_truncated")), "details": safe_details},
        "reject_reason_counts": {str(k)[:120]: max(0, int(v or 0)) for k, v in (diag.get("reject_reason_counts") or {}).items()} if isinstance(diag.get("reject_reason_counts"), dict) else {},
        "payload_dumped": False,
        "zip_name": staged.name,
        "zip_size": staged.stat().st_size,
        "zip_sha256": sha,
        "artifact_transfer": "LOCAL_FIXED_ROOT_STAGED",
    }
