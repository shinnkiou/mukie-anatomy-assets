"""Verified portable Blender bootstrap for UKIE AI BRIDGE P0.15.

Downloads only the exact BP3D production ZIP and its official SHA256 file from
download.blender.org, verifies the archive, rejects unsafe ZIP paths, and extracts
into the Bridge-owned LocalAppData tool directory. It never uninstalls or modifies
existing Blender installations and requires no administrator privileges.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

try:
    from .blender_selector import PIN, portable_root, select_pinned_blender
except ImportError:
    from blender_selector import PIN, portable_root, select_pinned_blender

BASE = "https://download.blender.org/release/Blender4.2"
ZIP_NAME = f"blender-{PIN}-windows-x64.zip"
SHA_NAME = f"blender-{PIN}.sha256"
MAX_ARCHIVE_BYTES = 500 * 1024 * 1024
MAX_EXTRACTED_BYTES = 2 * 1024 * 1024 * 1024


class BlenderBootstrapError(RuntimeError):
    pass


def _download(url: str, destination: Path, max_bytes: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "UKIE-AI-BRIDGE/0.15"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as handle:
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise BlenderBootstrapError("download exceeded configured byte limit")
            handle.write(chunk)
        handle.flush()
        os.fsync(handle.fileno())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_sha(text: str) -> str:
    for line in text.splitlines():
        if ZIP_NAME not in line:
            continue
        match = re.search(r"\b([0-9a-fA-F]{64})\b", line)
        if match:
            return match.group(1).lower()
    raise BlenderBootstrapError("official SHA256 file did not contain the pinned Windows ZIP hash")


def _safe_extract(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    total = 0
    with zipfile.ZipFile(archive, "r") as zf:
        for info in zf.infolist():
            total += int(info.file_size)
            if total > MAX_EXTRACTED_BYTES:
                raise BlenderBootstrapError("archive extracted size exceeded configured limit")
            target = (destination / info.filename).resolve()
            if destination != target and destination not in target.parents:
                raise BlenderBootstrapError("unsafe path found in Blender ZIP")
        zf.extractall(destination)


def bootstrap_pinned_blender() -> dict:
    before = select_pinned_blender()
    if before.get("found"):
        return {"status": "ALREADY_INSTALLED", "blender": before, "download_performed": False}

    root = portable_root()
    root.parent.mkdir(parents=True, exist_ok=True)
    stage_parent = root.parent
    with tempfile.TemporaryDirectory(prefix="blender-p015-", dir=stage_parent) as temp:
        temp_path = Path(temp)
        archive = temp_path / ZIP_NAME
        sha_file = temp_path / SHA_NAME
        _download(f"{BASE}/{SHA_NAME}", sha_file, 1024 * 1024)
        _download(f"{BASE}/{ZIP_NAME}", archive, MAX_ARCHIVE_BYTES)
        expected = _expected_sha(sha_file.read_text(encoding="utf-8", errors="replace"))
        actual = _sha256(archive)
        if actual.lower() != expected:
            raise BlenderBootstrapError("Blender ZIP SHA256 mismatch")

        extract_root = temp_path / "extract"
        _safe_extract(archive, extract_root)
        extracted = extract_root / f"blender-{PIN}-windows-x64"
        exe = extracted / "blender.exe"
        if not exe.is_file():
            raise BlenderBootstrapError("verified archive did not contain expected blender.exe")

        if root.exists():
            shutil.rmtree(root)
        os.replace(extracted, root)

    after = select_pinned_blender()
    if not after.get("found"):
        raise BlenderBootstrapError("portable Blender extracted but exact pin was not selectable")
    return {
        "status": "INSTALLED_VERIFIED_PORTABLE",
        "download_performed": True,
        "source": f"{BASE}/{ZIP_NAME}",
        "sha256_verified": True,
        "install_root": str(root),
        "blender": after,
    }
