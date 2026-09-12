"""P0.4 local Blender ANALYZE_ONLY runner.

The runner operates only on an explicit local input, copies it into an ASCII job
workspace, never saves the source or working .blend, and requires structured scene
data plus front/side PNG previews before returning LOCAL_SAVED.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

try:
    from .artifact_validation import validate_artifact_contract
    from .preflight import run_foundation_preflight, write_preflight_report
    from .validator import JobValidationError, load_and_validate, sha256_file
    from . import main as bridge_main
except ImportError:
    from artifact_validation import validate_artifact_contract
    from preflight import run_foundation_preflight, write_preflight_report
    from validator import JobValidationError, load_and_validate, sha256_file
    import main as bridge_main


RUNNER_VERSION = "ukie_analyze_runner_v2"


def preview_analyze_contract() -> dict:
    return {
        "files": [
            {
                "name": "scene_before.json",
                "min_bytes": 32,
                "json": True,
                "required_json_paths": [
                    "schema_version",
                    "mode",
                    "blender_version",
                    "python_version",
                    "objects",
                ],
            },
            {"name": "preview_front.png", "min_bytes": 1024},
            {"name": "preview_side.png", "min_bytes": 1024},
            {"name": "stdout.log", "min_bytes": 1},
            {"name": "working.blend", "min_bytes": 64},
            {"name": "input.blend", "min_bytes": 64},
        ]
    }


def _version_is_bp3d_pin(blender: dict) -> bool:
    line = str(blender.get("version_line") or "")
    return bridge_main.BP3D_BLENDER_PIN in line


def run_local_analyze(job_json: Path, local_input: Path, workspace: Path) -> dict:
    job = load_and_validate(job_json)
    if job.action != "analyze_blend":
        raise JobValidationError("local-analyze requires action=analyze_blend")
    if local_input.suffix.lower() != ".blend":
        raise JobValidationError("local-analyze accepts only .blend input")
    if not local_input.is_file():
        raise FileNotFoundError(local_input)

    analyzer = bridge_main.bundle_root() / "blender" / "analyze_scene.py"
    if not analyzer.is_file():
        raise RuntimeError(f"bundled analyzer missing: {analyzer}")

    required_free = max(local_input.stat().st_size * 3 + (256 * 1024 * 1024), 384 * 1024 * 1024)
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
    blender = bridge_main.detect_blender()
    if not blender.get("found"):
        raise RuntimeError(blender.get("error") or "Blender not found")
    if job.project == "BP3D" and not _version_is_bp3d_pin(blender):
        raise RuntimeError(
            f"BP3D requires Blender {bridge_main.BP3D_BLENDER_PIN}; detected {blender.get('version_line')}"
        )

    job_dir = bridge_main.safe_job_dir(workspace, job.job_id)
    preflight_path = job_dir / "preflight.json"
    write_preflight_report(preflight, preflight_path)
    input_copy = job_dir / "input.blend"
    working_copy = job_dir / "working.blend"
    scene_json = job_dir / "scene_before.json"
    preview_front = job_dir / "preview_front.png"
    preview_side = job_dir / "preview_side.png"
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
        "--preview-front",
        str(preview_front),
        "--preview-side",
        str(preview_side),
    ]

    started = bridge_main.utc_now()
    proc = None
    timed_out = False
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
    except subprocess.TimeoutExpired as exc:
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
        artifact_validation = validate_artifact_contract(job_dir, preview_analyze_contract())

    success = bool(
        proc is not None
        and proc.returncode == 0
        and artifact_validation is not None
        and artifact_validation.get("status") == "PASS"
        and source_unchanged
    )

    manifest = {
        "schema_version": "ukie_job_manifest_v2",
        "runner_version": RUNNER_VERSION,
        "job_id": job.job_id,
        "action": job.action,
        "project": job.project,
        "mode": "ANALYZE_ONLY",
        "started_at": started,
        "finished_at": bridge_main.utc_now(),
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
        "bridge_core_version": bridge_main.BRIDGE_VERSION,
        "protocol_version": bridge_main.PROTOCOL_VERSION,
        "process": {
            "timed_out": timed_out,
            "return_code": proc.returncode if proc is not None else None,
        },
        "artifacts": {
            "preflight": preflight_path.name,
            "scene_before": scene_json.name if scene_json.is_file() else None,
            "preview_front": preview_front.name if preview_front.is_file() else None,
            "preview_side": preview_side.name if preview_side.is_file() else None,
            "stdout": stdout_log.name,
            "stderr": stderr_log.name,
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
