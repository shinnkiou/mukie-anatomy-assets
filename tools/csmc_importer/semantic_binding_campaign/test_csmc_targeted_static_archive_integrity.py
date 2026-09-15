#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from csmc_targeted_static_archive_integrity import validate_targeted_static_package
from test_csmc_targeted_static_extraction_intake import valid_manifest


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _archive_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_valid_package(root: Path) -> tuple[dict, Path, int]:
    manifest = valid_manifest()
    archive = root / "targeted.zip"
    members: list[tuple[str, bytes]] = []

    for index, row in enumerate(manifest["functions"]):
        va = row["va"].replace("0x", "")
        decompile = f"synthetic decompile {index} {row['va']}\n".encode()
        listing = f"synthetic instruction listing {index} {row['va']}\n".encode()
        row["decompile_sha256"] = _sha(decompile)
        row["instruction_listing_sha256"] = _sha(listing)
        members.append((f"exports/{va}.decompile.txt", decompile))
        members.append((f"exports/{va}.instructions.txt", listing))

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, payload in members:
            zf.writestr(name, payload)
    return manifest, archive, len(members)


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest, archive, member_count = _build_valid_package(root)
        expected_sha = _archive_sha(archive)

        ok = validate_targeted_static_package(
            manifest,
            archive,
            expected_archive_sha256=expected_sha,
            expected_member_count=member_count,
        )
        assert ok["status"] == "PACKAGE_INTEGRITY_VERIFIED_STATIC_REVIEW_REQUIRED"
        assert ok["package_integrity_verified"] is True
        assert ok["archive_integrity_verified"] is True
        assert ok["referenced_hashes_verified"] is True
        assert ok["bridge_admitted"] is False
        assert ok["proof_grade"] is False
        assert ok["semantic_promotion"] is False
        assert ok["blender_emit"] is False
        assert ok["runtime_dispatch"] is False

        wrong_archive_sha = validate_targeted_static_package(
            manifest,
            archive,
            expected_archive_sha256="0" * 64,
            expected_member_count=member_count,
        )
        assert wrong_archive_sha["package_integrity_verified"] is False
        assert any("archive SHA-256 mismatch" in reason for reason in wrong_archive_sha["reasons"])

        missing_ref = deepcopy(manifest)
        missing_ref["functions"][0]["decompile_sha256"] = "f" * 64
        missing_ref_result = validate_targeted_static_package(
            missing_ref,
            archive,
            expected_archive_sha256=expected_sha,
            expected_member_count=member_count,
        )
        assert missing_ref_result["package_integrity_verified"] is False
        assert missing_ref_result["archive_integrity_verified"] is True
        assert missing_ref_result["referenced_hashes_verified"] is False

        wrong_count = validate_targeted_static_package(
            manifest,
            archive,
            expected_archive_sha256=expected_sha,
            expected_member_count=member_count + 1,
        )
        assert wrong_count["package_integrity_verified"] is False
        assert any("member count mismatch" in reason for reason in wrong_count["reasons"])

        traversal_archive = root / "traversal.zip"
        with zipfile.ZipFile(traversal_archive, "w") as zf:
            zf.writestr("../escape.txt", b"not extracted")
        traversal = validate_targeted_static_package(
            manifest,
            traversal_archive,
            expected_archive_sha256=_archive_sha(traversal_archive),
            expected_member_count=1,
        )
        assert traversal["archive_integrity_verified"] is False
        assert any("unsafe member path" in reason for reason in traversal["reasons"])

        pe_archive = root / "pe.zip"
        with zipfile.ZipFile(pe_archive, "w") as zf:
            zf.writestr("opaque.dat", b"MZ" + b"synthetic-not-real-pe")
        pe = validate_targeted_static_package(
            manifest,
            pe_archive,
            expected_archive_sha256=_archive_sha(pe_archive),
            expected_member_count=1,
        )
        assert pe["archive_integrity_verified"] is False
        assert any("PE-like member" in reason for reason in pe["reasons"])

    print(
        "TARGETED_STATIC_ARCHIVE_INTEGRITY_PASS cases=6 "
        "bridge_admitted=false proof_grade=false semantic_promotion=false"
    )


if __name__ == "__main__":
    run()
