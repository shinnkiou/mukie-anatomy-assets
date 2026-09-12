"""Fixed-root artifact uploader for the isolated CSMC canary.

It can read only a fixed LOCALAPPDATA artifact directory, selects only strict
CSMC capture ZIP names, hashes them locally, and sends bytes only to one fixed
Base44 backend function backed by the already-connected Google Drive connector.
The worker never receives a path, URL, folder ID, or command from the cloud and
never deletes the local original.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from . import worker_transport as base
except ImportError:
    import worker_transport as base

ACTION_NAME = "csmc_artifact_upload"
FIXED_INGRESS_URL = "https://base44.app/api/apps/6aa2743da37b11162682c01f/functions/csmc-artifact-upload"
FIXED_BASE44_APP_ID = "6aa2743da37b11162682c01f"
FIXED_DRIVE_FOLDER_ID = "1EN2R6DrjsyObR2YpVFFxf1K3wFkMdzwv"
ARTIFACT_SUBDIR = Path("UKIE_AI_BRIDGE") / "csmc-canary" / "artifacts"
NAME_RE = re.compile(r"^CAPTURE_\d{8}_\d{6}_P4(?:_1(?:_DIAG)?)?\.zip$")
MAX_BYTES = 128 * 1024 * 1024


class CsmcArtifactUploadError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _root() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise CsmcArtifactUploadError("CSMC_LOCALAPPDATA_MISSING", "LOCALAPPDATA is unavailable")
    root = (Path(local) / ARTIFACT_SUBDIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _latest_allowed(root: Path) -> Path:
    candidates: list[Path] = []
    for p in root.iterdir():
        if p.is_file() and NAME_RE.fullmatch(p.name):
            rp = p.resolve()
            if rp.parent != root:
                continue
            size = p.stat().st_size
            if 0 < size <= MAX_BYTES:
                candidates.append(rp)
    if not candidates:
        raise CsmcArtifactUploadError("CSMC_UPLOAD_NO_ARTIFACT", "no strict CSMC capture ZIP exists in fixed artifact root")
    candidates.sort(key=lambda p: (p.stat().st_mtime_ns, p.name), reverse=True)
    return candidates[0]


def _credential() -> dict[str, Any]:
    value = base.load_credential()
    if not value or not value.get("device_key") or not value.get("device_token"):
        raise CsmcArtifactUploadError("CSMC_UPLOAD_CREDENTIAL_MISSING", "existing approved worker credential is required")
    return value


def run_upload() -> dict[str, Any]:
    root = _root()
    path = _latest_allowed(root)
    size = path.stat().st_size
    sha = _sha256(path)
    cred = _credential()
    data = path.read_bytes()
    if len(data) != size or hashlib.sha256(data).hexdigest() != sha:
        raise CsmcArtifactUploadError("CSMC_UPLOAD_LOCAL_VERIFY_FAILED", "artifact changed during fixed-root read")
    headers = {
        "Content-Type": "application/zip",
        "User-Agent": "UKIE-AI-BRIDGE-CSMC-ARTIFACT/2",
        "X-App-Id": FIXED_BASE44_APP_ID,
        "Base44-Functions-Version": "preview",
        "X-UKIE-Device-Key": str(cred["device_key"]),
        "X-UKIE-Device-Token": str(cred["device_token"]),
        "X-CSMC-Filename": path.name,
        "X-CSMC-SHA256": sha,
        "X-CSMC-Size": str(size),
    }
    req = urllib.request.Request(FIXED_INGRESS_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            raw = response.read(256 * 1024)
    except urllib.error.HTTPError as exc:
        detail = exc.read(64 * 1024)
        raise CsmcArtifactUploadError("CSMC_UPLOAD_HTTP_FAILED", f"ingress HTTP {exc.code}: {detail[:500]!r}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise CsmcArtifactUploadError("CSMC_UPLOAD_TRANSPORT_FAILED", str(exc)) from exc
    try:
        result = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise CsmcArtifactUploadError("CSMC_UPLOAD_RESPONSE_INVALID", "ingress returned invalid JSON") from exc
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise CsmcArtifactUploadError("CSMC_UPLOAD_REJECTED", str(result.get("error") if isinstance(result, dict) else "invalid"))
    if result.get("readback_verified") is not True:
        raise CsmcArtifactUploadError("CSMC_UPLOAD_READBACK_UNVERIFIED", "provider raw readback was not verified")
    if int(result.get("size") or -1) != size or str(result.get("sha256") or "").lower() != sha:
        raise CsmcArtifactUploadError("CSMC_UPLOAD_READBACK_MISMATCH", "provider readback size/SHA mismatch")
    if str(result.get("folder_id") or "") != FIXED_DRIVE_FOLDER_ID:
        raise CsmcArtifactUploadError("CSMC_UPLOAD_DESTINATION_MISMATCH", "ingress did not confirm fixed Drive folder")
    return {
        "schema_version": "csmc_artifact_upload_result_v2",
        "action": ACTION_NAME,
        "status": "UPLOADED_READBACK_VERIFIED",
        "local_filename": path.name,
        "local_root_kind": "LOCALAPPDATA_CSMC_CANARY_ARTIFACTS_ONLY",
        "size": size,
        "sha256": sha,
        "drive_file_id": str(result.get("file_id") or "")[:256],
        "drive_folder_id": FIXED_DRIVE_FOLDER_ID,
        "readback_verified": True,
        "local_original_retained": True,
        "arbitrary_url_enabled": False,
        "arbitrary_path_enabled": False,
        "credential_source": "BASE44_GOOGLE_DRIVE_CONNECTOR",
    }
