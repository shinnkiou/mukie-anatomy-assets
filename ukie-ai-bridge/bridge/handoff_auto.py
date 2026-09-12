"""P0.14 automatic handoff policy layered over the proven P0.13 handoff core."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import handoff as base
    from .drive_discovery import discover_drive_sync_root
except ImportError:
    import handoff as base
    from drive_discovery import discover_drive_sync_root


DRIVE_TARGET = "DRIVE_SYNC_CANDIDATE"
LOCAL_TARGET = "LOCAL_OUTBOX_ONLY"
LOCAL_OUTBOX_NAME = "handoff_outbox"


def default_local_outbox() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "UKIE_AI_BRIDGE" / LOCAL_OUTBOX_NAME
    return Path.home() / ".ukie_ai_bridge" / LOCAL_OUTBOX_NAME


def _config_path(config_path: str | Path | None) -> Path:
    return Path(config_path) if config_path is not None else base.default_config_path()


def _write_config(path: Path, value: dict[str, Any]) -> dict[str, Any]:
    base._write_json_atomic(path, value)
    return {**value, "config_path": str(path)}


def _backup_stale_config(path: Path) -> str | None:
    if not path.is_file():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(f"{path.stem}.stale.{stamp}{path.suffix}")
    try:
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        return str(backup)
    except OSError:
        return None


def _augment_config(value: dict[str, Any], *, target_kind: str, discovery: dict[str, Any]) -> dict[str, Any]:
    drive_candidate = target_kind == DRIVE_TARGET
    value = dict(value)
    value.update({
        "selection_mode": "AUTO_DETECTED_DRIVE_SYNC_ROOT" if drive_candidate else "AUTO_LOCAL_OUTBOX_FALLBACK",
        "target_kind": target_kind,
        "drive_sync_candidate": drive_candidate,
        "cloud_provider_claim": "AUTO_DETECTED_GOOGLE_DRIVE_FOR_DESKTOP_CANDIDATE" if drive_candidate else "NONE_LOCAL_OUTBOX_ONLY",
        "discovery": discovery,
        "cloud_presence_proven": False,
        "drive_readback_proven": False,
        "ready_for_ai": False,
    })
    return value


def configure_handoff_auto(
    destination: str | Path | None = None,
    *,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    path = _config_path(config_path)
    if destination is not None:
        value = base.configure_handoff(Path(destination), config_path=path, interactive=False)
        discovery = {"status": "EXPLICIT", "selected": str(Path(destination))}
        value = _augment_config(value, target_kind=DRIVE_TARGET, discovery=discovery)
        return _write_config(path, {k: v for k, v in value.items() if k != "config_path"})

    discovery = discover_drive_sync_root()
    selected = discovery.get("selected")
    if isinstance(selected, str) and selected:
        value = base.configure_handoff(Path(selected), config_path=path, interactive=False)
        value = _augment_config(value, target_kind=DRIVE_TARGET, discovery=discovery)
        return _write_config(path, {k: v for k, v in value.items() if k != "config_path"})

    outbox = default_local_outbox()
    outbox.mkdir(parents=True, exist_ok=True)
    value = base.configure_handoff(outbox, config_path=path, interactive=False)
    value = _augment_config(value, target_kind=LOCAL_TARGET, discovery=discovery)
    # For local fallback the inbox is the outbox itself, not a fake Drive subfolder.
    value["sync_root"] = None
    value["inbox"] = str(outbox.resolve())
    return _write_config(path, {k: v for k, v in value.items() if k != "config_path"})


def ensure_handoff_config_auto(config_path: str | Path | None = None) -> dict[str, Any]:
    path = _config_path(config_path)
    try:
        current = base.load_handoff_config(path)
        current.setdefault("target_kind", DRIVE_TARGET)
        current.setdefault("drive_sync_candidate", current.get("target_kind") == DRIVE_TARGET)
        return current
    except base.HandoffError as exc:
        backup = _backup_stale_config(path)
        value = configure_handoff_auto(config_path=path)
        value["recovered_from_config_error"] = str(exc)
        value["stale_config_backup"] = backup
        return value


def _rewrite_local_fallback_receipt(result: dict[str, Any]) -> dict[str, Any]:
    value = dict(result)
    value.update({
        "handoff_target_kind": LOCAL_TARGET,
        "drive_sync_candidate": False,
        "sync_folder_copy_proven": False,
        "local_outbox_copy_proven": True,
        "drive_cloud_presence_proven": False,
        "drive_readback_proven": False,
        "ready_for_ai": False,
        "promotion_performed": False,
        "next_gate": "MOVE_OR_UPLOAD_LOCAL_OUTBOX_TO_DRIVE_THEN_CLOUD_READBACK",
    })
    sidecar = value.get("handoff_json")
    if isinstance(sidecar, str) and sidecar:
        base._write_json_atomic(Path(sidecar), {k: v for k, v in value.items() if k not in {"handoff_json", "sha256_sidecar", "local_destination"}})
    return value


def run_acceptance_and_handoff_auto(
    workspace: Path,
    release_info: dict[str, Any],
    run_acceptance,
    *,
    state_root: Path | None = None,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    config = ensure_handoff_config_auto(config_path)
    acceptance = run_acceptance(workspace, state_root, release_info)
    handoff = base.handoff_acceptance(acceptance, config=config)
    drive_candidate = config.get("drive_sync_candidate") is True

    if drive_candidate:
        handoff.update({
            "handoff_target_kind": DRIVE_TARGET,
            "drive_sync_candidate": True,
            "local_outbox_copy_proven": False,
        })
        status = "ACCEPTANCE_HANDOFF_COMPLETE"
    else:
        handoff = _rewrite_local_fallback_receipt(handoff)
        status = "ACCEPTANCE_LOCAL_OUTBOX_COMPLETE"

    return {
        "schema_version": "ukie_acceptance_and_handoff_v1",
        "status": status,
        "acceptance": acceptance,
        "handoff": handoff,
        "ready_for_ai": False,
        "drive_readback_proven": False,
        "next_gate": handoff.get("next_gate"),
    }
