"""P0.18 fail-closed Supabase worker transport.

The worker is deliberately capability-scoped. P0.18 can heartbeat and claim only
`device_status`. It cannot execute arbitrary shell/PowerShell/EXE commands and it
never receives a filesystem path from the cloud.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import secrets
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from . import main as bridge_main
    from .worker_credentials import WorkerCredentialError, load_credential, save_credential
except ImportError:
    import main as bridge_main
    from worker_credentials import WorkerCredentialError, load_credential, save_credential


WORKER_VERSION = "0.18.0-p0.18"
WORKER_PROTOCOL = "ukie_worker_v1"
EDGE_URL = "https://vbuokbwglauibabinaqs.supabase.co/functions/v1/ukie-worker-transport"
PAIRING_UI_URL = "https://sync-ops-base.base44.app/worker-pair"
ALLOWED_ACTIONS = {"device_status"}
POLL_SECONDS = 10
HEARTBEAT_SECONDS = 30


class WorkerTransportError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _release_info_candidates() -> list[Path]:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "RELEASE_INFO.json")
    candidates.extend([
        Path.cwd() / "RELEASE_INFO.json",
        Path(__file__).resolve().parents[1] / "RELEASE_INFO.json",
    ])
    return candidates


def load_release_info() -> dict[str, Any]:
    override = os.environ.get("UKIE_RELEASE_KEY")
    if override:
        return {"release_key": override, "bridge_version": os.environ.get("UKIE_BRIDGE_VERSION", WORKER_VERSION)}
    for path in _release_info_candidates():
        if not path.is_file():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and str(value.get("release_key", "")).startswith("BRIDGE_P"):
            return value
    raise WorkerTransportError("RELEASE_INFO.json was not found next to the worker executable")


def _request(payload: dict[str, Any], *, device_key: str | None = None, device_token: str | None = None, timeout: int = 20) -> dict[str, Any]:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(body) > 64 * 1024:
        raise WorkerTransportError("request exceeded P0.18 body limit")
    headers = {"Content-Type": "application/json", "User-Agent": f"UKIE-AI-BRIDGE/{WORKER_VERSION}"}
    if device_key is not None:
        headers["X-UKIE-Device-Key"] = device_key
    if device_token is not None:
        headers["X-UKIE-Device-Token"] = device_token
    request = urllib.request.Request(EDGE_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(256 * 1024)
    except urllib.error.HTTPError as exc:
        raw = exc.read(64 * 1024)
        try:
            detail = json.loads(raw.decode("utf-8"))
        except Exception:
            detail = {"error": f"HTTP_{exc.code}"}
        raise WorkerTransportError(f"transport HTTP {exc.code}: {detail.get('error', 'unknown')}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise WorkerTransportError(f"transport unavailable: {exc}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerTransportError("transport returned invalid JSON") from exc
    if not isinstance(value, dict) or value.get("ok") is not True:
        raise WorkerTransportError(f"transport rejected request: {value.get('error', 'unknown') if isinstance(value, dict) else 'invalid'}")
    return value


def device_name() -> str:
    value = platform.node().strip()
    if not value:
        raise WorkerTransportError("Windows device name is empty")
    return value[:120]


def begin_pairing(*, open_browser: bool = False) -> dict[str, Any]:
    release = load_release_info()
    existing = load_credential()
    if existing and existing.get("device_key"):
        return {
            "status": "ALREADY_PAIRED",
            "device_key": existing.get("device_key"),
            "credential_path": str(Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "UKIE_AI_BRIDGE" / "worker" / "credential.json"),
        }

    token = existing.get("device_token") if existing else secrets.token_urlsafe(48)
    secret_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    response = _request({
        "action": "pair_request",
        "device_name": device_name(),
        "secret_hash": secret_hash,
        "worker_version": WORKER_VERSION,
        "release_key": release["release_key"],
    })
    credential = {
        "device_name": device_name(),
        "device_key": None,
        "pairing_id": response["pairing_id"],
        "pairing_expires_at": response["expires_at"],
        "worker_version": WORKER_VERSION,
        "worker_protocol": WORKER_PROTOCOL,
        "release_key": release["release_key"],
        "paired_at": None,
    }
    save_credential(credential, token)
    pair_url = f"{PAIRING_UI_URL}?pairing_id={response['pairing_id']}&code={response['pairing_code']}"
    if open_browser:
        webbrowser.open(pair_url, new=2)
    return {
        "status": "PAIRING_REQUIRED",
        "pairing_id": response["pairing_id"],
        "pairing_code": response["pairing_code"],
        "expires_at": response["expires_at"],
        "pairing_url": pair_url,
        "secret_stored_in_cloud": False,
    }


def refresh_pairing() -> dict[str, Any]:
    credential = load_credential()
    if not credential:
        raise WorkerTransportError("worker is not paired; run worker-pair first")
    if credential.get("device_key"):
        return {"status": "PAIRED", "device_key": credential["device_key"]}
    pairing_id = credential.get("pairing_id")
    if not pairing_id:
        raise WorkerTransportError("credential has no pairing_id")
    response = _request({
        "action": "pair_status",
        "pairing_id": pairing_id,
        "device_token": credential["device_token"],
    })
    if response.get("approved") is True and response.get("device_key"):
        credential["device_key"] = response["device_key"]
        credential["paired_at"] = response.get("approved_at") or utc_now()
        save_credential(credential, credential["device_token"])
        return {"status": "PAIRED", "device_key": credential["device_key"], "paired_at": credential["paired_at"]}
    return {"status": response.get("status", "PENDING"), "approved": False}


def _paired_credential() -> dict[str, Any]:
    credential = load_credential()
    if not credential:
        raise WorkerTransportError("worker credential is missing")
    if not credential.get("device_key"):
        result = refresh_pairing()
        if result.get("status") != "PAIRED":
            raise WorkerTransportError(f"worker pairing is not approved: {result.get('status')}")
        credential = load_credential()
    if not credential or not credential.get("device_key") or not credential.get("device_token"):
        raise WorkerTransportError("worker pairing is incomplete")
    return credential


def _device_status_for_cloud() -> dict[str, Any]:
    result = bridge_main.device_status()
    result["worker_version"] = WORKER_VERSION
    result["worker_protocol"] = WORKER_PROTOCOL
    return result


def heartbeat() -> dict[str, Any]:
    credential = _paired_credential()
    status = _device_status_for_cloud()
    return _request({
        "action": "heartbeat",
        "worker_version": WORKER_VERSION,
        "bridge_version": status.get("bridge_version"),
        "hardware_info": {
            "platform": status.get("platform", {}),
            "memory": status.get("memory", {}),
            "gpu": status.get("gpu", {}),
        },
        "blender_info": status.get("blender", {}),
        "capabilities": status.get("capabilities", []),
    }, device_key=credential["device_key"], device_token=credential["device_token"])


def claim() -> dict[str, Any]:
    credential = _paired_credential()
    return _request({"action": "claim"}, device_key=credential["device_key"], device_token=credential["device_token"])


def _complete(job: dict[str, Any], *, outcome: str, result: dict[str, Any] | None = None, error_code: str | None = None, error_detail: dict[str, Any] | None = None) -> dict[str, Any]:
    credential = _paired_credential()
    return _request({
        "action": "complete",
        "job_id": job["id"],
        "lease_owner": job["lease_owner"],
        "outcome": outcome,
        "result": result or {},
        "error_code": error_code,
        "error_detail": error_detail or {},
    }, device_key=credential["device_key"], device_token=credential["device_token"])


def execute_claimed_job(job: dict[str, Any], *, status_provider: Callable[[], dict[str, Any]] | None = None) -> dict[str, Any]:
    action = str(job.get("action") or "")
    if action not in ALLOWED_ACTIONS:
        return _complete(job, outcome="FAIL", error_code="WORKER_ACTION_NOT_ALLOWLISTED", error_detail={"action": action})
    if action == "device_status":
        provider = status_provider or _device_status_for_cloud
        try:
            result = provider()
        except Exception as exc:
            return _complete(job, outcome="FAIL", error_code="DEVICE_STATUS_FAILED", error_detail={"error_type": type(exc).__name__, "error": str(exc)[:1000]})
        return _complete(job, outcome="PASS", result=result)
    return _complete(job, outcome="FAIL", error_code="WORKER_ACTION_UNIMPLEMENTED", error_detail={"action": action})


def run_once() -> dict[str, Any]:
    hb = heartbeat()
    claimed = claim()
    if claimed.get("status") == "NO_JOB" or not claimed.get("job"):
        return {"status": "IDLE", "heartbeat": hb.get("status"), "worker_version": WORKER_VERSION}
    result = execute_claimed_job(claimed["job"])
    return {"status": result.get("status"), "job_key": result.get("job_key"), "worker_version": WORKER_VERSION}


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
