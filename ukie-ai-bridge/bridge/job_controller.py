"""Exact-once local execution controller for UKIE AI BRIDGE.

This controller is transport-agnostic. Base44/Supabase/Drive delivery may be
at-least-once, but the local worker does not call the executor twice for the same
immutable job envelope unless a future explicit retry/attempt contract exists.
"""

from __future__ import annotations

from typing import Any, Callable

try:
    from .state_store import BridgeStateStore
    from .validator import ValidatedJob
except ImportError:
    from state_store import BridgeStateStore
    from validator import ValidatedJob


Executor = Callable[[], dict[str, Any]]


def execute_once(job: ValidatedJob, store: BridgeStateStore, executor: Executor) -> dict[str, Any]:
    claim = store.mark_started(job)
    decision = claim["decision"]
    if decision != "START":
        return {
            "executed": False,
            "decision": decision,
            "job_id": job.job_id,
            "receipt": claim["receipt"],
        }

    try:
        result = executor()
    except TimeoutError as exc:
        failure = {"status": "TIMEOUT", "error": str(exc)}
        store.mark_failed(job, failure, status="TIMEOUT")
        return {"executed": True, "decision": "TIMEOUT", "job_id": job.job_id, "result": failure}
    except Exception as exc:
        failure = {"status": "FAILED", "error": str(exc), "error_type": type(exc).__name__}
        store.mark_failed(job, failure, status="FAILED")
        return {"executed": True, "decision": "FAILED", "job_id": job.job_id, "result": failure}

    if not isinstance(result, dict):
        failure = {"status": "FAILED", "error": "executor result must be an object"}
        store.mark_failed(job, failure, status="FAILED")
        return {"executed": True, "decision": "FAILED", "job_id": job.job_id, "result": failure}

    status = result.get("status")
    if status == "LOCAL_SAVED":
        store.mark_local_saved(job, result)
        decision = "LOCAL_SAVED"
    elif status == "VERIFIED":
        store.mark_verified(job, result)
        decision = "VERIFIED"
    elif status == "COMPLETED":
        # Reserved for the future end-to-end path after remote readback verification.
        store.mark_completed(job, result)
        decision = "COMPLETED"
    elif status == "TIMEOUT":
        store.mark_failed(job, result, status="TIMEOUT")
        decision = "TIMEOUT"
    elif status in {"FAILED", "INTERRUPTED", "NEEDS_HUMAN"}:
        store.mark_failed(job, result, status=status)
        decision = status
    else:
        failure = {
            "status": "FAILED",
            "error": "executor returned an unsupported terminal/local status",
            "reported_status": status,
        }
        store.mark_failed(job, failure, status="FAILED")
        return {"executed": True, "decision": "FAILED", "job_id": job.job_id, "result": failure}

    return {
        "executed": True,
        "decision": decision,
        "job_id": job.job_id,
        "result": result,
        "receipt": store.snapshot()["jobs"][job.job_id],
    }
