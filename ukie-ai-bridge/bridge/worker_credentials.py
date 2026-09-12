"""Windows user-bound credential storage for the P0.18 worker transport.

The device secret is generated locally and protected with Windows DPAPI. Only its
SHA-256 is stored in Supabase. There is deliberately no plaintext fallback.
"""

from __future__ import annotations

import base64
import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path
from typing import Any


class WorkerCredentialError(RuntimeError):
    pass


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def credential_path() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "UKIE_AI_BRIDGE" / "worker"
    root.mkdir(parents=True, exist_ok=True)
    return root / "credential.json"


def _blob_from_bytes(data: bytes) -> tuple[DATA_BLOB, Any]:
    buf = (ctypes.c_ubyte * len(data))(*data)
    return DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))), buf


def _bytes_from_blob(blob: DATA_BLOB) -> bytes:
    if not blob.pbData or blob.cbData == 0:
        return b""
    return ctypes.string_at(blob.pbData, blob.cbData)


def protect_secret(secret: str) -> str:
    if os.name != "nt":
        raise WorkerCredentialError("DPAPI credential protection requires Windows")
    raw = secret.encode("utf-8")
    in_blob, keepalive = _blob_from_bytes(raw)
    out_blob = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    ok = crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        "UKIE AI BRIDGE worker token",
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    _ = keepalive
    if not ok:
        raise WorkerCredentialError(f"CryptProtectData failed: {ctypes.GetLastError()}")
    try:
        return base64.b64encode(_bytes_from_blob(out_blob)).decode("ascii")
    finally:
        if out_blob.pbData:
            kernel32.LocalFree(out_blob.pbData)


def unprotect_secret(encoded: str) -> str:
    if os.name != "nt":
        raise WorkerCredentialError("DPAPI credential protection requires Windows")
    try:
        protected = base64.b64decode(encoded.encode("ascii"), validate=True)
    except Exception as exc:
        raise WorkerCredentialError("credential contains invalid protected data") from exc
    in_blob, keepalive = _blob_from_bytes(protected)
    out_blob = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    _ = keepalive
    if not ok:
        raise WorkerCredentialError(f"CryptUnprotectData failed: {ctypes.GetLastError()}")
    try:
        return _bytes_from_blob(out_blob).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WorkerCredentialError("credential plaintext is invalid UTF-8") from exc
    finally:
        if out_blob.pbData:
            kernel32.LocalFree(out_blob.pbData)


def load_credential(path: Path | None = None) -> dict[str, Any] | None:
    path = path or credential_path()
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerCredentialError(f"credential file unreadable: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "ukie_worker_credential_v1":
        raise WorkerCredentialError("unsupported worker credential schema")
    protected = value.get("protected_device_token")
    if not isinstance(protected, str) or not protected:
        raise WorkerCredentialError("protected device token missing")
    value["device_token"] = unprotect_secret(protected)
    return value


def save_credential(value: dict[str, Any], device_token: str, path: Path | None = None) -> Path:
    path = path or credential_path()
    if len(device_token) < 48:
        raise WorkerCredentialError("refusing to store a weak device token")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(value)
    payload["schema_version"] = "ukie_worker_credential_v1"
    payload["protected_device_token"] = protect_secret(device_token)
    payload.pop("device_token", None)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    os.replace(temp, path)
    return path
