"""Fixed, no-argument CSMC canary cycle.

Executed only through bridge.csmc_approved_python after SHA-256 pin validation.
It performs the already-approved read-only P4.1 observer capture and writes a
small local resume marker under LOCALAPPDATA. It does not upload private ZIP
bytes and accepts no command-line or cloud-supplied arguments.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

try:
    from bridge import csmc_observer_action
except ModuleNotFoundError:
    import csmc_observer_action

STATE_SCHEMA = "ukie_csmc_auto_cycle_state_v1"


def _state_file() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise RuntimeError("LOCALAPPDATA is unavailable")
    root = Path(local) / "UKIE_AI_BRIDGE" / "csmc" / "state"
    root.mkdir(parents=True, exist_ok=True)
    return root / "latest_cycle.json"


def _write_state(payload: dict[str, Any]) -> str:
    path = _state_file()
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
    tmp = path.with_suffix(".json.tmp")
    tmp.write_bytes(raw)
    tmp.replace(path)
    return hashlib.sha256(raw).hexdigest()


def main_worker_cycle() -> dict[str, Any]:
    capture = csmc_observer_action.run_capture()
    state = {
        "schema_version": STATE_SCHEMA,
        "action": "csmc_pipeline_cycle",
        "capture": {
            "zip_name": capture.get("zip_name"),
            "zip_size": capture.get("zip_size"),
            "zip_sha256": capture.get("zip_sha256"),
            "candidate_count": capture.get("candidate_count"),
            "scan_reason": capture.get("scan_reason"),
            "observer_version": capture.get("observer_version"),
            "sidecar_sha256": capture.get("sidecar_sha256"),
        },
        "artifact_transfer": "LOCAL_FIXED_ROOT_ONLY",
        "next_resume": "SCHEDULED_TASK_CAN_REENTER_SAME_HASH_POLICY",
    }
    state_sha256 = _write_state(state)
    return {
        **capture,
        "schema_version": "ukie_csmc_pipeline_cycle_v1",
        "action": "csmc_pipeline_cycle",
        "state_saved": True,
        "state_sha256": state_sha256,
        "resume_ready": True,
        "artifact_transfer": "LOCAL_FIXED_ROOT_ONLY",
    }
