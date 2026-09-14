# SPDX-License-Identifier: MIT
"""NEVER TEAR AI3D-013 Structure CANARY v0.2.1 diagnostic companion.

Changes from v0.2.0:
- uses a new bounded CANARY-002 job identity; CANARY-001 remains diagnostic history
- includes exact worker identity on PASS and FAIL completion requests
- reports plan-validation failures while the lease is still owned
- keeps the same fail-closed single capability and six-command Structure contract
"""
from __future__ import annotations

import json
from typing import Any

import ai3d_worker as core
import ai3d_structure_worker as structure

WORKER_VERSION = "0.2.1-ai3d-structure-diagnostic"
PROTOCOL = "never-tear-ai3d-worker-v1"
ACTION = "ai3d_structure_module_v1"
JOB_KEY = "AI3D-013-PHYSICAL-STRUCTURE-CANARY-002"
COMMAND_ID = "AI3D-013-STRUCTURE-CANARY-002-NEVER-TEAR"
RUN_ID = JOB_KEY
EDGE_URL = "https://vbuokbwglauibabinaqs.supabase.co/functions/v1/ai3d-worker-transport-structure-canary"
ALLOWED_ACTIONS = frozenset({ACTION})

# Reuse the reviewed v0.2.0 validators/executor, but bind them to the new
# diagnostic identity before core.main starts.
structure.WORKER_VERSION = WORKER_VERSION
structure.RUN_ID = RUN_ID
structure.EDGE_URL = EDGE_URL
structure.ALLOWED_ACTIONS = ALLOWED_ACTIONS

_original_bundled_file = core.bundled_file

def _diagnostic_bundled_file(name: str):
    if name == "blender_structure_module_canary.py":
        return _original_bundled_file("blender_structure_module_canary_v021.py")
    return _original_bundled_file(name)


def complete_fail(credential: dict[str, str], job: dict[str, Any], error_code: str, message: str) -> None:
    try:
        core.request_json(credential, {
            "action": "complete",
            "ai3d_worker_version": WORKER_VERSION,
            "capabilities": sorted(ALLOWED_ACTIONS),
            "job_id": job["id"],
            "lease_owner": job["lease_owner"],
            "outcome": "FAIL",
            "error_code": error_code[:120],
            "error_message": message[:1000],
        })
    except Exception as report_exc:
        print(f"AI3D_FAILURE_REPORT_ERROR: {report_exc}", flush=True)


def complete_pass(credential: dict[str, str], job: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return core.request_json(credential, {
        "action": "complete",
        "ai3d_worker_version": WORKER_VERSION,
        "capabilities": sorted(ALLOWED_ACTIONS),
        "job_id": job["id"],
        "lease_owner": job["lease_owner"],
        "outcome": "PASS",
        "result": {
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
            "automated_qa": "PASS",
            "visual_qa": "PENDING",
        },
    })


def claim(credential: dict[str, str]) -> dict[str, Any] | None:
    response = core.request_json(credential, {
        "action": "claim",
        "ai3d_worker_version": WORKER_VERSION,
        "capabilities": sorted(ALLOWED_ACTIONS),
    })
    if response.get("status") == "NO_JOB":
        return None
    if response.get("status") != "CLAIMED" or not isinstance(response.get("job"), dict):
        raise core.WorkerError(f"unexpected claim response: {response.get('status')}")
    job = response["job"]
    if job.get("action") not in ALLOWED_ACTIONS:
        complete_fail(credential, job, "AI3D_ACTION_VALIDATION_FAILED", "server returned non-allowlisted action")
        raise core.WorkerError("server returned non-allowlisted action")
    try:
        job["plan"] = structure.sanitize_plan(job.get("plan"))
    except Exception as exc:
        complete_fail(credential, job, "AI3D_PLAN_VALIDATION_FAILED", str(exc))
        raise
    return job


def process_job(credential: dict[str, str], job: dict[str, Any]) -> None:
    command_id = str(job.get("command_id") or "")
    if (
        job.get("action") != ACTION
        or job.get("task_id") != structure.TASK_ID
        or job.get("job_key") != JOB_KEY
        or command_id != COMMAND_ID
    ):
        raise core.WorkerError("Structure CANARY-002 job identity rejected")
    job_dir = core.command_dir(command_id)
    result, png_path = structure.run_blender_job(credential, job, job_dir)
    upload = core.upload_png(credential, job, png_path, result["png_sha256"])
    response = complete_pass(credential, job, result)
    if response.get("status") != "STRUCTURE_CANARY_AUTOMATED_PASS_VISUAL_PENDING":
        raise core.WorkerError(f"unexpected completion status: {response.get('status')}")
    receipt = {
        "schema_version": "never-tear-ai3d-structure-worker-receipt-v2",
        "worker_version": WORKER_VERSION,
        "command_id": command_id,
        "job_key": job.get("job_key"),
        "status": response.get("status"),
        "artifact_id": upload.get("artifact_id"),
        "png_sha256": result["png_sha256"],
        "checkpoint_id": result["checkpoint_id"],
        "local_job_dir": str(job_dir),
    }
    core.receipt_path(command_id).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


def self_test() -> int:
    failures: list[str] = []
    if WORKER_VERSION != "0.2.1-ai3d-structure-diagnostic":
        failures.append("worker version mismatch")
    if JOB_KEY.endswith("001") or COMMAND_ID.endswith("001-NEVER-TEAR"):
        failures.append("old canary identity reused")
    if ALLOWED_ACTIONS != frozenset({"ai3d_structure_module_v1"}):
        failures.append("allowlist widened")
    try:
        structure.sanitize_plan(structure._valid_plan())
    except Exception as exc:
        failures.append(f"valid plan rejected: {exc}")
    result = {
        "schema_version": "never-tear-ai3d-structure-worker-selftest-v2",
        "worker_version": WORKER_VERSION,
        "job_key": JOB_KEY,
        "protocol": PROTOCOL,
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "completion_identity_attached": True,
        "failure_reporting_attached": True,
        "arbitrary_shell": False,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0 if not failures else 23


# Patch only the extension points used by core.main / core.run_cycle.
core.WORKER_VERSION = WORKER_VERSION
core.PROTOCOL = PROTOCOL
core.EDGE_URL = EDGE_URL
core.ALLOWED_ACTIONS = ALLOWED_ACTIONS
core.bundled_file = _diagnostic_bundled_file
core.sanitize_plan = structure.sanitize_plan
core.validate_result = structure.validate_result
core.run_blender_job = structure.run_blender_job
core.claim = claim
core.complete_pass = complete_pass
core.complete_fail = complete_fail
core.process_job = process_job
core.self_test = self_test

if __name__ == "__main__":
    raise SystemExit(core.main())
