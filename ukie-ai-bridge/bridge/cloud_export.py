"""Prepare the latest UKIE physical-acceptance triplet for a user-controlled cloud upload.

This module never uploads anything. It copies exactly one validated acceptance ZIP plus
its SHA256 and handoff sidecars from the Bridge-owned local outbox into a visible
Downloads folder, preserving the original evidence and never claiming cloud presence.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ACCEPTANCE_PREFIX = "UKIE_PHYSICAL_ACCEPTANCE__"
UPLOAD_DIR_NAME = "UKIE_AI_BRIDGE_UPLOAD_READY"


class CloudExportError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _default_outbox() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise CloudExportError("LOCALAPPDATA is unavailable")
    return Path(local) / "UKIE_AI_BRIDGE" / "handoff_outbox"


def _default_downloads() -> Path:
    user = os.environ.get("USERPROFILE")
    if not user:
        raise CloudExportError("USERPROFILE is unavailable")
    return Path(user) / "Downloads" / UPLOAD_DIR_NAME


def _parse_sha_sidecar(path: Path, zip_name: str) -> str:
    data = path.read_bytes()
    if any(byte > 0x7F for byte in data):
        raise CloudExportError("SHA sidecar must be ASCII")
    text = data.decode("ascii").strip()
    parts = text.split("  ", 1)
    if len(parts) != 2 or len(parts[0]) != 64 or parts[1] != zip_name:
        raise CloudExportError("SHA sidecar format or target mismatch")
    try:
        int(parts[0], 16)
    except ValueError as exc:
        raise CloudExportError("SHA sidecar hash is not hexadecimal") from exc
    return parts[0].lower()


def _parse_handoff(path: Path, zip_name: str, zip_size: int, zip_sha: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CloudExportError(f"handoff JSON unreadable: {exc}") from exc
    if not isinstance(value, dict):
        raise CloudExportError("handoff JSON root must be an object")
    if value.get("schema_version") != "ukie_acceptance_handoff_v1":
        raise CloudExportError("unsupported handoff schema")
    if value.get("status") != "LOCAL_HANDOFF_COMPLETE":
        raise CloudExportError("handoff is not locally complete")
    if value.get("file_name") != zip_name:
        raise CloudExportError("handoff filename mismatch")
    if int(value.get("byte_size") or 0) != zip_size:
        raise CloudExportError("handoff byte size mismatch")
    if str(value.get("sha256") or "").lower() != zip_sha:
        raise CloudExportError("handoff SHA mismatch")
    copy_proven = value.get("sync_folder_copy_proven") is True or (
        value.get("handoff_target_kind") == "LOCAL_OUTBOX_ONLY"
        and value.get("local_outbox_copy_proven") is True
    )
    if not copy_proven:
        raise CloudExportError("handoff local copy is not proven")
    for field in ("drive_cloud_presence_proven", "drive_readback_proven", "ready_for_ai", "promotion_performed"):
        if value.get(field) is not False:
            raise CloudExportError(f"handoff illegally preclaims {field}")
    return value


def find_latest_triplet(outbox: Path | None = None) -> dict:
    root = (outbox or _default_outbox()).resolve()
    if not root.is_dir():
        raise CloudExportError(f"local outbox not found: {root}")

    candidates: list[tuple[float, Path]] = []
    for path in root.glob(f"{ACCEPTANCE_PREFIX}*.zip"):
        if path.is_file():
            candidates.append((path.stat().st_mtime, path))
    if not candidates:
        raise CloudExportError("no physical acceptance ZIP exists in local outbox")

    candidates.sort(key=lambda item: (item[0], item[1].name), reverse=True)
    errors: list[str] = []
    for _, zip_path in candidates:
        sha_path = zip_path.with_name(zip_path.name + ".sha256")
        handoff_path = zip_path.with_name(zip_path.name + ".handoff.json")
        if not sha_path.is_file() or not handoff_path.is_file():
            errors.append(f"{zip_path.name}: missing sidecar")
            continue
        try:
            zip_sha = _sha256(zip_path)
            sidecar_sha = _parse_sha_sidecar(sha_path, zip_path.name)
            if sidecar_sha != zip_sha:
                raise CloudExportError("ZIP SHA does not match sidecar")
            receipt = _parse_handoff(handoff_path, zip_path.name, zip_path.stat().st_size, zip_sha)
            return {
                "zip": zip_path,
                "sha256": sha_path,
                "handoff": handoff_path,
                "zip_sha256": zip_sha,
                "zip_size": zip_path.stat().st_size,
                "receipt": receipt,
            }
        except CloudExportError as exc:
            errors.append(f"{zip_path.name}: {exc}")
    raise CloudExportError("no valid acceptance triplet found; " + "; ".join(errors[:5]))


def _copy_verified(source: Path, destination: Path) -> str:
    expected = _sha256(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.is_file() and destination.stat().st_size == source.stat().st_size and _sha256(destination) == expected:
            return "REUSED_IDENTICAL"
        raise CloudExportError(f"destination collision with different content: {destination.name}")
    partial = destination.with_name(destination.name + ".partial")
    if partial.exists():
        partial.unlink()
    try:
        with source.open("rb") as src, partial.open("wb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())
        if partial.stat().st_size != source.stat().st_size or _sha256(partial) != expected:
            raise CloudExportError(f"copied file verification failed: {source.name}")
        os.replace(partial, destination)
    finally:
        if partial.exists():
            partial.unlink()
    return "COPIED_AND_VERIFIED"


def prepare_cloud_upload(
    outbox: Path | None = None,
    destination_root: Path | None = None,
    open_folder: bool = True,
) -> dict:
    triplet = find_latest_triplet(outbox)
    receipt = triplet["receipt"]
    destination = (destination_root or _default_downloads()).resolve()
    acceptance_id = str(receipt.get("acceptance_id") or "UNKNOWN_ACCEPTANCE")
    ready_dir = destination / acceptance_id
    ready_dir.mkdir(parents=True, exist_ok=True)

    files = []
    for kind in ("zip", "sha256", "handoff"):
        source = Path(triplet[kind])
        target = ready_dir / source.name
        status = _copy_verified(source, target)
        files.append({
            "kind": kind,
            "name": source.name,
            "byte_size": target.stat().st_size,
            "sha256": _sha256(target),
            "copy_status": status,
        })

    if open_folder and os.name == "nt":
        try:
            subprocess.Popen(["explorer.exe", str(ready_dir)], close_fds=True)
        except OSError:
            pass

    return {
        "schema_version": "ukie_cloud_export_v1",
        "status": "UPLOAD_READY_LOCAL",
        "acceptance_id": acceptance_id,
        "release_key": receipt.get("release_key"),
        "bridge_version": receipt.get("bridge_version"),
        "bundle_sha256": triplet["zip_sha256"],
        "bundle_size": triplet["zip_size"],
        "destination": str(ready_dir),
        "files": files,
        "cloud_presence_proven": False,
        "drive_readback_proven": False,
        "ready_for_ai": False,
        "promotion_performed": False,
        "next_gate": "USER_CONTROLLED_UPLOAD_THEN_PROVIDER_READBACK",
    }
