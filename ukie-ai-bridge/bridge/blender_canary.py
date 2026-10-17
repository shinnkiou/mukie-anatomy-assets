"""One-command physical Blender canary for UKIE AI BRIDGE.

The canary creates its own disposable cube fixture with the pinned local Blender,
then routes that generated file through the same exact-once ANALYZE_ONLY runner
used for real jobs. A local PASS is still not READY_FOR_AI: Drive upload/readback
and later GPU checks remain separate hard gates.
"""

from __future__ import annotations

import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from . import main as bridge_main
    from .analyze_runner import run_local_analyze
    from .job_controller import execute_once
    from .state_store import BridgeStateStore
    from .validator import load_and_validate, sha256_file
except ImportError:
    import main as bridge_main
    from analyze_runner import run_local_analyze
    from job_controller import execute_once
    from state_store import BridgeStateStore
    from validator import load_and_validate, sha256_file


CANARY_SCHEMA = "ukie_blender_canary_v1"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _verify_scene_report(path: Path) -> dict:
    if not path.is_file():
        return {"status": "FAIL", "reason": "scene_before.json missing"}
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "reason": f"scene report unreadable: {exc}"}

    cube = None
    for obj in report.get("objects", []):
        if isinstance(obj, dict) and obj.get("name") == "UKIE_CANARY_CUBE":
            cube = obj
            break
    if cube is None:
        return {"status": "FAIL", "reason": "UKIE_CANARY_CUBE missing"}
    mesh = cube.get("mesh") if isinstance(cube.get("mesh"), dict) else {}
    if mesh.get("vertices") != 8 or mesh.get("polygons") != 6:
        return {
            "status": "FAIL",
            "reason": "canary topology mismatch",
            "observed": {"vertices": mesh.get("vertices"), "polygons": mesh.get("polygons")},
        }
    return {
        "status": "PASS",
        "object": "UKIE_CANARY_CUBE",
        "vertices": 8,
        "polygons": 6,
        "blender_version": report.get("blender_version"),
        "python_version": report.get("python_version"),
    }


def _zip_tree(source_dir: Path, output: Path, extras: list[Path]) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file() and path.resolve() != output.resolve():
                zf.write(path, path.relative_to(source_dir.parent))
        for path in extras:
            if path.is_file() and source_dir not in path.parents:
                zf.write(path, Path("CANARY_ROOT") / path.name)


def run_blender_canary(workspace: Path, state_root: Path | None = None) -> dict:
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    blender = bridge_main.detect_blender()
    if not blender.get("found"):
        raise RuntimeError(blender.get("error") or "Blender not found")
    version_line = str(blender.get("version_line") or "")
    if bridge_main.BP3D_BLENDER_PIN not in version_line:
        raise RuntimeError(
            f"canary requires Blender {bridge_main.BP3D_BLENDER_PIN}; detected {version_line or 'unknown'}"
        )

    stamp = _stamp()
    canary_id = f"BLENDER_CANARY_{stamp}"
    canary_root = (workspace / canary_id).resolve()
    canary_root.mkdir(parents=True, exist_ok=False)

    generator = bridge_main.bundle_root() / "blender" / "create_canary.py"
    if not generator.is_file():
        raise RuntimeError(f"bundled canary generator missing: {generator}")

    source = canary_root / "canary_source.blend"
    create_stdout = canary_root / "canary_create_stdout.log"
    create_stderr = canary_root / "canary_create_stderr.log"
    create_proc = subprocess.run(
        [
            blender["path"],
            "-b",
            "--factory-startup",
            "--python",
            str(generator),
            "--",
            "--output",
            str(source),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    create_stdout.write_text(create_proc.stdout or "", encoding="utf-8", newline="\n")
    create_stderr.write_text(create_proc.stderr or "", encoding="utf-8", newline="\n")
    if create_proc.returncode != 0 or not source.is_file():
        raise RuntimeError(f"canary fixture generation failed with exit={create_proc.returncode}")

    source_sha = sha256_file(source)
    job_id = f"CANARY_JOB_{stamp}"
    job_json = canary_root / "request.json"
    job_payload = {
        "schema_version": "ukie_job_v1",
        "job_id": job_id,
        "action": "analyze_blend",
        "project": "BRIDGE_TEST",
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "timeout_seconds": 300,
        "input": {
            "drive_file_id": "LOCAL_CANARY_GENERATED",
            "sha256": source_sha,
            "original_filename": "UKIE_CANARY_GENERATED.blend",
            "byte_size": source.stat().st_size,
        },
        "blender": {"required_version": bridge_main.BP3D_BLENDER_PIN, "background": True},
    }
    job_json.write_text(json.dumps(job_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    job = load_and_validate(job_json)

    store_root = state_root if state_root is not None else (workspace / "bridge_state")
    store = BridgeStateStore(store_root)
    job_workspace = canary_root / "jobs"
    outcome = execute_once(
        job,
        store,
        lambda: run_local_analyze(job_json, source, job_workspace),
    )

    job_dir = job_workspace / job_id
    semantic = _verify_scene_report(job_dir / "scene_before.json")
    previews = {
        "front": (job_dir / "preview_front.png").is_file() and (job_dir / "preview_front.png").stat().st_size >= 1024,
        "side": (job_dir / "preview_side.png").is_file() and (job_dir / "preview_side.png").stat().st_size >= 1024,
    }
    source_unchanged = sha256_file(source) == source_sha

    local_pass = bool(
        outcome.get("decision") == "LOCAL_SAVED"
        and semantic.get("status") == "PASS"
        and all(previews.values())
        and source_unchanged
    )
    canary_manifest = {
        "schema_version": CANARY_SCHEMA,
        "canary_id": canary_id,
        "job_id": job_id,
        "status": "CANARY_LOCAL_PASS" if local_pass else "CANARY_FAILED",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "blender": blender,
        "source": {
            "name": source.name,
            "byte_size": source.stat().st_size,
            "sha256": source_sha,
            "unchanged_after_analysis": source_unchanged,
        },
        "exact_once": {
            "decision": outcome.get("decision"),
            "executed": outcome.get("executed"),
        },
        "semantic_verification": semantic,
        "previews": previews,
        "next_gate": "DRIVE_UPLOAD_READBACK" if local_pass else "INSPECT_LOCAL_LOGS",
        "ready_for_ai": False,
        "notes": "Local canary PASS does not prove Google Drive durability or dedicated GPU use.",
    }
    manifest_path = canary_root / "canary_manifest.json"
    manifest_path.write_text(json.dumps(canary_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    bundle = workspace / f"{canary_id}.zip"
    _zip_tree(canary_root, bundle, [])
    canary_manifest["bundle"] = {
        "path": str(bundle),
        "byte_size": bundle.stat().st_size,
        "sha256": sha256_file(bundle),
    }
    manifest_path.write_text(json.dumps(canary_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return canary_manifest
