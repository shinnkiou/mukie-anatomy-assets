# SPDX-License-Identifier: MIT
"""AI3D-013 Structure CANARY v0.2.4 geometry-level Boolean QA repair.

CANARY-004 proved the Stable Launcher -> verified worker -> isolated transport ->
real Blender -> durable artifact path, but visual QA found no central opening.
The old automated check only counted a BOOLEAN command. v0.2.4 keeps the same
bounded six-command capability and moves to a new CANARY-005 identity whose
Blender wrapper verifies the resulting mesh with an opening void ray plus a
known-solid control ray.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import ai3d_worker as core
import ai3d_structure_worker as structure
import ai3d_structure_worker_v021 as prev

WORKER_VERSION = "0.2.4-ai3d-structure-visualfix"
PROTOCOL = "never-tear-ai3d-worker-v1"
ACTION = "ai3d_structure_module_v1"
JOB_KEY = "AI3D-013-PHYSICAL-STRUCTURE-CANARY-005"
COMMAND_ID = "AI3D-013-STRUCTURE-CANARY-005-NEVER-TEAR"
RUN_ID = JOB_KEY
EDGE_URL = "https://vbuokbwglauibabinaqs.supabase.co/functions/v1/ai3d-worker-transport-structure-canary-v5"
EVIDENCE_CLASS = "PHYSICAL_WINDOWS_BLENDER_STRUCTURE_CAPABILITY_CANARY_V5"
GEOMETRY_PROBE_VERSION = "CANARY005_OPENING_RAY_V1"
ALLOWED_ACTIONS = frozenset({ACTION})

# Rebind the reviewed v0.2.1 transport/validators to the new bounded identity.
prev.WORKER_VERSION = WORKER_VERSION
prev.JOB_KEY = JOB_KEY
prev.COMMAND_ID = COMMAND_ID
prev.RUN_ID = RUN_ID
prev.EDGE_URL = EDGE_URL
prev.ALLOWED_ACTIONS = ALLOWED_ACTIONS

structure.WORKER_VERSION = WORKER_VERSION
structure.RUN_ID = RUN_ID
structure.EDGE_URL = EDGE_URL
structure.ALLOWED_ACTIONS = ALLOWED_ACTIONS

core.WORKER_VERSION = WORKER_VERSION
core.PROTOCOL = PROTOCOL
core.EDGE_URL = EDGE_URL
core.ALLOWED_ACTIONS = ALLOWED_ACTIONS


def _v024_bundled_file(name: str):
    if name == "blender_structure_module_canary.py":
        return prev._original_bundled_file("blender_structure_module_canary_v024.py")
    return prev._original_bundled_file(name)


def _tail(path: Path, limit: int = 900) -> str:
    try:
        raw = path.read_bytes()
    except Exception:
        return ""
    text = raw[-limit:].decode("utf-8", "replace")
    return " | ".join(part.strip() for part in text.replace("\r", "\n").split("\n") if part.strip())


_original_validate_result = structure.validate_result
_original_run_blender_job = structure.run_blender_job


def validate_result(job_dir: Path):
    result, png_path = _original_validate_result(job_dir)
    if result.get("evidence_class") != EVIDENCE_CLASS:
        raise core.WorkerError("Structure CANARY-005 evidence class rejected")
    if result.get("geometry_probe_version") != GEOMETRY_PROBE_VERSION:
        raise core.WorkerError("Structure CANARY-005 geometry probe version rejected")
    checks = result.get("checks")
    if not isinstance(checks, dict):
        raise core.WorkerError("Structure CANARY-005 checks missing")
    required_true = (
        "wall_count_exact",
        "opening_boolean_command_count_exact",
        "opening_void_probe",
        "solid_control_probe",
        "opening_boolean_exact",
        "cutter_removed",
        "mesh_nonempty",
        "floor_contact",
        "render_evidence",
        "background_mode",
        "production_plan_not_executed",
    )
    for key in required_true:
        if checks.get(key) is not True:
            raise core.WorkerError(f"Structure CANARY-005 geometry check failed: {key}")
    if checks.get("canary_promoted") is not False:
        raise core.WorkerError("Structure CANARY-005 promotion invariant rejected")
    return result, png_path


def run_blender_job(credential: dict[str, str], job: dict[str, Any], job_dir: Path):
    # The reviewed base runner calls structure.validate_result after Blender.
    # Rebinding it here makes the geometry probes mandatory before upload.
    structure.validate_result = validate_result
    try:
        return _original_run_blender_job(credential, job, job_dir)
    except Exception as exc:
        stderr_tail = _tail(job_dir / "blender.stderr.log")
        stdout_tail = _tail(job_dir / "blender.stdout.log", 650)
        result_summary = ""
        try:
            result = json.loads((job_dir / "result.json").read_text(encoding="utf-8"))
            result_summary = " result_status=%s checks=%s" % (result.get("status"), result.get("checks"))
        except Exception:
            pass
        detail = "%s; stderr_tail=%s; stdout_tail=%s;%s" % (exc, stderr_tail, stdout_tail, result_summary)
        raise core.WorkerError(detail[:1000]) from exc


def complete_pass(credential: dict[str, str], job: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    # Send the actual geometry predicates to v5. The server independently
    # requires them; old count-only PASS payloads cannot pass this boundary.
    return core.request_json(credential, {
        "action": "complete",
        "ai3d_worker_version": WORKER_VERSION,
        "capabilities": sorted(ALLOWED_ACTIONS),
        "job_id": job["id"],
        "lease_owner": job["lease_owner"],
        "outcome": "PASS",
        "result": {
            "run_id": result["run_id"],
            "evidence_class": result["evidence_class"],
            "status": result["status"],
            "raw_pixel_sha256": result["raw_pixel_sha256"],
            "png_sha256": result["png_sha256"],
            "checkpoint_id": result["checkpoint_id"],
            "checkpoint_sha256": result["checkpoint_sha256"],
            "renderer": result["renderer"],
            "blender_version": result["blender_version"],
            "render_engine": result["render_engine"],
            "boolean_solver": result["boolean_solver"],
            "width": result["width"],
            "height": result["height"],
            "wall_count": result["wall_count"],
            "opening_boolean_count": result["opening_boolean_count"],
            "command_count": result["command_count"],
            "automated_qa": result["automated_qa"],
            "visual_qa": result["visual_qa"],
            "canary_promoted": result["canary_promoted"],
            "promotion_allowed": result["promotion_allowed"],
            "geometry_probe_version": result["geometry_probe_version"],
            "checks": result["checks"],
        },
    })


def self_test() -> int:
    failures: list[str] = []
    if WORKER_VERSION != "0.2.4-ai3d-structure-visualfix":
        failures.append("worker version mismatch")
    if not JOB_KEY.endswith("005") or not COMMAND_ID.endswith("005-NEVER-TEAR"):
        failures.append("CANARY-005 identity mismatch")
    if ALLOWED_ACTIONS != frozenset({"ai3d_structure_module_v1"}):
        failures.append("allowlist widened")
    if not EDGE_URL.endswith("/ai3d-worker-transport-structure-canary-v5"):
        failures.append("v5 transport not isolated")
    try:
        plan = structure._valid_plan()
        plan["run_id"] = RUN_ID
        structure.sanitize_plan(plan)
    except Exception as exc:
        failures.append("valid plan rejected: %s" % exc)
    try:
        source = prev._original_bundled_file("blender_structure_module_canary_v024.py").read_text(encoding="utf-8")
        required = [
            "spec_from_file_location",
            "base.RUN_ID = RUN_ID",
            "BOOLEAN_OVERLAP_EPSILON_M",
            'checks["opening_void_probe"]',
            'checks["solid_control_probe"]',
            'checks["opening_boolean_exact"] = geometry_boolean_exact',
            "canary_promoted",
        ]
        for marker in required:
            if marker not in source:
                failures.append("geometry-QA marker missing: %s" % marker)
        if "import blender_structure_module_canary as base" in source:
            failures.append("unsafe normal sibling import retained")
    except Exception as exc:
        failures.append("v0.2.4 wrapper source unreadable: %s" % exc)
    result = {
        "schema_version": "never-tear-ai3d-structure-worker-selftest-v5",
        "worker_version": WORKER_VERSION,
        "job_key": JOB_KEY,
        "protocol": PROTOCOL,
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "explicit_bundled_loader": True,
        "geometry_level_boolean_qa": True,
        "opening_void_probe_required": True,
        "solid_control_probe_required": True,
        "server_geometry_checks_forwarded": True,
        "execution_overlap_epsilon_bounded": True,
        "failure_log_tail_reporting": True,
        "arbitrary_shell": False,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0 if not failures else 23


# Patch the same reviewed extension points as v0.2.1, but require the new
# geometry predicates on both the local and server completion boundaries.
core.bundled_file = _v024_bundled_file
structure.validate_result = validate_result
structure.run_blender_job = run_blender_job
prev.complete_pass = complete_pass
core.run_blender_job = run_blender_job
core.claim = prev.claim
core.complete_pass = complete_pass
core.complete_fail = prev.complete_fail
core.process_job = prev.process_job
core.sanitize_plan = structure.sanitize_plan
core.validate_result = validate_result
core.self_test = self_test

if __name__ == "__main__":
    raise SystemExit(core.main())
