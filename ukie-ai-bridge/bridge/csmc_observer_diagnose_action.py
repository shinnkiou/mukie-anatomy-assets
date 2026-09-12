"""Fixed read-only diagnose action for the isolated CSMC canary.

The observer predicates and memory-type conditions remain unchanged.  The only
post-v1 observer change is bounded temporal resampling: the same fixed P4.1
DIAG_V1 sidecar is executed three times against the already-running MODELER
session with a fixed pause between samples.  No cloud-supplied path, command,
argument, process name, timing value, or key sequence is accepted.  No runtime
payload bytes are staged or returned.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

ACTION_NAME = "csmc_observer_diagnose_v1"
TARGET_PROCESS = "CLIPStudioModeler.exe"
SIDECAR_NAME = "BP3D_ModelerObserver_P4_1_DIAG_V1.ps1"
CAPTURE_GLOB = "CAPTURE_*_P4_1_DIAG.zip"
STAGING_SUBDIR = Path("UKIE_AI_BRIDGE") / "csmc-canary" / "artifacts"
SAMPLE_COUNT = 3
SAMPLE_INTERVAL_SECONDS = 2.0


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
                st = p.stat()
                out[p.resolve()] = (st.st_mtime_ns, st.st_size)
    return out


def _new_zip(before: dict[Path, tuple[int, int]]) -> Path:
    candidates: list[Path] = []
    for root in _capture_roots():
        if not root.is_dir():
            continue
        for p in root.glob(CAPTURE_GLOB):
            if not p.is_file():
                continue
            rp = p.resolve()
            st = p.stat()
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


def _fixed_stage_root() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise CsmcObserverDiagnoseError("CSMC_LOCALAPPDATA_MISSING", "LOCALAPPDATA is unavailable")
    root = (Path(local) / STAGING_SUBDIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _run_one(sidecar: Path, powershell: Path) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    before = _snapshot()
    completed = subprocess.run(
        [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(sidecar)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=360,
        check=False,
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
    return zip_path, diag, manifest


def _safe_failure_rows(diag: dict[str, Any]) -> list[dict[str, Any]]:
    rf = diag.get("read_failures") if isinstance(diag.get("read_failures"), dict) else {}
    details = rf.get("details") if isinstance(rf.get("details"), list) else []
    rows: list[dict[str, Any]] = []
    for row in details[:64]:
        if isinstance(row, dict):
            rows.append({k: row.get(k) for k in ("region_base", "region_size", "offset", "type", "type_raw", "protect", "requested_bytes", "win32_error")})
    return rows


def run_diagnose() -> dict[str, Any]:
    sidecar = _sidecar_path()
    powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    if not powershell.is_file():
        raise CsmcObserverDiagnoseError("CSMC_POWERSHELL_MISSING", "fixed Windows PowerShell path is unavailable")

    samples: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    source_zips: list[Path] = []
    for index in range(SAMPLE_COUNT):
        zip_path, diag, manifest = _run_one(sidecar, powershell)
        source_zips.append(zip_path)
        samples.append(diag)
        manifests.append(manifest)
        if index + 1 < SAMPLE_COUNT:
            time.sleep(SAMPLE_INTERVAL_SECONDS)

    # Predicate logic is deliberately unchanged.  Aggregation records the best
    # stage reached by any temporal sample; it does not relax any predicate.
    pipeline_keys = (
        "prefix_hits", "mem_private_prefix_hits", "kind_character", "expected_guid",
        "version_2", "size_sanity", "stored_align8_logical_eq_8", "accepted",
    )
    region_keys = ("scanned_committed_readable", "readable_mem_private", "mapped", "image", "other")
    aggregate_pipeline = {k: 0 for k in pipeline_keys}
    aggregate_regions = {k: 0 for k in region_keys}
    aggregate_rejects: dict[str, int] = {}
    failure_rows: list[dict[str, Any]] = []
    failure_count = 0
    failure_truncated = False
    total_search_seconds = 0.0
    temporal_rows: list[dict[str, Any]] = []

    for index, diag in enumerate(samples):
        pipeline = diag.get("predicate_pipeline") if isinstance(diag.get("predicate_pipeline"), dict) else {}
        regions = diag.get("regions") if isinstance(diag.get("regions"), dict) else {}
        rejects = diag.get("reject_reason_counts") if isinstance(diag.get("reject_reason_counts"), dict) else {}
        rf = diag.get("read_failures") if isinstance(diag.get("read_failures"), dict) else {}
        for k in pipeline_keys:
            aggregate_pipeline[k] = max(aggregate_pipeline[k], max(0, int(pipeline.get(k) or 0)))
        for k in region_keys:
            aggregate_regions[k] = max(aggregate_regions[k], max(0, int(regions.get(k) or 0)))
        for k, v in rejects.items():
            key = str(k)[:120]
            aggregate_rejects[key] = aggregate_rejects.get(key, 0) + max(0, int(v or 0))
        failure_count += max(0, int(rf.get("count") or 0))
        failure_truncated = failure_truncated or bool(rf.get("details_truncated"))
        for row in _safe_failure_rows(diag):
            if len(failure_rows) < 64:
                failure_rows.append({"sample_index": index, **row})
            else:
                failure_truncated = True
        seconds = float(diag.get("search_seconds") or 0)
        total_search_seconds += seconds
        temporal_rows.append({
            "sample_index": index,
            "search_reason": str(diag.get("search_reason") or "")[:120],
            "search_seconds": seconds,
            "regions": {k: max(0, int(regions.get(k) or 0)) for k in region_keys},
            "predicate_pipeline": {k: max(0, int(pipeline.get(k) or 0)) for k in pipeline_keys},
            "reject_reason_counts": {str(k)[:120]: max(0, int(v or 0)) for k, v in rejects.items()},
            "read_failure_count": max(0, int(rf.get("count") or 0)),
        })

    first_manifest = manifests[0]
    if any(bool(m.get("target_already_running")) is not True for m in manifests):
        raise CsmcObserverDiagnoseError("CSMC_DIAG_MODELER_STATE_CHANGED", "all temporal samples must use an existing MODELER session")

    aggregate = {
        "schema_version": "csmc_observer_diagnose_temporal_v1",
        "diagnostic_only": True,
        "payload_dump_allowed": False,
        "contains_private_runtime_payload": False,
        "read_only": True,
        "observer_change": "bounded_temporal_resampling_same_predicates",
        "sample_count": SAMPLE_COUNT,
        "sample_interval_seconds": SAMPLE_INTERVAL_SECONDS,
        "target": TARGET_PROCESS,
        "existing_modeler_session_used": True,
        "modeler_launch_performed": False,
        "model_load_performed": False,
        "focus_change_performed": False,
        "predicate_pipeline": aggregate_pipeline,
        "regions": aggregate_regions,
        "reject_reason_counts": aggregate_rejects,
        "read_failures": {"count": failure_count, "details_truncated": failure_truncated, "details": failure_rows},
        "temporal_samples": temporal_rows,
        "source_zip_names": [p.name for p in source_zips],
    }

    stage_root = _fixed_stage_root()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    staged = (stage_root / f"CAPTURE_{stamp}_P4_1_DIAG.zip").resolve()
    if staged.parent != stage_root:
        raise CsmcObserverDiagnoseError("CSMC_STAGE_PATH_REJECTED", "staging path escaped fixed root")
    if staged.exists():
        raise CsmcObserverDiagnoseError("CSMC_STAGE_COLLISION", "temporal diagnostic artifact already exists")
    partial = staged.with_name(staged.name + ".partial")
    partial.unlink(missing_ok=True)
    with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("temporal_diagnostic.json", json.dumps(aggregate, ensure_ascii=False, indent=2))
        z.writestr("capture_manifest.json", json.dumps({
            "schema_version": "csmc_observer_diagnose_temporal_manifest_v1",
            "target_already_running": bool(first_manifest.get("target_already_running")),
            "payload_dump_allowed": False,
            "contains_private_runtime_payload": False,
            "sample_count": SAMPLE_COUNT,
            "sample_interval_seconds": SAMPLE_INTERVAL_SECONDS,
            "observer_change": "bounded_temporal_resampling_same_predicates",
        }, ensure_ascii=False, indent=2))
    os.replace(partial, staged)
    sha = _sha256(staged)

    return {
        "schema_version": "csmc_observer_diagnose_result_temporal_v1",
        "action": ACTION_NAME,
        "target": TARGET_PROCESS,
        "existing_modeler_session_used": True,
        "modeler_launch_performed": False,
        "model_load_performed": False,
        "focus_change_performed": False,
        "scan_reason": "temporal_complete",
        "search_seconds": total_search_seconds,
        "regions": aggregate_regions,
        "predicate_pipeline": aggregate_pipeline,
        "read_failures": {"count": failure_count, "details_truncated": failure_truncated, "details": failure_rows},
        "reject_reason_counts": aggregate_rejects,
        "payload_dumped": False,
        "zip_name": staged.name,
        "zip_size": staged.stat().st_size,
        "zip_sha256": sha,
        "artifact_transfer": "LOCAL_FIXED_ROOT_STAGED",
    }
