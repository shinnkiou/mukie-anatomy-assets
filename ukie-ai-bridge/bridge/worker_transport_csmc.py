"""Fail-closed Worker extension for one narrow CSMC observer action.

This module deliberately leaves the P0.18 transport/auth/lease contract intact and
adds only `csmc_observer_capture`. No cloud-supplied command, executable, path,
keyboard sequence, mouse action, or filesystem root is accepted.
"""

from __future__ import annotations

import time
from typing import Any, Callable

try:
    from . import worker_transport as base
    from .csmc_observer_action import ACTION_NAME, CsmcObserverActionError, run_capture
except ImportError:
    import worker_transport as base
    from csmc_observer_action import ACTION_NAME, CsmcObserverActionError, run_capture

WORKER_PROTOCOL = base.WORKER_PROTOCOL
PAIRING_UI_URL = base.PAIRING_UI_URL
POLL_SECONDS = base.POLL_SECONDS
HEARTBEAT_SECONDS = base.HEARTBEAT_SECONDS
ALLOWED_ACTIONS = frozenset(set(base.ALLOWED_ACTIONS) | {ACTION_NAME})
WorkerTransportError = base.WorkerTransportError

# Forward the P0.18 transport surface used by the CLI.
begin_pairing = base.begin_pairing
refresh_pairing = base.refresh_pairing
heartbeat = base.heartbeat
claim = base.claim
load_release_info = base.load_release_info
_complete = base._complete


def set_worker_version(version: str) -> None:
    base.WORKER_VERSION = version


def execute_claimed_job(
    job: dict[str, Any],
    *,
    status_provider: Callable[[], dict[str, Any]] | None = None,
    observer_provider: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    action = str(job.get("action") or "")
    if action not in ALLOWED_ACTIONS:
        return _complete(job, outcome="FAIL", error_code="WORKER_ACTION_NOT_ALLOWLISTED", error_detail={"action": action})

    if action == ACTION_NAME:
        provider = observer_provider or run_capture
        try:
            result = provider()
        except CsmcObserverActionError as exc:
            return _complete(
                job,
                outcome="FAIL",
                error_code=exc.code,
                error_detail={"error_type": type(exc).__name__, "error": str(exc)[:1000]},
            )
        except Exception as exc:
            return _complete(
                job,
                outcome="FAIL",
                error_code="CSMC_OBSERVER_FAILED",
                error_detail={"error_type": type(exc).__name__, "error": str(exc)[:1000]},
            )
        return _complete(job, outcome="PASS", result=result)

    return base.execute_claimed_job(job, status_provider=status_provider)


def run_once() -> dict[str, Any]:
    hb = heartbeat()
    claimed = claim()
    if claimed.get("status") == "NO_JOB" or not claimed.get("job"):
        return {"status": "IDLE", "heartbeat": hb.get("status"), "worker_version": base.WORKER_VERSION}
    result = execute_claimed_job(claimed["job"])
    return {"status": result.get("status"), "job_key": result.get("job_key"), "worker_version": base.WORKER_VERSION}


def run_loop(*, poll_seconds: int = POLL_SECONDS) -> None:
    if poll_seconds < 5 or poll_seconds > 300:
        raise WorkerTransportError("poll interval must be between 5 and 300 seconds")
    last_heartbeat = 0.0
    while True:
        now = time.monotonic()
        if now - last_heartbeat >= HEARTBEAT_SECONDS:
            heartbeat()
            last_heartbeat = now
        claimed = claim()
        if claimed.get("status") == "CLAIMED" and claimed.get("job"):
            execute_claimed_job(claimed["job"])
            continue
        time.sleep(poll_seconds)
