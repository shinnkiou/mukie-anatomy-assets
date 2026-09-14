# SPDX-License-Identifier: MIT
"""AI3D-013 Structure CANARY v0.2.2 gate-fix companion.

Uses new CANARY-003 identity, corrects the canary QA gate via the bundled v022
Blender wrapper, and appends bounded Blender log tails to server-side failure
reports. Production Structure remains blocked until visual QA passes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import ai3d_worker as core
import ai3d_structure_worker as structure
import ai3d_structure_worker_v021 as prev

WORKER_VERSION = "0.2.2-ai3d-structure-gatefix"
PROTOCOL = "never-tear-ai3d-worker-v1"
ACTION = "ai3d_structure_module_v1"
JOB_KEY = "AI3D-013-PHYSICAL-STRUCTURE-CANARY-003"
COMMAND_ID = "AI3D-013-STRUCTURE-CANARY-003-NEVER-TEAR"
RUN_ID = JOB_KEY
EDGE_URL = "https://vbuokbwglauibabinaqs.supabase.co/functions/v1/ai3d-worker-transport-structure-canary-v3"
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


def _v022_bundled_file(name: str):
    if name == "blender_structure_module_canary.py":
        return prev._original_bundled_file("blender_structure_module_canary_v022.py")
    return prev._original_bundled_file(name)


def _tail(path: Path, limit: int = 700) -> str:
    try:
        raw = path.read_bytes()
    except Exception:
        return ""
    text = raw[-limit:].decode("utf-8", "replace")
    return " | ".join(part.strip() for part in text.replace("\r", "\n").split("\n") if part.strip())


_original_run_blender_job = structure.run_blender_job


def run_blender_job(credential: dict[str, str], job: dict[str, Any], job_dir: Path):
    try:
        return _original_run_blender_job(credential, job, job_dir)
    except Exception as exc:
        stderr_tail = _tail(job_dir / "blender.stderr.log")
        stdout_tail = _tail(job_dir / "blender.stdout.log", 500)
        result_summary = ""
        try:
            result = json.loads((job_dir / "result.json").read_text(encoding="utf-8"))
            result_summary = " result_status=%s checks=%s" % (result.get("status"), result.get("checks"))
        except Exception:
            pass
        detail = "%s; stderr_tail=%s; stdout_tail=%s;%s" % (exc, stderr_tail, stdout_tail, result_summary)
        raise core.WorkerError(detail[:950]) from exc


def self_test() -> int:
    failures: list[str] = []
    if WORKER_VERSION != "0.2.2-ai3d-structure-gatefix":
        failures.append("worker version mismatch")
    if JOB_KEY.endswith("002") or COMMAND_ID.endswith("002-NEVER-TEAR"):
        failures.append("old canary identity reused")
    if ALLOWED_ACTIONS != frozenset({"ai3d_structure_module_v1"}):
        failures.append("allowlist widened")
    try:
        plan = structure._valid_plan()
        plan["run_id"] = RUN_ID
        structure.sanitize_plan(plan)
    except Exception as exc:
        failures.append("valid plan rejected: %s" % exc)
    try:
        source = prev._original_bundled_file("blender_structure_module_canary_v022.py").read_text(encoding="utf-8")
        if "base.all = _qa_gate_all" not in source or "vals[:-1]" not in source:
            failures.append("QA gate fix marker missing")
    except Exception as exc:
        failures.append("QA gate fix source unreadable: %s" % exc)
    result = {
        "schema_version": "never-tear-ai3d-structure-worker-selftest-v3",
        "worker_version": WORKER_VERSION,
        "job_key": JOB_KEY,
        "protocol": PROTOCOL,
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "qa_gate_fix": True,
        "failure_log_tail_reporting": True,
        "arbitrary_shell": False,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0 if not failures else 23


core.bundled_file = _v022_bundled_file
structure.run_blender_job = run_blender_job
core.run_blender_job = run_blender_job
core.claim = prev.claim
core.complete_pass = prev.complete_pass
core.complete_fail = prev.complete_fail
core.process_job = prev.process_job
core.sanitize_plan = structure.sanitize_plan
core.validate_result = structure.validate_result
core.self_test = self_test

if __name__ == "__main__":
    raise SystemExit(core.main())
