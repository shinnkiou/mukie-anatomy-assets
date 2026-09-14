#!/usr/bin/env python3
"""Fail-closed semantic sidecar for the controlled 307-qword cadence result.

This module can raise the *candidate confidence* of the render-part cardinality
relationship to Level 4 when the published controlled-corpus checks all hold.
It can never confirm the semantic binding or authorize Blender emission.
"""
from __future__ import annotations

from csmc_controlled_evidence_ir import ControlledEvidence, validate_evidence

CANDIDATE_SEMANTIC = "TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE"
CORPUS_SHA256 = "be6132ef83959167ffd19218810e099f0bd164714fbd1ec4770f9296b38643b6"
FIXTURES = (
    "CSMC_F01_TRIANGLE", "CSMC_F02_QUAD", "CSMC_F03_CUBE",
    "CSMC_F04_CUBE_SUBDIV", "CSMC_F05_CUBE_UV", "CSMC_F06_CUBE_MAT2",
    "CSMC_F07_TWO_CUBES", "CSMC_R01_CUBE_B1_W0", "CSMC_R02_CUBE_B1_W100",
    "CSMC_R03_CUBE_B2_W100", "CSMC_R04_CUBE_B2_SPLIT",
    "CSMC_R05_CUBE_B2_MIX50", "CSMC_V01_VROID_BODY_BASE",
)


def build_level4_candidate(
    *,
    relationship_holds_count: int,
    full_match_lags: tuple[int, ...],
    robustness_pass_count: int,
    robustness_total_count: int,
) -> ControlledEvidence:
    if relationship_holds_count != 13:
        raise ValueError("render-part cadence relationship must hold for all 13 fixtures")
    if full_match_lags != (307,):
        raise ValueError("bounded lag negative control must uniquely select 307 qwords")
    if robustness_total_count <= 0 or robustness_pass_count != robustness_total_count:
        raise ValueError("detector parameter robustness grid did not fully pass")

    evidence = ControlledEvidence(
        evidence_id="CONTROLLED_TAIL_2456_RENDER_PART_LEVEL4_20260914",
        evidence_source="C050_REFERENCE_PLUS_PUBLIC_SAFE_AUTOCORRELATION",
        controlled_fixture_ids=FIXTURES,
        relationship_type="CADENCE_COUNT_EQUALS_TWO_PLUS_RENDER_PART_COUNT",
        negative_control_ids=(
            "GEOMETRY_COMPLEXITY_NEGATIVE_CONTROL",
            "UV_EDIT_NEGATIVE_CONTROL",
            "RIG_WEIGHT_NEGATIVE_CONTROL",
            "BOUNDED_LAG_280_330_NEGATIVE_SWEEP",
        ),
        independent_validation_ids=("CSMC_V01_VROID_BODY_BASE",),
        supporting_relationship_ids=(
            "F01_F05_SINGLE_RENDER_PART_FAMILY",
            "F03_F06_MATERIAL_POSITIVE_CONTROL",
            "F03_F07_OBJECT_POSITIVE_CONTROL",
            "R01_R05_RIG_WEIGHT_NEGATIVE_FAMILY",
            "V01_VROID_INDEPENDENT_CONSISTENCY",
        ),
        candidate_semantic=CANDIDATE_SEMANTIC,
        confidence_level=4,
        validation_status="I3_PARTIAL",
        source_sha256=(CORPUS_SHA256,),
        counterexample_count=0,
        semantic_promotion=False,
    )
    errors = validate_evidence(evidence)
    if errors:
        raise ValueError("controlled evidence rejected: " + "; ".join(errors))
    return evidence


def semantic_gate_summary(evidence: ControlledEvidence) -> dict:
    if evidence.candidate_semantic != CANDIDATE_SEMANTIC:
        raise ValueError("unexpected candidate semantic")
    if evidence.confidence_level > 4:
        raise ValueError("this controlled result cannot exceed Level 4")
    if evidence.semantic_promotion:
        raise ValueError("render-part cadence remains candidate-only")
    return {
        "candidate_semantic": evidence.candidate_semantic,
        "confidence_level": evidence.confidence_level,
        "validation_status": evidence.validation_status,
        "semantic_status": "CANDIDATE_ONLY",
        "confirmed": False,
        "semantic_promotion": False,
        "blender_emit_ready": False,
    }
