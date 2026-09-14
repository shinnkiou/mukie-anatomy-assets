# SPDX-License-Identifier: MIT
"""AI3D-013 Structure CANARY v0.2.3 bundled-loader repair companion.

CANARY-003 proved the isolated transport reaches real Blender but failed because
Blender's embedded Python could not import a sibling module from the PyInstaller
one-file extraction directory. v0.2.3 uses a new CANARY-004 identity and a fixed
wrapper that explicitly loads the trusted bundled base executor by absolute
sibling path. The six-command boundary and no-promotion policy remain unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import ai3d_worker as core
import ai3d_structure_worker as structure
import ai3d_structure_worker_v021 as prev

WORKER_VERSION = "0.2.3-ai3d-structure-loaderfix"
PROTOCOL = "never-tear-ai3d-worker-v1"
ACTION = "ai3d_structure_module_v1"
JOB_KEY = "AI3D-013-PHYSICAL-STRUCTURE-CANARY-004"
COMMAND_ID = "AI3D-013-STRUCTURE-CANARY-004-NEVER-TEAR"
RUN_ID = JOB_KEY
EDGE_URL = "https://vbuokbwglauibabinaqs.supabase.co/functions/v1/ai3d-worker-transport-structure-canary-v4"
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


def _v023_bundled_file(name: str):
    if name == "blender_structure_module_canary.py":
        return prev._original_bundled_file("blender_structure_module_canary_v023.py")
    return prev._original_bundled_file(name)


def _tail(path: Path, limit: int = 900) -> str:
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
        stdout_tail = _tail(job_dir / "blender.stdout.log", 650)
        result_summary = ""
        try:
            result = json.loads((job_dir / "result.json").read_text(encoding="utf-8"))
            result_summary = " result_status=%s checks=%s" % (result.get("status"), result.get("checks"))
        except Exception:
            pass
        detail = "%s; stderr_tail=%s; stdout_tail=%s;%s" % (exc, stderr_tail, stdout_tail, result_summary)
        raise core.WorkerError(detail[:1000]) from exc


def self_test() -> int:
    failures: list[str] = []
    if WORKER_VERSION != "0.2.3-ai3d-structure-loaderfix":
        failures.append("worker version mismatch")
    if JOB_KEY.endswith("003") or COMMAND_ID.endswith("003-NEVER-TEAR"):
        failures.append("old canary identity reused")
    if ALLOWED_ACTIONS != frozenset({"ai3d_structure_module_v1"}):
        failures.append("allowlist widened")
    if not EDGE_URL.endswith("/ai3d-worker-transport-structure-canary-v4"):
        failures.append("v4 transport not isolated")
    try:
        plan = structure._valid_plan()
        plan["run_id"] = RUN_ID
        structure.sanitize_plan(plan)
    except Exception as exc:
        failures.append("valid plan rejected: %s" % exc)
    try:
        source = prev._original_bundled_file("blender_structure_module_canary_v023.py").read_text(encoding="utf-8")
        required = ["spec_from_file_location", "base.RUN_ID = RUN_ID", "base.all = _qa_gate_all", "vals[:-1]"]
        for marker in required:
            if marker not in source:
                failures.append("loader/gate marker missing: %s" % marker)
        if "import blender_structure_module_canary as base" in source:
            failures.append("unsafe normal sibling import retained")
    except Exception as exc:
        failures.append("loader-fix source unreadable: %s" % exc)
    result = {
        "schema_version": "never-tear-ai3d-structure-worker-selftest-v4",
        "worker_version": WORKER_VERSION,
        "job_key": JOB_KEY,
        "protocol": PROTOCOL,
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "explicit_bundled_loader": True,
        "qa_gate_fix": True,
        "failure_log_tail_reporting": True,
        "arbitrary_shell": False,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0 if not failures else 23


core.bundled_file = _v023_bundled_file
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
