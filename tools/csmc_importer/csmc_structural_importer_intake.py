#!/usr/bin/env python3
"""Fail-closed structural intake for the CSMC importer mainline.

This composes the already-validated outer-envelope parser and public-safe
307-qword cadence detector into one importer-facing sidecar. It deliberately
stops before field semantics: geometry/index/UV/material/bone/weight remain
unresolved and Blender emission stays disabled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "csmc_structural_importer_intake_v0_1"
CADENCE_CANDIDATE_ID = "TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE"
CADENCE_LAG_QWORDS = 307
CADENCE_PERIOD_BYTES = 2456

CONFIRMED_CONSUMER_EVIDENCE = (
    "EXPLICIT_PARENT_LENGTH_FIELD",
    "EXPLICIT_PARENT_RECORD_BOUNDARY",
    "EXPLICIT_CONSUMER_CROSSREF",
)

SEMANTIC_DOMAINS = (
    "geometry",
    "index_topology",
    "uv",
    "material",
    "bone",
    "weight",
)


class StructuralIntakeError(ValueError):
    pass


def _copy_public_map(value: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(dict(value)))


def _validate_sha256(value: str) -> None:
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise StructuralIntakeError("file_sha256 must be 64 hexadecimal characters")


def build_structural_intake(
    *,
    file_sha256: str,
    route_table: str,
    route_column: str,
    outer_version: int,
    envelope: Mapping[str, Any],
    cadence: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a public-safe importer sidecar from already-parsed structural facts."""
    _validate_sha256(file_sha256)
    env = _copy_public_map(envelope)
    cad = _copy_public_map(cadence)

    if env.get("align8_plus8_holds") is not True:
        raise StructuralIntakeError("validated outer frame invariant does not hold")
    if env.get("raw_payload_embedded") not in (False, None):
        raise StructuralIntakeError("raw payload embedding is not admissible")
    if cad.get("raw_values_embedded") not in (False, None):
        raise StructuralIntakeError("raw cadence values are not admissible")
    if cad.get("semantic_promotion") not in (False, None):
        raise StructuralIntakeError("cadence detector attempted semantic promotion")

    cadence_matches_candidate = (
        cad.get("detected") is True
        and cad.get("lag_qwords") == CADENCE_LAG_QWORDS
        and cad.get("period_bytes") == CADENCE_PERIOD_BYTES
        and isinstance(cad.get("cadence_count_candidate"), int)
        and cad.get("cadence_count_candidate") > 0
    )

    accepted_structural_candidates: list[dict[str, Any]] = []
    if cadence_matches_candidate:
        accepted_structural_candidates.append(
            {
                "evidence_id": CADENCE_CANDIDATE_ID,
                "confidence_level": 4,
                "classification": "STRUCTURAL_CARDINALITY_CANDIDATE",
                "basis": {
                    "lag_qwords": CADENCE_LAG_QWORDS,
                    "period_bytes": CADENCE_PERIOD_BYTES,
                    "cadence_count_candidate": cad["cadence_count_candidate"],
                },
                "semantic_projection": False,
                "field_semantics_identified": False,
                "blender_emit_ready": False,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "STRUCTURAL_ONLY",
        "source": {
            "file_sha256": file_sha256.lower(),
            "route": {
                "table": route_table,
                "column": route_column,
                "outer_version": int(outer_version),
            },
        },
        "container_frame": env,
        "cadence": cad,
        "accepted_structural_candidates": accepted_structural_candidates,
        "consumer_side_evidence": {
            evidence_id: {
                "status": "CONFIRMED",
                "role": "SUPPORTING_ONLY",
                "semantic_promotion": False,
            }
            for evidence_id in CONFIRMED_CONSUMER_EVIDENCE
        },
        "controlled_fixture_to_consumer_match": "UNRESOLVED",
        "semantic_claims": {name: "unresolved" for name in SEMANTIC_DOMAINS},
        "semantic_promotions": [],
        "semantic_promotion_count": 0,
        "automatic_semantic_promotion": False,
        "semantic_projection": False,
        "runtime_dispatch": False,
        "blender_emit_ready": False,
        "raw_payload_values_embedded": False,
        "second_pass_consumer_analysis_required": False,
        "mainline_next_action": (
            "continue known-file-only structural parser/importer integration; "
            "require independent direct evidence before any field-semantic promotion"
        ),
    }


def inspect_csmc(path: str | Path) -> dict[str, Any]:
    """Inspect one authorized CSMC using existing mainline structural parsers."""
    from csmc_core import extract_character_blob
    from csmc_controlled_envelope import parse_character_blob
    from csmc_cadence_structural_detector import detect_cadence_qwords, split_qwords

    p = Path(path)
    file_bytes = p.read_bytes()
    file_sha256 = hashlib.sha256(file_bytes).hexdigest()
    blob, table, column, outer_version = extract_character_blob(p)
    if outer_version is None:
        raise StructuralIntakeError("outer version is missing")

    env = parse_character_blob(
        blob,
        file_sha256=file_sha256,
        outer_version=int(outer_version),
    )
    payload = blob[env.payload_offset : env.payload_offset + env.stored_length]
    if len(payload) % 8:
        raise StructuralIntakeError("stored payload is not qword aligned")

    cadence = detect_cadence_qwords(split_qwords(payload))
    return build_structural_intake(
        file_sha256=file_sha256,
        route_table=table,
        route_column=column,
        outer_version=int(outer_version),
        envelope=env.to_public_dict(),
        cadence=cadence.to_public_dict(),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Public-safe CSMC structural importer intake")
    ap.add_argument("path", help="authorized .csmc file")
    ap.add_argument("--json-out", help="optional output sidecar path")
    args = ap.parse_args()

    result = inspect_csmc(args.path)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
