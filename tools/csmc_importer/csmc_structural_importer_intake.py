#!/usr/bin/env python3
"""Fail-closed policy sidecar for the existing CSMC importer intake.

The established ``csmc_import_intake`` remains the parser-facing source of
truth. This module adds only mainline evidence-policy metadata: the validated
2456-byte / 307-qword structural cardinality candidate and the three MODELER
FIRST PASS supporting facts. It cannot promote field semantics or emit Blender
geometry.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "csmc_structural_importer_intake_v0_2"
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
    """Build a public-safe policy sidecar from validated structural facts."""
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
    """Wrap the established v0.4 importer intake with fail-closed policy metadata."""
    from csmc_import_intake import inspect_csmc as inspect_existing_intake

    intake = inspect_existing_intake(path)
    public = intake.to_public_dict()

    if public.get("pipeline_stage") != "STRUCTURAL_ONLY":
        raise StructuralIntakeError("existing importer intake left STRUCTURAL_ONLY mode")
    if public.get("semantic_promotion_count") != 0:
        raise StructuralIntakeError("existing importer intake promoted semantics")
    if public.get("blender_emit_ready") is not False:
        raise StructuralIntakeError("existing importer intake enabled Blender emit")

    envelope = {
        "align8_plus8_holds": bool(public["frame_rule_holds"]),
        "frame_rule": public["frame_rule"],
        "logical_length": public["logical_length"],
        "aligned_logical_length": public["aligned_logical_length"],
        "alignment_extension_length": public["alignment_extension_length"],
        "logical_mod8_phase": public["logical_mod8_phase"],
        "stored_length": public["stored_length"],
        "framing_remainder_length": public["framing_remainder_length"],
        "payload_offset": public["payload_offset"],
        "payload_size_available": public["payload_size_available"],
        "payload_sha256": public["payload_sha256"],
        "raw_payload_embedded": bool(public["raw_payload_embedded"]),
    }
    cadence = {
        "schema_version": public["cadence_detector_schema"],
        "detected": public["cadence_detected"],
        "lag_qwords": public["cadence_period_qwords"],
        "period_bytes": public["cadence_period_bytes"],
        "cluster_run_count": public["cadence_cluster_run_count"],
        "cadence_count_candidate": public["cadence_count_candidate"],
        "cluster_start_qword": public["cadence_cluster_start_qword"],
        "cluster_end_qword": public["cadence_cluster_end_qword"],
        "semantic_status": public["cadence_semantic_status"],
        "raw_values_embedded": False,
        "semantic_promotion": False,
    }

    return build_structural_intake(
        file_sha256=public["source_sha256"],
        route_table=public["sqlite_table"],
        route_column=public["blob_column"],
        outer_version=public["outer_version"],
        envelope=envelope,
        cadence=cadence,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Public-safe CSMC structural policy intake")
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
