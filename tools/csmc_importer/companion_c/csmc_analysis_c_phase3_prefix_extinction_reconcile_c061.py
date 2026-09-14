#!/usr/bin/env python3
"""C-061: reference-only reconciliation of phase-3 VRoid holdout and prefix exact-qword negative control."""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Mapping

PIPELINE_STAGE = "STRUCTURAL_ONLY"
CLASSIFICATION = "PHASE3_HOLDOUT_PREFIX_EXACT_QWORD_NEGATIVE_CONTROL_RECONCILED"

BASELINE = {
    "source_mainline_prefix_head": "7ab466ac495cbb09792fad20f0d30e2bb4ed551a",
    "source_mainline_framing_head": "c591741eabacfaf3d983328b8065dfab9b53a675",
    "source_supabase_prefix_row": 152,
    "source_supabase_framing_row": 153,
    "source_drive_prefix_findings_id": "13LN932sx-a4OUm8gfqcVEAppCzWt-7bE",
    "source_drive_prefix_aggregate_id": "1N6bRQIswV6d6EeVrgAKs8LfQmTfPGxeh",
    "pair_count": 7,
    "holdout_pair": "R04_V01",
    "holdout_logical_mod8": 3,
    "holdout_invariant_length_qwords": 1800,
    "holdout_start_r04_qword": 480,
    "holdout_start_v01_qword": 533940,
    "holdout_trailing_qwords_each": 2,
    "prefix_exact_qword_overlap_zero_pairs": 7,
    "prefix_multiset_qword_overlap_zero_pairs": 7,
    "frame_rule": "stored_length = align8(logical_length) + 8",
    "framing_remainder_length": 8,
    "alignment_extension_semantic": "UNRESOLVED",
    "framing_remainder_semantic": "UNRESOLVED",
    "pipeline_stage": PIPELINE_STAGE,
    "semantic_promotion_count": 0,
    "blender_emit_ready": False,
    "runtime_dispatch": False,
    "raw_private_bytes_published": False,
}

EXPECTED = {
    "source_mainline_prefix_head": "7ab466ac495cbb09792fad20f0d30e2bb4ed551a",
    "source_mainline_framing_head": "c591741eabacfaf3d983328b8065dfab9b53a675",
    "source_supabase_prefix_row": 152,
    "source_supabase_framing_row": 153,
    "pair_count": 7,
    "holdout_pair": "R04_V01",
    "holdout_logical_mod8": 3,
    "holdout_invariant_length_qwords": 1800,
    "holdout_start_r04_qword": 480,
    "holdout_start_v01_qword": 533940,
    "holdout_trailing_qwords_each": 2,
    "prefix_exact_qword_overlap_zero_pairs": 7,
    "prefix_multiset_qword_overlap_zero_pairs": 7,
    "frame_rule": "stored_length = align8(logical_length) + 8",
    "framing_remainder_length": 8,
    "alignment_extension_semantic": "UNRESOLVED",
    "framing_remainder_semantic": "UNRESOLVED",
    "pipeline_stage": PIPELINE_STAGE,
    "semantic_promotion_count": 0,
    "blender_emit_ready": False,
    "runtime_dispatch": False,
    "raw_private_bytes_published": False,
}

def evaluate(row: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"accepted": False, "errors": ["input_not_mapping"], "classification": "REJECTED"}
    errors: list[str] = []
    for key, expected in EXPECTED.items():
        if row.get(key) != expected or type(row.get(key)) is not type(expected):
            errors.append(f"{key}_mismatch")
    for key in ("source_drive_prefix_findings_id", "source_drive_prefix_aggregate_id"):
        if not isinstance(row.get(key), str) or not row.get(key):
            errors.append(f"{key}_missing")
    if errors:
        return {"accepted": False, "errors": errors, "classification": "REJECTED"}
    return {
        "accepted": True,
        "errors": [],
        "classification": CLASSIFICATION,
        "source_pair_count": 7,
        "holdout_supported": True,
        "holdout_is_same_identity_semantic_control": False,
        "exact_qword_reuse_status": "NOT_PRODUCTIVE_FOR_TESTED_BOUNDED_PREFIXES",
        "search_mask_policy": {
            "exclude": "VALIDATED_INVARIANT_CORE",
            "include": ["VARIABLE_PREFIX", "TERMINAL_REMAINDER"],
            "next_probe_family": "PREREGISTERED_BOUNDED_SIZE_STRIDE_COUNT_RELATIONSHIPS",
        },
        "framing": {
            "frame_rule": EXPECTED["frame_rule"],
            "framing_remainder_length": 8,
            "alignment_extension_semantic": "UNRESOLVED",
            "framing_remainder_semantic": "UNRESOLVED",
        },
        "semantic_binding": "UNRESOLVED",
        "i3_valid": False,
        "pipeline_stage": PIPELINE_STAGE,
        "semantic_promotion_count": 0,
        "blender_emit_ready": False,
        "runtime_dispatch": False,
        "raw_private_bytes_published": False,
    }

def self_test() -> None:
    out = evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["classification"] == CLASSIFICATION
    assert out["exact_qword_reuse_status"] == "NOT_PRODUCTIVE_FOR_TESTED_BOUNDED_PREFIXES"
    assert out["holdout_is_same_identity_semantic_control"] is False
    cases = []
    for key, value in (
        ("pair_count", 6),
        ("holdout_logical_mod8", 4),
        ("holdout_invariant_length_qwords", 1799),
        ("prefix_exact_qword_overlap_zero_pairs", 6),
        ("framing_remainder_length", 7),
        ("alignment_extension_semantic", "PADDING"),
        ("semantic_promotion_count", 1),
        ("blender_emit_ready", True),
        ("runtime_dispatch", True),
    ):
        bad = deepcopy(BASELINE)
        bad[key] = value
        cases.append(bad)
    for bad in cases:
        assert evaluate(bad)["accepted"] is False
    assert 1 + len(cases) == 10
    print("C061_SELF_TEST_PASS 10/10")

if __name__ == "__main__":
    self_test()
