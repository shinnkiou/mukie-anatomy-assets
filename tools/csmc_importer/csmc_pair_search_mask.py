#!/usr/bin/env python3
"""Build public-safe structural search masks from validated pair invariant evidence.

The mask excludes only the exact invariant interval proven for a pair and keeps
the variable prefix plus terminal remainder as candidate regions. It carries no
raw qword values and cannot authorize semantic promotion or Blender emission.
"""
from __future__ import annotations

from csmc_pair_invariant_evidence import PairInvariantEvidence, validate_pair_invariant

SCHEMA_VERSION = "csmc_pair_search_mask_v0_1"


def _fixture_mask(qword_count: int, start: int, length: int) -> dict:
    end = start + length
    include = []
    if start > 0:
        include.append([0, start])
    if end < qword_count:
        include.append([end, qword_count])
    return {
        "qword_count": qword_count,
        "include_candidate_regions_qwords": include,
        "exclude_exact_invariant_region_qwords": [start, end],
    }


def build_search_mask(evidence: PairInvariantEvidence) -> dict:
    errors = validate_pair_invariant(evidence)
    if errors:
        raise ValueError("invalid pair invariant evidence: " + "; ".join(errors))
    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_id": evidence.evidence_id,
        "fixture_a": evidence.fixture_a,
        "fixture_b": evidence.fixture_b,
        "logical_mod8_phase": evidence.logical_mod8_a,
        "relationship_type": "PHASE_NORMALIZED_SEARCH_MASK",
        "fixture_a_mask": _fixture_mask(
            evidence.qword_count_a,
            evidence.invariant_start_a,
            evidence.invariant_length_qwords,
        ),
        "fixture_b_mask": _fixture_mask(
            evidence.qword_count_b,
            evidence.invariant_start_b,
            evidence.invariant_length_qwords,
        ),
        "candidate_semantic": "STRUCTURAL_ONLY",
        "semantic_promotion": False,
        "raw_values_embedded": False,
        "blender_emit_ready": False,
    }
