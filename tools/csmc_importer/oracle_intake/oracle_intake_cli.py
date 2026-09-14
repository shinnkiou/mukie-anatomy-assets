#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from completion_gate import validate_physical_completion_gate
from oracle_intake import (
    OracleIntakeRejected,
    SOURCE_MANIFEST_SHA256,
    canonical_sha256,
    public_safe_projection,
    validate_oracle_observation,
)


def read_json_with_raw_sha256(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        # utf-8-sig accepts a BOM without normalizing the bytes used for SHA binding.
        value = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise OracleIntakeRejected(f"invalid JSON: {path}: {exc}") from exc
    return value, digest


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fail-closed intake for read-only F02 MODELER mutation-oracle observations."
    )
    ap.add_argument("source_manifest", type=Path)
    ap.add_argument("observation", type=Path)
    ap.add_argument("--partial", action="store_true", help="allow fewer than 30 observations")
    ap.add_argument("--public-out", type=Path, default=None)
    ap.add_argument("--receipt-out", type=Path, default=None)
    args = ap.parse_args()

    source_manifest, computed_source_sha = read_json_with_raw_sha256(args.source_manifest)
    if computed_source_sha != SOURCE_MANIFEST_SHA256:
        raise OracleIntakeRejected(
            f"source manifest raw SHA256 mismatch: expected {SOURCE_MANIFEST_SHA256}, got {computed_source_sha}"
        )

    observation, observation_sha = read_json_with_raw_sha256(args.observation)
    require_complete = not args.partial
    result = validate_oracle_observation(
        source_manifest,
        computed_source_sha,
        observation,
        require_complete=require_complete,
    )
    completion_gate = validate_physical_completion_gate(
        observation,
        result,
        require_complete=require_complete,
    )

    projection = public_safe_projection(observation)
    projection_sha = canonical_sha256(projection)
    receipt = {
        "schema_version": "csmc_f02_mutation_oracle_intake_receipt_v2",
        "source_manifest_raw_sha256": computed_source_sha,
        "observation_raw_sha256": observation_sha,
        "public_projection_canonical_sha256": projection_sha,
        "validation": result,
        "physical_completion_gate": completion_gate,
        "semantic_promotion": False,
        "blender_emit": False,
        "diagnostic_only": True,
    }

    if args.public_out is not None:
        args.public_out.write_text(
            json.dumps(projection, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if args.receipt_out is not None:
        args.receipt_out.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
