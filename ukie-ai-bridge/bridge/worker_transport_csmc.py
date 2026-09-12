"""Fail-closed Worker extension for isolated CSMC canary actions.

The canary reuses an already-approved P0.18.2 device credential and talks only
to the isolated CSMC transport. Cloud jobs cannot supply commands, executable
paths, filesystem roots, URLs, keyboard/mouse sequences, or arbitrary args.
"""
from __future__ import annotations

import time
from typing import Any, Callable

try:
    from . import worker_transport as base
    from .csmc_observer_action import ACTION_NAME as CAPTURE_ACTION, CsmcObserverActionError, run_capture
    from .csmc_observer_diagnose_action import ACTION_NAME as DIAG_ACTION, CsmcObserverDiagnoseError, run_diagnose
    from .csmc_artifact_upload_action import ACTION_NAME as UPLOAD_ACTION, CsmcArtifactUploadError, run_upload
except ImportError:
    import worker_transport as base
    from csmc_observer_action import ACTION_NAME as CAPTURE_ACTION, CsmcObserverActionError, run_capture
    from csmc_observer_diagnose_action import ACTION_NAME as DIAG_ACTION, CsmcObserverDiagnoseError, run_diagnose
    from csmc_artifact_upload_action import ACTION_NAME as UPLOAD_ACTION, CsmcArtifactUploadError, run_upload

WORKER_PROTOCOL = base.WORKER_PROTOCOL
PAIRING_UI_URL = base.PAIRING_UI_URL
POLL_SECONDS = base.POLL_SECONDS
HEARTBEAT_SECONDS = base.HEARTBEAT_SECONDS
CSMC_ACTIONS = frozenset({CAPTURE_ACTION, DIAG_ACTION, UPLOAD_ACTION})
ALLOWED_ACTIONS = frozenset(set(base.ALLOWED_ACTIONS) | set(CSMC_ACTIONS))
WorkerTransportError = base.WorkerTransportError

PRODUCTION_EDGE_URL = base.EDGE_URL
CSMC_CANARY_EDGE_URL = "https://vbuokbwglauibabinaqs.supabase.co/functions/v1/ukie-worker-transport-csmc-canary"
if CSMC_CANARY_EDGE_URL == PRODUCTION_EDGE_URL:
    raise RuntimeError("CSMC canary transport must not equal production worker transport")
base.EDGE_URL = CSMC_CANARY_EDGE_URL

load_release_info = base.load_release_info
_complete = base._complete


def set_worker_version(version: str) -> None:
    base.WORKER_VERSION = version


def _existing_credential() -> dict[str, Any]:
    credential = base.load_credential()
    if not credential or not credential.get("device_key") or not credential.get("device_token"):
        raise WorkerTransportError("CSMC canary requires an existing approved P0.18.2 worker pairing")
    return credential


def begin_pairing(*, open_browser: bool = False) -> dict[str, Any]:
    del open_browser
    credential = _existing_credential()
    return {"status": "ALREADY_PAIRED", "device_key": credential["device_key"], "canary_pairing_created": False}


def refresh_pairing() -> dict[str, Any]:
    credential = _existing_credential()
    return {"status": "PAIRED", "device_key": credential["device_key"], "canary_pairing_created": False}


def heartbeat() -> dict[str, Any]:
    credential = _existing_credential()
    return base._request({"action": "heartbeat"}, device_key=credential["device_key"], device_token=credential["device_token"])


def claim() -> dict[str, Any]:
    credential = _existing_credential()
    return base._request({"action": "claim"}, device_key=credential["device_key"], device_token=credential["device_token"])


def _fail(job: dict[str, Any], code: str, exc: Exception) -> dict[str, Any]:
    return _complete(job, outcome="FAIL", error_code=code, error_detail={"error_type": type(exc).__name__, "error": str(exc)[:1000]})


def execute_claimed_job(
    job: dict[str, Any],
    *,
    status_provider: Callable[[], dict[str, Any]] | None = None,
    observer_provider: Callable[[], dict[str, Any]] | None = None,
    diagnose_provider: Callable[[], dict[str, Any]] | None = None,
    upload_provider: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    action = str(job.get("action") or "")
    if action not in ALLOWED_ACTIONS:
        return _complete(job, outcome="FAIL", error_code="WORKER_ACTION_NOT_ALLOWLISTED", error_detail={"action": action})
    if action == CAPTURE_ACTION:
        provider = observer_provider or run_capture
        try: result = provider()
        except CsmcObserverActionError as exc: return _fail(job, exc.code, exc)
        except Exception as exc: return _fail(job, "CSMC_OBSERVER_FAILED", exc)
        return _complete(job, outcome="PASS", result=result)
    if action == DIAG_ACTION:
        provider = diagnose_provider or run_diagnose
        try: result = provider()
        except CsmcObserverDiagnoseError as exc: return _fail(job, exc.code, exc)
        except Exception as exc: return _fail(job, "CSMC_DIAG_FAILED", exc)
        return _complete(job, outcome="PASS", result=result)
    if action == UPLOAD_ACTION:
        provider = upload_provider or run_upload
        try: result = provider()
        except CsmcArtifactUploadError as exc: return _fail(job, exc.code, exc)
        except Exception as exc: return _fail(job, "CSMC_UPLOAD_FAILED", exc)
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
            heartbeat(); last_heartbeat = now
        claimed = claim()
        if claimed.get("status") == "CLAIMED" and claimed.get("job"):
            execute_claimed_job(claimed["job"]); continue
        time.sleep(poll_seconds)
