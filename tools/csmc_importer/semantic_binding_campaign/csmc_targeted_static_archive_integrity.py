#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from csmc_targeted_static_extraction_intake import validate_targeted_static_manifest

SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")
EXECUTABLE_SUFFIXES = {
    ".exe",
    ".dll",
    ".sys",
    ".com",
    ".scr",
    ".msi",
    ".msp",
    ".cpl",
    ".ocx",
}
MAX_MEMBERS = 4096
MAX_TOTAL_UNCOMPRESSED = 512 * 1024 * 1024
MAX_SINGLE_UNCOMPRESSED = 128 * 1024 * 1024
READ_CHUNK = 1024 * 1024


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA_RE.fullmatch(value))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(READ_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_member_name(name: str) -> bool:
    if not name or "\x00" in name or "\\" in name:
        return False
    path = PurePosixPath(name)
    if path.is_absolute():
        return False
    if any(part in {"", ".", ".."} for part in path.parts):
        return False
    first = path.parts[0] if path.parts else ""
    if len(first) >= 2 and first[1] == ":" and first[0].isalpha():
        return False
    return True


def _zipinfo_is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(mode)


def _declared_content_hashes(manifest: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    refs: list[tuple[str, str, str]] = []
    functions = manifest.get("functions")
    if not isinstance(functions, list):
        return refs
    for row in functions:
        if not isinstance(row, Mapping):
            continue
        va = row.get("va")
        va_text = va if isinstance(va, str) else "UNKNOWN_VA"
        if row.get("decompile_present") is True:
            refs.append((va_text, "decompile_sha256", str(row.get("decompile_sha256", ""))))
        if row.get("instruction_listing_present") is True:
            refs.append((va_text, "instruction_listing_sha256", str(row.get("instruction_listing_sha256", ""))))
    return refs


def inspect_targeted_static_archive(
    archive_path: Path,
    *,
    expected_archive_sha256: str,
    expected_member_count: int | None = None,
) -> dict[str, Any]:
    """Verify archive identity and safely hash members without extracting them."""
    reasons: list[str] = []
    digest_counts: dict[str, int] = {}
    actual_archive_sha256: str | None = None
    member_count = 0
    total_uncompressed = 0

    if not _valid_sha(expected_archive_sha256):
        reasons.append("expected_archive_sha256 must be 64-hex")

    if not archive_path.is_file():
        reasons.append("archive file is missing")
        return {
            "status": "ARCHIVE_INTEGRITY_REJECTED",
            "archive_integrity_verified": False,
            "archive_sha256": actual_archive_sha256,
            "member_count": member_count,
            "total_uncompressed_bytes": total_uncompressed,
            "digest_counts": digest_counts,
            "reasons": reasons,
        }

    try:
        actual_archive_sha256 = _sha256_file(archive_path)
    except OSError as exc:
        reasons.append(f"archive SHA-256 read error: {exc}")
    else:
        if _valid_sha(expected_archive_sha256) and actual_archive_sha256 != expected_archive_sha256.lower():
            reasons.append("archive SHA-256 mismatch")

    if not zipfile.is_zipfile(archive_path):
        reasons.append("archive is not a valid ZIP")
        return {
            "status": "ARCHIVE_INTEGRITY_REJECTED",
            "archive_integrity_verified": False,
            "archive_sha256": actual_archive_sha256,
            "member_count": member_count,
            "total_uncompressed_bytes": total_uncompressed,
            "digest_counts": digest_counts,
            "reasons": reasons,
        }

    seen_names: set[str] = set()
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            infos = [info for info in zf.infolist() if not info.is_dir()]
            member_count = len(infos)
            if member_count > MAX_MEMBERS:
                reasons.append(f"archive has too many members: {member_count} > {MAX_MEMBERS}")
            if expected_member_count is not None and member_count != expected_member_count:
                reasons.append(
                    f"archive member count mismatch: expected {expected_member_count}, got {member_count}"
                )

            for info in infos:
                if not _safe_member_name(info.filename):
                    reasons.append("archive contains unsafe member path")
                    continue
                if info.filename in seen_names:
                    reasons.append("archive contains duplicate member path")
                    continue
                seen_names.add(info.filename)

                if _zipinfo_is_symlink(info):
                    reasons.append("archive contains symlink member")
                    continue
                if info.flag_bits & 0x1:
                    reasons.append("archive contains encrypted member")
                    continue
                if info.file_size > MAX_SINGLE_UNCOMPRESSED:
                    reasons.append("archive contains oversized member")
                    continue

                total_uncompressed += info.file_size
                if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
                    reasons.append(
                        f"archive uncompressed size exceeds {MAX_TOTAL_UNCOMPRESSED} bytes"
                    )
                    break

                suffix = PurePosixPath(info.filename).suffix.lower()
                if suffix in EXECUTABLE_SUFFIXES:
                    reasons.append("archive contains executable-suffix member")
                    continue

                h = hashlib.sha256()
                prefix = b""
                with zf.open(info, "r") as member:
                    while True:
                        chunk = member.read(READ_CHUNK)
                        if not chunk:
                            break
                        if not prefix:
                            prefix = chunk[:2]
                        h.update(chunk)
                if prefix == b"MZ":
                    reasons.append("archive contains PE-like member")
                    continue

                digest = h.hexdigest()
                digest_counts[digest] = digest_counts.get(digest, 0) + 1
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        reasons.append(f"archive inspection error: {exc}")

    verified = not reasons
    return {
        "status": "ARCHIVE_INTEGRITY_VERIFIED" if verified else "ARCHIVE_INTEGRITY_REJECTED",
        "archive_integrity_verified": verified,
        "archive_sha256": actual_archive_sha256,
        "member_count": member_count,
        "total_uncompressed_bytes": total_uncompressed,
        "digest_counts": digest_counts,
        "reasons": reasons,
    }


def validate_targeted_static_package(
    manifest: Mapping[str, Any] | None,
    archive_path: Path,
    *,
    expected_archive_sha256: str,
    expected_member_count: int | None = None,
) -> dict[str, Any]:
    """Bind manifest intake to real archive bytes before static evidence review.

    This remains an integrity/completeness gate. Even success cannot admit the
    provenance bridge, serializer semantics, semantic promotion, Blender emit,
    or runtime dispatch.
    """
    m = dict(manifest or {})
    manifest_result = validate_targeted_static_manifest(m)
    archive_result = inspect_targeted_static_archive(
        archive_path,
        expected_archive_sha256=expected_archive_sha256,
        expected_member_count=expected_member_count,
    )

    reasons: list[str] = []
    reasons.extend(f"manifest: {reason}" for reason in manifest_result.get("reasons", []))
    reasons.extend(f"archive: {reason}" for reason in archive_result.get("reasons", []))

    referenced_hashes_verified = False
    if manifest_result.get("intake_complete") is True and archive_result.get("archive_integrity_verified") is True:
        digest_counts = archive_result.get("digest_counts", {})
        ref_errors = 0
        for va, field, digest in _declared_content_hashes(m):
            if not _valid_sha(digest):
                reasons.append(f"content reference invalid: {va} {field}")
                ref_errors += 1
                continue
            count = int(digest_counts.get(digest.lower(), 0))
            if count == 0:
                reasons.append(f"content reference missing from archive: {va} {field}")
                ref_errors += 1
            elif count > 1:
                reasons.append(f"content reference ambiguous in archive: {va} {field}")
                ref_errors += 1
        referenced_hashes_verified = ref_errors == 0

    complete = (
        manifest_result.get("intake_complete") is True
        and archive_result.get("archive_integrity_verified") is True
        and referenced_hashes_verified
        and not reasons
    )

    return {
        "status": (
            "PACKAGE_INTEGRITY_VERIFIED_STATIC_REVIEW_REQUIRED"
            if complete
            else "PACKAGE_INTEGRITY_REJECTED"
        ),
        "package_integrity_verified": complete,
        "manifest_intake_complete": manifest_result.get("intake_complete") is True,
        "archive_integrity_verified": archive_result.get("archive_integrity_verified") is True,
        "referenced_hashes_verified": referenced_hashes_verified,
        "archive_sha256": archive_result.get("archive_sha256"),
        "member_count": archive_result.get("member_count", 0),
        "total_uncompressed_bytes": archive_result.get("total_uncompressed_bytes", 0),
        "static_review_required": complete,
        "bridge_admitted": False,
        "proof_grade": False,
        "explicit_serializer_field_read": "UNRESOLVED",
        "controlled_fixture_to_consumer_match": "UNRESOLVED",
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "reasons": reasons,
    }
