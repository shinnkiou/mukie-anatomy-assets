"""Offline verification for UKIE AI BRIDGE physical Blender canary bundles.

A canary ZIP is untrusted evidence until this module validates its archive shape,
source hash, exact-once receipt, semantic scene report, job manifest and complete
PNG structure. No archive member is extracted or executed.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
import zlib
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


CANARY_SCHEMA = "ukie_blender_canary_v1"
MAX_FILES = 128
MAX_TOTAL_UNCOMPRESSED = 768 * 1024 * 1024
MAX_SINGLE_UNCOMPRESSED = 384 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250.0
MAX_PNG_CHUNK = 64 * 1024 * 1024
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


class CanaryVerificationError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_member_name(name: str) -> PurePosixPath:
    if not name or "\\" in name:
        raise CanaryVerificationError("archive contains an invalid member name")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CanaryVerificationError(f"unsafe archive member path: {name}")
    return path


def _read_json(zf: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        value = json.loads(zf.read(name).decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CanaryVerificationError(f"invalid JSON member {name}: {exc}") from exc
    if not isinstance(value, dict):
        raise CanaryVerificationError(f"JSON member {name} must be an object")
    return value


def _png_info(data: bytes, name: str) -> dict[str, int]:
    """Validate a complete non-interlaced PNG including chunk CRCs and IDAT."""
    if len(data) < 1024 or data[:8] != PNG_SIGNATURE:
        raise CanaryVerificationError(f"{name} is not a sufficiently sized PNG")

    pos = 8
    chunk_index = 0
    width = height = bit_depth = color_type = interlace = None
    idat_parts: list[bytes] = []
    saw_iend = False

    while pos < len(data):
        if pos + 12 > len(data):
            raise CanaryVerificationError(f"{name} has a truncated PNG chunk")
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        if length > MAX_PNG_CHUNK:
            raise CanaryVerificationError(f"{name} contains an oversized PNG chunk")
        chunk_type = data[pos + 4:pos + 8]
        data_start = pos + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(data):
            raise CanaryVerificationError(f"{name} has a truncated PNG chunk payload")
        payload = data[data_start:data_end]
        stored_crc = struct.unpack(">I", data[data_end:crc_end])[0]
        calculated_crc = zlib.crc32(chunk_type)
        calculated_crc = zlib.crc32(payload, calculated_crc) & 0xFFFFFFFF
        if stored_crc != calculated_crc:
            raise CanaryVerificationError(f"{name} PNG CRC mismatch in {chunk_type!r}")

        if chunk_index == 0:
            if chunk_type != b"IHDR" or length != 13:
                raise CanaryVerificationError(f"{name} must begin with a 13-byte IHDR")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if width < 64 or height < 64:
                raise CanaryVerificationError(f"{name} dimensions are implausibly small")
            if compression != 0 or filtering != 0 or interlace != 0:
                raise CanaryVerificationError(f"{name} uses an unsupported PNG encoding mode")
            if color_type not in PNG_CHANNELS or bit_depth not in {8, 16}:
                raise CanaryVerificationError(f"{name} uses an unsupported PNG color layout")
        elif chunk_type == b"IHDR":
            raise CanaryVerificationError(f"{name} contains multiple IHDR chunks")

        if chunk_type == b"IDAT":
            idat_parts.append(payload)
        elif chunk_type == b"IEND":
            if length != 0:
                raise CanaryVerificationError(f"{name} has an invalid IEND")
            saw_iend = True
            pos = crc_end
            if pos != len(data):
                raise CanaryVerificationError(f"{name} contains trailing bytes after IEND")
            break

        pos = crc_end
        chunk_index += 1

    if not saw_iend or not idat_parts or width is None or height is None:
        raise CanaryVerificationError(f"{name} is missing required PNG chunks")

    try:
        raw = zlib.decompress(b"".join(idat_parts))
    except zlib.error as exc:
        raise CanaryVerificationError(f"{name} IDAT stream cannot be decompressed") from exc

    channels = PNG_CHANNELS[int(color_type)]
    scanline_bytes = (int(width) * channels * int(bit_depth) + 7) // 8
    stride = 1 + scanline_bytes
    expected = int(height) * stride
    if len(raw) != expected:
        raise CanaryVerificationError(f"{name} decompressed raster size does not match IHDR")
    for offset in range(0, len(raw), stride):
        if raw[offset] > 4:
            raise CanaryVerificationError(f"{name} contains an invalid PNG scanline filter")

    return {
        "width": int(width),
        "height": int(height),
        "byte_size": len(data),
        "bit_depth": int(bit_depth),
        "color_type": int(color_type),
    }


def _validate_archive_shape(zf: zipfile.ZipFile) -> dict[str, Any]:
    infos = zf.infolist()
    if not infos or len(infos) > MAX_FILES:
        raise CanaryVerificationError("archive file count is outside the allowed range")

    total = 0
    for info in infos:
        _safe_member_name(info.filename)
        if info.is_dir():
            continue
        if info.file_size < 0 or info.file_size > MAX_SINGLE_UNCOMPRESSED:
            raise CanaryVerificationError(f"archive member is too large: {info.filename}")
        total += info.file_size
        if total > MAX_TOTAL_UNCOMPRESSED:
            raise CanaryVerificationError("archive uncompressed size exceeds the safety cap")
        compressed = max(1, info.compress_size)
        ratio = info.file_size / compressed
        if info.file_size > 1024 * 1024 and ratio > MAX_COMPRESSION_RATIO:
            raise CanaryVerificationError(f"suspicious compression ratio: {info.filename}")
    return {"file_count": len(infos), "total_uncompressed_bytes": int(total)}


def verify_canary_bundle(bundle: str | Path, expected_sha256: str | None = None) -> dict[str, Any]:
    path = Path(bundle)
    if not path.is_file() or path.suffix.lower() != ".zip":
        raise CanaryVerificationError("canary bundle must be an existing .zip file")

    bundle_sha = sha256_file(path)
    if expected_sha256 is not None:
        if not HEX64.fullmatch(expected_sha256):
            raise CanaryVerificationError("expected bundle SHA-256 is invalid")
        if bundle_sha.lower() != expected_sha256.lower():
            raise CanaryVerificationError("bundle SHA-256 does not match expected readback hash")

    try:
        zf = zipfile.ZipFile(path, "r")
    except zipfile.BadZipFile as exc:
        raise CanaryVerificationError("canary bundle is not a valid ZIP") from exc

    with zf:
        archive = _validate_archive_shape(zf)
        files = {info.filename for info in zf.infolist() if not info.is_dir()}
        manifest_names = [name for name in files if PurePosixPath(name).name == "canary_manifest.json"]
        if len(manifest_names) != 1:
            raise CanaryVerificationError("bundle must contain exactly one canary_manifest.json")

        manifest_name = manifest_names[0]
        root = PurePosixPath(manifest_name).parent
        if str(root) in {"", "."}:
            raise CanaryVerificationError("canary manifest must be inside a canary root directory")
        manifest = _read_json(zf, manifest_name)

        if manifest.get("schema_version") != CANARY_SCHEMA:
            raise CanaryVerificationError("unsupported canary schema")
        if manifest.get("status") != "CANARY_LOCAL_PASS":
            raise CanaryVerificationError("canary manifest does not report local PASS")
        canary_id = manifest.get("canary_id")
        job_id = manifest.get("job_id")
        if not isinstance(canary_id, str) or not canary_id.startswith("BLENDER_CANARY_"):
            raise CanaryVerificationError("invalid canary_id")
        if root.name != canary_id:
            raise CanaryVerificationError("archive root and canary_id disagree")
        if not isinstance(job_id, str) or not job_id.startswith("CANARY_JOB_"):
            raise CanaryVerificationError("invalid canary job_id")

        source = manifest.get("source") if isinstance(manifest.get("source"), dict) else {}
        source_sha = source.get("sha256")
        if not isinstance(source_sha, str) or not HEX64.fullmatch(source_sha):
            raise CanaryVerificationError("canary source SHA-256 is invalid")
        if source.get("unchanged_after_analysis") is not True:
            raise CanaryVerificationError("canary source was not proven immutable")

        exact_once = manifest.get("exact_once") if isinstance(manifest.get("exact_once"), dict) else {}
        if exact_once.get("decision") != "LOCAL_SAVED" or exact_once.get("executed") is not True:
            raise CanaryVerificationError("exact-once execution evidence is not a fresh LOCAL_SAVED run")

        semantic = manifest.get("semantic_verification") if isinstance(manifest.get("semantic_verification"), dict) else {}
        if semantic.get("status") != "PASS" or semantic.get("vertices") != 8 or semantic.get("polygons") != 6:
            raise CanaryVerificationError("canary semantic verification does not match the fixed cube")
        previews = manifest.get("previews") if isinstance(manifest.get("previews"), dict) else {}
        if previews.get("front") is not True or previews.get("side") is not True:
            raise CanaryVerificationError("canary manifest is missing front/side preview PASS")
        if manifest.get("ready_for_ai") is not False:
            raise CanaryVerificationError("local canary must not self-promote ready_for_ai")

        source_name = str(root / "canary_source.blend")
        if source_name not in files:
            raise CanaryVerificationError("canary source blend is missing from bundle")
        source_bytes = zf.read(source_name)
        if sha256_bytes(source_bytes).lower() != source_sha.lower():
            raise CanaryVerificationError("bundled canary source SHA-256 does not match manifest")
        if int(source.get("byte_size") or -1) != len(source_bytes):
            raise CanaryVerificationError("bundled canary source size does not match manifest")

        job_root = root / "jobs" / job_id
        job_manifest_name = str(job_root / "manifest.json")
        scene_name = str(job_root / "scene_before.json")
        front_name = str(job_root / "preview_front.png")
        side_name = str(job_root / "preview_side.png")
        for required in (job_manifest_name, scene_name, front_name, side_name):
            if required not in files:
                raise CanaryVerificationError(f"required canary evidence is missing: {required}")

        job_manifest = _read_json(zf, job_manifest_name)
        if job_manifest.get("job_id") != job_id or job_manifest.get("status") != "LOCAL_SAVED":
            raise CanaryVerificationError("job manifest does not prove LOCAL_SAVED for canary job")
        jm_source = job_manifest.get("source") if isinstance(job_manifest.get("source"), dict) else {}
        if jm_source.get("source_unchanged") is not True:
            raise CanaryVerificationError("job manifest does not prove source immutability")
        artifact_validation = job_manifest.get("artifact_validation") if isinstance(job_manifest.get("artifact_validation"), dict) else {}
        if artifact_validation.get("status") != "PASS":
            raise CanaryVerificationError("job artifact contract did not PASS")

        scene = _read_json(zf, scene_name)
        cube = None
        for obj in scene.get("objects", []):
            if isinstance(obj, dict) and obj.get("name") == "UKIE_CANARY_CUBE":
                cube = obj
                break
        mesh = cube.get("mesh") if isinstance(cube, dict) and isinstance(cube.get("mesh"), dict) else {}
        if mesh.get("vertices") != 8 or mesh.get("polygons") != 6:
            raise CanaryVerificationError("scene_before.json does not contain the fixed canary topology")

        front = _png_info(zf.read(front_name), front_name)
        side = _png_info(zf.read(side_name), side_name)

        return {
            "schema_version": "ukie_canary_evidence_verification_v2",
            "status": "CANARY_EVIDENCE_VALID",
            "canary_id": canary_id,
            "job_id": job_id,
            "bundle": {
                "file_name": path.name,
                "byte_size": path.stat().st_size,
                "sha256": bundle_sha,
                "expected_sha256_matched": expected_sha256 is not None,
            },
            "archive": archive,
            "source": {"sha256": source_sha, "byte_size": len(source_bytes), "unchanged": True},
            "semantic": {"vertices": 8, "polygons": 6, "blender_version": semantic.get("blender_version")},
            "previews": {"front": front, "side": side},
            "exact_once": {"decision": "LOCAL_SAVED", "executed": True},
            "drive_readback_proven": expected_sha256 is not None,
            "ready_for_ai": False,
            "next_gate": "REGISTER_CANARY_AND_PROMOTE_RELEASE" if expected_sha256 is not None else "DRIVE_UPLOAD_READBACK",
        }
