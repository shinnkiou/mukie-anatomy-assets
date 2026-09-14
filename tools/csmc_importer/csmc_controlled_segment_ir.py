#!/usr/bin/env python3
"""Public-safe structural segment IR derived from validated pair invariants.

This sidecar turns an already-validated pair invariant into three qword ranges
per fixture:
- variable prefix candidate region
- exact invariant core
- terminal remainder candidate region

It never embeds payload values and cannot promote geometry/material/rig
semantics or authorize Blender emission.
"""
from __future__ import annotations

from csmc_pair_invariant_evidence import PairInvariantEvidence, validate_pair_invariant

SCHEMA_VERSION = "csmc_controlled_segment_ir_v0_1"


def _fixture_segments(qword_count: int, invariant_start: int, invariant_length: int) -> dict:
    invariant_end = invariant_start + invariant_length
    return {
        "qword_count": qword_count,
        "segments": [
            {
                "segment_id": "variable_prefix",
                "class": "VARIABLE_PREFIX_CANDIDATE_REGION",
                "range_qwords": [0, invariant_start],
                "length_qwords": invariant_start,
                "search_candidate": True,
            },
            {
                "segment_id": "exact_invariant_core",
                "class": "EXACT_INVARIANT_CORE",
                "range_qwords": [invariant_start, invariant_end],
                "length_qwords": invariant_length,
                "search_candidate": False,
            },
            {
                "segment_id": "terminal_remainder",
                "class": "TERMINAL_REMAINDER_CANDIDATE_REGION",
                "range_qwords": [invariant_end, qword_count],
                "length_qwords": qword_count - invariant_end,
                "search_candidate": True,
            },
        ],
    }


def build_segment_ir(evidence: PairInvariantEvidence) -> dict:
    errors = validate_pair_invariant(evidence)
    if errors:
        raise ValueError("invalid pair invariant evidence: " + "; ".join(errors))

    a = _fixture_segments(
        evidence.qword_count_a,
        evidence.invariant_start_a,
        evidence.invariant_length_qwords,
    )
    b = _fixture_segments(
        evidence.qword_count_b,
        evidence.invariant_start_b,
        evidence.invariant_length_qwords,
    )
    if a["segments"][2]["length_qwords"] != evidence.trailing_qwords_a:
        raise ValueError("fixture A terminal remainder disagrees with evidence")
    if b["segments"][2]["length_qwords"] != evidence.trailing_qwords_b:
        raise ValueError("fixture B terminal remainder disagrees with evidence")

    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_id": evidence.evidence_id,
        "relationship_type": "PHASE_NORMALIZED_STRUCTURAL_SEGMENTATION",
        "logical_mod8_phase": evidence.logical_mod8_a,
        "pair": {
            "fixture_a": evidence.fixture_a,
            "fixture_b": evidence.fixture_b,
        },
        "fixture_a": a,
        "fixture_b": b,
        "semantic_claims": {
            "geometry": "unresolved",
            "index_topology": "unresolved",
            "uv": "unresolved",
            "material": "unresolved",
            "bone": "unresolved",
            "weight": "unresolved",
        },
        "structural_validation": "VALIDATED_PAIR_INVARIANT",
        "semantic_confidence_level": 0,
        "semantic_promotion": False,
        "raw_values_embedded": False,
        "blender_emit_ready": False,
    }
