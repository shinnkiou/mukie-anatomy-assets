"""Fail-closed Worker extension for one narrow CSMC observer action.

The experimental CSMC worker reuses an already-approved P0.18.2 device
credential, but sends heartbeat/claim/complete only to the isolated CSMC canary
Edge Function. It cannot create a new pairing through the canary endpoint.

No cloud-supplied command, executable, path, keyboard sequence, mouse action, or
filesystem root is accepted.
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

PRODUCTION_EDGE_URL = base.EDGE_URL
CSMC_CANARY_EDGE_URL = "https://vbuokbwglauibabinaqs.supabase.co/functions/v1/ukie-worker-transport-csmc-canary"
if CSMC_CANARY_EDGE_URL == PRODUCTION_EDGE_URL:
    raise RuntimeError("CSMC canary transport must not equal the production worker transport")

# The canary executable has its own process-local module graph. Repoint only
# that process-local transport. Production source/executable configuration is
# unchanged.
base.EDGE_URL = CSMC_CANARY_EDGE_URL

load_release_info = base.load_release_info
_complete = base._complete


def set_worker_version(version: str) -> None:
    base.WORKER_VERSION = version


def _existing_credential() -> dict[str, Any]:
    credential = base.load_credential()
    if not credential or not credential.get("device_key") or not credential.get("device_token"):
        raise WorkerTransportError(
            "CSMC canary requires an existing approved P0.18.2 worker pairing; "
            "pair with the production worker first"
        )
    return credential


def begin_pairing(*, open_browser: bool = False) -> dict[str, Any]:
    """Compatibility entrypoint: never creates a pairing on the canary endpoint."""
    del open_browser
    credential = _existing_credential()
    return {"status": "ALREADY_PAIRED", "device_key": credential["device_key"], "canary_pairing_created": False}


def refresh_pairing() -> dict[str, Any]:
    credential = _existing_credential()
    return {"status": "PAIRED", "device_key": credential["device_key"], "canary_pairing_created": False}


def heartbeat() -> dict[str, Any]:
    """Authenticate against the canary endpoint without sending device inventory."""
    credential = _existing_credential()
    return base._request(
        {"action": "heartbeat"},
        device_key=credential["device_key"],
        device_token=credential["device_token"],
    )


def claim() -> dict[str, Any]:
    credential = _existing_credential()
    return base._request(
        {"action": "claim"},
        device_key=credential["device_key"],
        device_token=credential["device_token"],
    )


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

    # device_status stays in the local inherited safety surface only for
    # compatibility/self-test. The isolated queue can claim only
    # csmc_observer_capture.
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
