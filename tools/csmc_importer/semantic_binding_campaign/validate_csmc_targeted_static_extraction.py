#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from csmc_targeted_static_extraction_intake import validate_targeted_static_manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed intake validator for the CSMC targeted static extraction manifest."
    )
    parser.add_argument("manifest", type=Path, help="Path to private manifest JSON (not the proprietary archive bytes).")
    parser.add_argument("--report", type=Path, help="Optional path to write the public-safe validation report JSON.")
    args = parser.parse_args()

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except Exception as exc:
        result = {
            "status": "INTAKE_REJECTED",
            "intake_complete": False,
            "static_review_required": False,
            "bridge_admitted": False,
            "proof_grade": False,
            "semantic_promotion": False,
            "blender_emit": False,
            "runtime_dispatch": False,
            "reasons": [f"manifest read/JSON error: {exc}"],
        }
    else:
        result = validate_targeted_static_manifest(manifest)

    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.report:
        args.report.write_text(text, encoding="utf-8")

    return 0 if result.get("intake_complete") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
