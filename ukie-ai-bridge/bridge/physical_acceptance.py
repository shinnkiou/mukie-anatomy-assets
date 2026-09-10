"""One-command physical acceptance orchestrator for UKIE AI BRIDGE.

The acceptance run is deliberately local-only. It collects device status, executes
the disposable Blender canary, then attempts the independently scoped GPU route
probe. A GPU failure does not erase a successful core canary. Nothing here uploads
files, mutates Base44, promotes a release, saves user .blend files, or enables AI.
The generated bundle is evidence that still requires Drive upload/readback and the
control-plane release gate.
"""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import main as bridge_main
    from .blender_canary import run_blender_canary
    from .gpu_probe import GPUProbeError, run_gpu_probe
    from .validator import sha256_file
except ImportError:
    import main as bridge_main
    from blender_canary import run_blender_canary
    from gpu_probe import GPUProbeError, run_gpu_probe
    from validator import sha256_file


ACCEPTANCE_SCHEMA = "ukie_physical_acceptance_v1"
RELEASE_INFO_SCHEMA = "ukie_bridge_release_info_v1"
HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _json_write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_zip_tree(root: Path, output: Path) -> None:
    root = root.resolve()
    output = output.resolve()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.resolve() == output:
                continue
            resolved = path.resolve()
            if root != resolved and root not in resolved.parents:
                raise RuntimeError(f"acceptance artifact escaped workspace: {path}")
            zf.write(path, path.relative_to(root.parent))


def _copy_if_file(source: str | Path | None, destination: Path) -> dict[str, Any] | None:
    if not source:
        return None
    src = Path(source)
    if not src.is_file():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, destination)
    return {
        "name": destination.name,
        "byte_size": destination.stat().st_size,
        "sha256": sha256_file(destination),
    }


def _normalize_release_info(value: dict[str, Any] | None) -> tuple[dict[str, Any], str]:
    if value is None:
        return ({
            "schema_version": RELEASE_INFO_SCHEMA,
            "release_key": "UNBOUND_LOCAL_DEVELOPMENT",
            "bridge_version": None,
            "commit_sha": None,
            "workflow_run_id": None,
            "bp3d_blender_pin": bridge_main.BP3D_BLENDER_PIN,
        }, "UNBOUND")

    if not isinstance(value, dict):
        raise RuntimeError("release info must be a JSON object")
    if value.get("schema_version") != RELEASE_INFO_SCHEMA:
        raise RuntimeError("unsupported release info schema")
    release_key = value.get("release_key")
    bridge_version = value.get("bridge_version")
    commit_sha = value.get("commit_sha")
    workflow_run_id = value.get("workflow_run_id")
    if not isinstance(release_key, str) or not release_key.startswith("BRIDGE_P"):
        raise RuntimeError("release info contains an invalid release_key")
    if not isinstance(bridge_version, str) or not bridge_version.strip():
        raise RuntimeError("release info is missing bridge_version")
    if not isinstance(commit_sha, str) or not HEX40.fullmatch(commit_sha):
        raise RuntimeError("release info contains an invalid commit_sha")
    if not isinstance(workflow_run_id, int) or isinstance(workflow_run_id, bool) or workflow_run_id <= 0:
        raise RuntimeError("release info contains an invalid workflow_run_id")
    if str(value.get("bp3d_blender_pin") or "") != bridge_main.BP3D_BLENDER_PIN:
        raise RuntimeError("release info Blender pin does not match Bridge production pin")
    return (dict(value), "BOUND")


def run_physical_acceptance(
    workspace: Path,
    state_root: Path | None = None,
    release_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    release, release_binding_status = _normalize_release_info(release_info)
    stamp = _stamp()
    acceptance_id = f"PHYSICAL_ACCEPTANCE_{stamp}"
    run_root = workspace / acceptance_id
    run_root.mkdir(parents=True, exist_ok=False)

    device = bridge_main.device_status()
    _json_write(run_root / "device_status.json", device)

    result: dict[str, Any] = {
        "schema_version": ACCEPTANCE_SCHEMA,
        "acceptance_id": acceptance_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "RUNNING",
        "release": release,
        "release_binding_status": release_binding_status,
        "device": {
            "platform": device.get("platform"),
            "memory": device.get("memory"),
            "blender": device.get("blender"),
        },
        "core": {"status": "PENDING", "canary": None},
        "gpu": {"status": "PENDING", "result": None},
        "artifacts": {},
        "ready_for_ai": False,
        "promotion_performed": False,
        "upload_performed": False,
        "metadata": {"synthetic_ci_only": False},
    }

    # Core is the hard local prerequisite. The canary uses only generated data.
    canary_workspace = run_root / "canary"
    try:
        canary = run_blender_canary(canary_workspace, state_root)
        result["core"]["canary"] = canary
        core_pass = canary.get("status") == "CANARY_LOCAL_PASS"
    except Exception as exc:
        result["core"]["canary"] = {
            "status": "CANARY_FAILED",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        core_pass = False

    result["core"]["status"] = "CORE_LOCAL_PASS" if core_pass else "CORE_LOCAL_FAILED"

    canary_payload = result["core"].get("canary") or {}
    bundle_info = canary_payload.get("bundle") if isinstance(canary_payload, dict) else None
    if isinstance(bundle_info, dict):
        candidate = bundle_info.get("path")
        if candidate and Path(candidate).is_file():
            copied = _copy_if_file(Path(candidate), run_root / "evidence" / Path(candidate).name)
            if copied:
                result["artifacts"]["canary_bundle"] = copied

    # If core fails, skip GPU rather than creating misleading secondary noise.
    if not core_pass:
        result["gpu"] = {"status": "SKIPPED_CORE_FAILED", "result": None}
        result["status"] = "CORE_FAILED"
    else:
        gpu_workspace = run_root / "gpu"
        try:
            gpu = run_gpu_probe(gpu_workspace)
            gpu_pass = gpu.get("ready_for_gpu_render") is True
            result["gpu"] = {"status": "GPU_ROUTE_PASS" if gpu_pass else "GPU_ROUTE_BLOCKED", "result": gpu}
        except GPUProbeError as exc:
            gpu_pass = False
            result["gpu"] = {
                "status": "GPU_ROUTE_BLOCKED",
                "result": {"error_type": type(exc).__name__, "error": str(exc)},
            }
        except Exception as exc:
            gpu_pass = False
            result["gpu"] = {
                "status": "GPU_ROUTE_FAILED",
                "result": {"error_type": type(exc).__name__, "error": str(exc)},
            }

        result["status"] = "CORE_PASS_GPU_PASS" if gpu_pass else "CORE_PASS_GPU_BLOCKED"
        for name in ("gpu_probe.json", "gpu_probe.png", "gpu_probe_stdout.log", "gpu_probe_stderr.log"):
            copied = _copy_if_file(gpu_workspace / name, run_root / "evidence" / name)
            if copied:
                result["artifacts"][name] = copied

    result["completed_at"] = datetime.now(timezone.utc).isoformat()
    result["local_core_ready"] = core_pass
    result["local_gpu_render_ready"] = result["gpu"]["status"] == "GPU_ROUTE_PASS"
    if not core_pass:
        result["next_gate"] = "INSPECT_LOCAL_ACCEPTANCE_EVIDENCE"
    elif release_binding_status != "BOUND":
        result["next_gate"] = "BIND_RELEASE_AND_RERUN"
    else:
        result["next_gate"] = "DRIVE_UPLOAD_READBACK_THEN_ACCEPTANCE_VERIFICATION_AND_RELEASE_GATE"
    result["notes"] = (
        "Local acceptance never sets READY_FOR_AI. Physical evidence must be bound to a release, read back from Drive, "
        "verified offline, and then evaluated by the release gate. GPU route is capability-scoped and external "
        "utilization telemetry remains separate."
    )

    manifest = run_root / "physical_acceptance_manifest.json"
    _json_write(manifest, result)

    bundle = workspace / f"{acceptance_id}.zip"
    _safe_zip_tree(run_root, bundle)
    result["acceptance_bundle"] = {
        "path": str(bundle),
        "byte_size": bundle.stat().st_size,
        "sha256": sha256_file(bundle),
    }
    # Update the standalone manifest after the bundle hash exists. The ZIP contains
    # the pre-bundle manifest by design to avoid self-referential archive hashing.
    _json_write(manifest, result)
    return result
