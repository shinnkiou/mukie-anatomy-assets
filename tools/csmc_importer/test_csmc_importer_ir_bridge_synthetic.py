#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy

from csmc_importer_ir_bridge import ImporterIRBridgeError, build_bridge
from csmc_structural_ir import SCHEMA_VERSION as IR_SCHEMA

CSMC_SHA = "b" * 64
CLIP_SHA = "a" * 64


def intake():
    return {
        "schema_version": "csmc_structural_importer_intake_v0_2",
        "mode": "STRUCTURAL_ONLY",
        "source": {"file_sha256": CSMC_SHA},
        "accepted_structural_candidates": [
            {
                "evidence_id": "TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE",
                "confidence_level": 4,
                "semantic_projection": False,
                "blender_emit_ready": False,
            }
        ],
        "consumer_side_evidence": {
            "EXPLICIT_PARENT_LENGTH_FIELD": {"status": "CONFIRMED", "role": "SUPPORTING_ONLY"},
            "EXPLICIT_PARENT_RECORD_BOUNDARY": {"status": "CONFIRMED", "role": "SUPPORTING_ONLY"},
            "EXPLICIT_CONSUMER_CROSSREF": {"status": "CONFIRMED", "role": "SUPPORTING_ONLY"},
        },
        "controlled_fixture_to_consumer_match": "UNRESOLVED",
        "semantic_promotion_count": 0,
        "semantic_projection": False,
        "runtime_dispatch": False,
        "blender_emit_ready": False,
    }


def structural_ir():
    return {
        "schema_version": IR_SCHEMA,
        "source": {"clip_sha256": CLIP_SHA, "csmc_sha256": CSMC_SHA, "raw_bytes_embedded": False},
        "ir_axes": ["length_blocks", "preserve_signature", "boundary_class"],
        "boundaries": [
            {
                "id": "BND_197_TO_195",
                "class": "local_extinction",
                "from_delta_blocks": 197,
                "to_delta_blocks": 195,
                "net_relative_size_bytes": -16,
                "barrier_matches_old_delta": 0,
                "barrier_matches_new_delta": 0,
                "complete_cross_serialization_extinction": True,
                "semantic_owner": "unresolved",
            }
        ],
        "record_families": [
            {"length_blocks": 48, "preserve_signature": "0000110", "count": 7, "semantic_record_type": "unresolved"},
            {"length_blocks": 48, "preserve_signature": "0000111", "count": 3, "semantic_record_type": "unresolved"},
            {"length_blocks": 48, "preserve_signature": "0001110", "count": 3, "semantic_record_type": "unresolved"},
            {"length_blocks": 49, "preserve_signature": "0000111", "count": 3, "semantic_record_type": "unresolved"},
            {"length_blocks": 49, "preserve_signature": "1000111", "count": 6, "semantic_record_type": "unresolved"},
        ],
        "semantic_claims": {
            "geometry": "unresolved",
            "index_buffer": "unresolved",
            "uv": "unresolved",
            "material": "unresolved",
            "texture": "unresolved",
            "bone_hierarchy": "unresolved",
            "bind_pose": "unresolved",
            "bone_indices": "unresolved",
            "skin_weights": "unresolved",
        },
        "guardrails": {
            "public_safe": True,
            "aggregate_only": True,
            "contains_raw_payload": False,
            "contains_literal_qwords": False,
            "blender_import_proven": False,
        },
    }


def expect_fail(i, ir):
    try:
        build_bridge(intake=i, structural_ir=ir)
    except ImporterIRBridgeError:
        return
    raise AssertionError("bridge must fail closed")


def main():
    out = build_bridge(intake=intake(), structural_ir=structural_ir())
    assert out["mode"] == "STRUCTURAL_ONLY"
    assert out["guardrails"]["structural_ir_validated"] is True
    assert out["guardrails"]["source_sha_matched"] is True
    assert out["guardrails"]["boundary_inference_from_cadence"] is False
    assert out["semantic_promotion_count"] == 0
    assert out["semantic_projection"] is False
    assert out["runtime_dispatch"] is False
    assert out["blender_emit_ready"] is False
    assert all(v == "unresolved" for v in out["semantic_claims"].values())

    bad = deepcopy(intake())
    bad["source"]["file_sha256"] = "c" * 64
    expect_fail(bad, structural_ir())

    bad = deepcopy(intake())
    bad["semantic_promotion_count"] = 1
    expect_fail(bad, structural_ir())

    bad_ir = deepcopy(structural_ir())
    bad_ir["semantic_claims"]["geometry"] = "mesh"
    expect_fail(intake(), bad_ir)

    bad = deepcopy(intake())
    bad["accepted_structural_candidates"].append({"evidence_id": "UNVALIDATED_FIELD_SEMANTIC"})
    expect_fail(bad, structural_ir())

    print("CSMC importer IR bridge synthetic tests PASS")


if __name__ == "__main__":
    main()
