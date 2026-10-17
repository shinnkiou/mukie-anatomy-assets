"""Safe local handoff for physical acceptance evidence.

This module does not call Google APIs and never claims cloud durability. It copies a
locally verified, release-bound physical acceptance ZIP into a user-selected sync
folder using a temporary file + fsync + atomic rename, then writes SHA-256 and JSON
sidecars. The cloud control plane must later discover/read back the file and compare
SHA-256 before Drive durability is considered proven.
"""

from __future__ import annotations

import ctypes
import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .acceptance_verifier import AcceptanceVerificationError, verify_acceptance_bundle
    from .validator import sha256_file
except ImportError:
    from acceptance_verifier import AcceptanceVerificationError, verify_acceptance_bundle
    from validator import sha256_file


CONFIG_SCHEMA = "ukie_handoff_config_v1"
HANDOFF_SCHEMA = "ukie_acceptance_handoff_v1"
INBOX_NAME = "UKIE_AI_BRIDGE_INBOX"
SAFE_TOKEN = re.compile(r"[^A-Za-z0-9_.-]+")


class HandoffError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_config_path() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "UKIE_AI_BRIDGE" / "config" / "handoff.json"
    return Path.home() / ".ukie_ai_bridge" / "handoff.json"


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    data = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with temp.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("wb") as handle:
            handle.write(text.encode("ascii"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _assert_writable_directory(path: Path) -> Path:
    path = path.expanduser().resolve()
    if not path.is_dir():
        raise HandoffError(f"handoff destination is not a directory: {path}")
    probe = path / f".ukie_write_probe_{uuid.uuid4().hex}.tmp"
    try:
        with probe.open("xb") as handle:
            handle.write(b"UKIE_HANDOFF_WRITE_TEST")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise HandoffError(f"handoff destination is not writable: {exc}") from exc
    finally:
        probe.unlink(missing_ok=True)
    return path


def _pick_folder_windows() -> Path | None:
    if os.name != "nt":
        raise HandoffError("interactive handoff folder selection is supported only on Windows")

    class BROWSEINFOW(ctypes.Structure):
        _fields_ = [
            ("hwndOwner", ctypes.c_void_p),
            ("pidlRoot", ctypes.c_void_p),
            ("pszDisplayName", ctypes.c_wchar_p),
            ("lpszTitle", ctypes.c_wchar_p),
            ("ulFlags", ctypes.c_uint),
            ("lpfn", ctypes.c_void_p),
            ("lParam", ctypes.c_void_p),
            ("iImage", ctypes.c_int),
        ]

    shell32 = ctypes.windll.shell32
    ole32 = ctypes.windll.ole32
    display = ctypes.create_unicode_buffer(32768)
    path_buffer = ctypes.create_unicode_buffer(32768)
    initialized = False
    try:
        # COINIT_APARTMENTTHREADED. RPC_E_CHANGED_MODE is not fatal for the old
        # shell folder picker; it means the process already chose another model.
        hr = int(ole32.CoInitializeEx(None, 0x2))
        initialized = hr in (0, 1)
        bi = BROWSEINFOW()
        bi.hwndOwner = None
        bi.pidlRoot = None
        bi.pszDisplayName = ctypes.cast(display, ctypes.c_wchar_p)
        bi.lpszTitle = "Select your Google Drive for Desktop sync folder for UKIE AI BRIDGE results"
        bi.ulFlags = 0x0001 | 0x0040  # BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE
        bi.lpfn = None
        bi.lParam = None
        bi.iImage = 0
        pidl = shell32.SHBrowseForFolderW(ctypes.byref(bi))
        if not pidl:
            return None
        try:
            if not shell32.SHGetPathFromIDListW(pidl, path_buffer):
                raise HandoffError("Windows folder picker returned a non-filesystem location")
            return Path(path_buffer.value)
        finally:
            ole32.CoTaskMemFree(pidl)
    finally:
        if initialized:
            ole32.CoUninitialize()


def configure_handoff(
    destination: str | Path | None = None,
    *,
    config_path: str | Path | None = None,
    interactive: bool = True,
) -> dict[str, Any]:
    if destination is None:
        if not interactive:
            raise HandoffError("handoff destination is not configured")
        selected = _pick_folder_windows()
        if selected is None:
            raise HandoffError("handoff folder selection was cancelled")
    else:
        selected = Path(destination)

    selected = _assert_writable_directory(selected)
    inbox = selected / INBOX_NAME
    inbox.mkdir(parents=True, exist_ok=True)
    inbox = _assert_writable_directory(inbox)

    value = {
        "schema_version": CONFIG_SCHEMA,
        "configured_at": utc_now(),
        "selection_mode": "WINDOWS_FOLDER_PICKER" if destination is None else "EXPLICIT_LOCAL_TEST_OR_ADMIN",
        "sync_root": str(selected),
        "inbox": str(inbox),
        "cloud_provider_claim": "USER_SELECTED_GOOGLE_DRIVE_FOR_DESKTOP_FOLDER",
        "cloud_presence_proven": False,
        "drive_readback_proven": False,
        "ready_for_ai": False,
    }
    path = Path(config_path) if config_path is not None else default_config_path()
    _write_json_atomic(path, value)
    return {**value, "config_path": str(path)}


def load_handoff_config(config_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path is not None else default_config_path()
    if not path.is_file():
        raise HandoffError(f"handoff config not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HandoffError(f"handoff config is unreadable: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != CONFIG_SCHEMA:
        raise HandoffError("handoff config schema is unsupported")
    inbox = value.get("inbox")
    if not isinstance(inbox, str) or not inbox:
        raise HandoffError("handoff config does not contain an inbox")
    value["inbox"] = str(_assert_writable_directory(Path(inbox)))
    return value


def ensure_handoff_config(config_path: str | Path | None = None) -> dict[str, Any]:
    try:
        return load_handoff_config(config_path)
    except HandoffError as exc:
        path = Path(config_path) if config_path is not None else default_config_path()
        if path.exists():
            raise
        return configure_handoff(config_path=config_path, interactive=True)


def _safe_token(value: Any, fallback: str) -> str:
    text = SAFE_TOKEN.sub("_", str(value or "")).strip("._-")
    return text[:120] or fallback


def _copy_atomic_verified(source: Path, destination: Path, expected_sha: str, expected_size: int) -> dict[str, Any]:
    if destination.exists():
        if destination.is_file() and destination.stat().st_size == expected_size and sha256_file(destination).lower() == expected_sha.lower():
            return {"status": "ALREADY_PRESENT_MATCH", "path": destination, "sha256": expected_sha, "byte_size": expected_size}
        raise HandoffError(f"handoff destination collision with different content: {destination.name}")

    temp = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.partial")
    try:
        with source.open("rb") as src, temp.open("xb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())
        actual_size = temp.stat().st_size
        actual_sha = sha256_file(temp)
        if actual_size != expected_size or actual_sha.lower() != expected_sha.lower():
            raise HandoffError("handoff copy failed post-copy size/SHA verification")
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)

    return {"status": "COPIED_AND_VERIFIED", "path": destination, "sha256": expected_sha, "byte_size": expected_size}


def handoff_acceptance(
    acceptance_result: dict[str, Any],
    *,
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    allow_synthetic_test_fixture: bool = False,
) -> dict[str, Any]:
    if not isinstance(acceptance_result, dict):
        raise HandoffError("acceptance result must be an object")
    bundle_info = acceptance_result.get("acceptance_bundle") if isinstance(acceptance_result.get("acceptance_bundle"), dict) else {}
    source_value = bundle_info.get("path")
    expected_sha = bundle_info.get("sha256")
    expected_size = bundle_info.get("byte_size")
    if not isinstance(source_value, str) or not source_value:
        raise HandoffError("acceptance result does not contain a bundle path")
    source = Path(source_value).resolve()
    if not source.is_file() or source.suffix.lower() != ".zip":
        raise HandoffError("acceptance bundle is missing")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise HandoffError("acceptance result does not contain a valid SHA-256")
    if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size <= 0:
        raise HandoffError("acceptance result does not contain a valid byte size")
    if source.stat().st_size != expected_size or sha256_file(source).lower() != expected_sha.lower():
        raise HandoffError("acceptance bundle no longer matches the producer manifest")

    release = acceptance_result.get("release") if isinstance(acceptance_result.get("release"), dict) else {}
    release_key = release.get("release_key")
    acceptance_id = acceptance_result.get("acceptance_id")
    if acceptance_result.get("release_binding_status") != "BOUND" or not isinstance(release_key, str) or not release_key.startswith("BRIDGE_P"):
        raise HandoffError("acceptance is not bound to a release")
    if not isinstance(acceptance_id, str) or not acceptance_id.startswith("PHYSICAL_ACCEPTANCE_"):
        raise HandoffError("acceptance_id is invalid")

    try:
        verified = verify_acceptance_bundle(
            source,
            expected_release_key=release_key,
            allow_synthetic_test_fixture=allow_synthetic_test_fixture,
        )
    except AcceptanceVerificationError as exc:
        raise HandoffError(f"local acceptance verification blocked handoff: {exc}") from exc

    cfg = config if config is not None else load_handoff_config(config_path)
    if not isinstance(cfg, dict) or cfg.get("schema_version") != CONFIG_SCHEMA:
        raise HandoffError("handoff config object is invalid")
    inbox = _assert_writable_directory(Path(str(cfg.get("inbox") or "")))

    filename = f"UKIE_PHYSICAL_ACCEPTANCE__{_safe_token(release_key, 'RELEASE')}__{_safe_token(acceptance_id, 'ACCEPTANCE')}.zip"
    destination = inbox / filename
    copied = _copy_atomic_verified(source, destination, expected_sha, expected_size)

    sha_sidecar = inbox / f"{filename}.sha256"
    handoff_sidecar = inbox / f"{filename}.handoff.json"
    _write_text_atomic(sha_sidecar, f"{expected_sha.lower()}  {filename}\n")
    receipt = {
        "schema_version": HANDOFF_SCHEMA,
        "status": "LOCAL_HANDOFF_COMPLETE",
        "created_at": utc_now(),
        "acceptance_id": acceptance_id,
        "acceptance_status": acceptance_result.get("status"),
        "release_key": release_key,
        "bridge_version": release.get("bridge_version"),
        "commit_sha": release.get("commit_sha"),
        "workflow_run_id": release.get("workflow_run_id"),
        "file_name": filename,
        "byte_size": expected_size,
        "sha256": expected_sha.lower(),
        "copy_status": copied["status"],
        "local_acceptance_verification": verified.get("status"),
        "local_core_ready": acceptance_result.get("local_core_ready") is True,
        "local_gpu_render_ready": acceptance_result.get("local_gpu_render_ready") is True,
        "sync_folder_copy_proven": True,
        "drive_cloud_presence_proven": False,
        "drive_readback_proven": False,
        "ready_for_ai": False,
        "promotion_performed": False,
        "next_gate": "CLOUD_DISCOVERY_RAW_READBACK_AND_ACCEPTANCE_VERIFICATION",
    }
    _write_json_atomic(handoff_sidecar, receipt)

    # Re-read the final file after sidecars are durable. This still proves only
    # local sync-folder integrity, not Google Drive cloud synchronization.
    final_sha = sha256_file(destination)
    if destination.stat().st_size != expected_size or final_sha.lower() != expected_sha.lower():
        raise HandoffError("final handoff file failed local readback verification")

    return {
        **receipt,
        "handoff_json": str(handoff_sidecar),
        "sha256_sidecar": str(sha_sidecar),
        "local_destination": str(destination),
    }


def run_acceptance_and_handoff(
    workspace: Path,
    release_info: dict[str, Any],
    run_acceptance,
    *,
    state_root: Path | None = None,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    # Resolve/select the inbox first. If the user cancels the first-run folder
    # picker, do not start Blender and create evidence they may think was synced.
    config = ensure_handoff_config(config_path)
    acceptance = run_acceptance(workspace, state_root, release_info)
    handoff = handoff_acceptance(acceptance, config=config)
    return {
        "schema_version": "ukie_acceptance_and_handoff_v1",
        "status": "ACCEPTANCE_HANDOFF_COMPLETE",
        "acceptance": acceptance,
        "handoff": handoff,
        "ready_for_ai": False,
        "drive_readback_proven": False,
        "next_gate": "CLOUD_DISCOVERY_RAW_READBACK_AND_ACCEPTANCE_VERIFICATION",
    }
