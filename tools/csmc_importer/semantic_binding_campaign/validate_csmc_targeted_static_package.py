#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from csmc_targeted_static_archive_integrity import validate_targeted_static_package


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed package-integrity gate for a CSMC targeted static extraction ZIP."
    )
    parser.add_argument("manifest", type=Path, help="Path to the private targeted-extraction manifest JSON.")
    parser.add_argument("archive", type=Path, help="Path to the private targeted-extraction ZIP.")
    parser.add_argument(
        "--expected-archive-sha256",
        required=True,
        help="Expected SHA-256 for the exact ZIP bytes.",
    )
    parser.add_argument(
        "--expected-member-count",
        type=int,
        help="Optional exact number of non-directory ZIP members.",
    )
    parser.add_argument("--report", type=Path, help="Optional path for the public-safe gate report JSON.")
    args = parser.parse_args()

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except Exception as exc:
        result = {
            "status": "PACKAGE_INTEGRITY_REJECTED",
            "package_integrity_verified": False,
            "manifest_intake_complete": False,
            "archive_integrity_verified": False,
            "referenced_hashes_verified": False,
            "static_review_required": False,
            "bridge_admitted": False,
            "proof_grade": False,
            "explicit_serializer_field_read": "UNRESOLVED",
            "controlled_fixture_to_consumer_match": "UNRESOLVED",
            "semantic_promotion": False,
            "blender_emit": False,
            "runtime_dispatch": False,
            "reasons": [f"manifest read/JSON error: {exc}"],
        }
    else:
        result = validate_targeted_static_package(
            manifest,
            args.archive,
            expected_archive_sha256=args.expected_archive_sha256,
            expected_member_count=args.expected_member_count,
        )

    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    return 0 if result.get("package_integrity_verified") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
