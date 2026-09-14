#!/usr/bin/env python3
"""Fail-closed reconciliation validator for Companion C run C-064.

This module validates only public-safe structural aggregates from the mainline
render-part residual localization follow-up. It cannot promote a CSMC field
semantic and it never reads private fixture bytes.
"""

EXPECTED_STARTS = {"F03": 442, "F06": 453, "F07": 465}
EXPECTED_PRE_SHIFTS = {"F06_minus_F03_bytes": 88, "F07_minus_F03_bytes": 184, "F07_minus_F06_bytes": 96}
EXPECTED_LOGICAL_DELTAS = {"F06_minus_F03": 2555, "F07_minus_F03": 2651, "F07_minus_F06": 96}


def validate(record: dict) -> list[str]:
    errors: list[str] = []

    if record.get("pipeline_stage") != "STRUCTURAL_ONLY":
        errors.append("pipeline_stage must remain STRUCTURAL_ONLY")
    if record.get("semantic_promotion_count") != 0:
        errors.append("semantic promotion is forbidden")
    if record.get("blender_emit_ready") is not False:
        errors.append("Blender emit must remain blocked")
    if record.get("runtime_dispatch") is not False:
        errors.append("runtime dispatch must remain false")
    if record.get("raw_private_bytes_published") is not False:
        errors.append("raw/private bytes publication is forbidden")

    if record.get("candidate") != "TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE":
        errors.append("candidate identity changed")
    if record.get("confidence_before") != "LEVEL_4_CANDIDATE":
        errors.append("unexpected confidence_before")
    if record.get("confidence_after") != "LEVEL_4_CANDIDATE_REFINED_NOT_PROMOTED":
        errors.append("candidate must remain Level 4 and unpromoted")

    common = record.get("triple_common", {})
    if common.get("length_qwords") != 924 or common.get("length_bytes") != 7392:
        errors.append("triple-common extent mismatch")
    if common.get("length_qwords", -1) * 8 != common.get("length_bytes"):
        errors.append("qword/byte extent arithmetic mismatch")
    if common.get("start_qwords") != EXPECTED_STARTS:
        errors.append("triple-common start offsets mismatch")
    if common.get("v01_occurrence_qword") != 531781:
        errors.append("V01 recurrence offset mismatch")

    shifts = record.get("pre_common_shifts", {})
    if shifts != EXPECTED_PRE_SHIFTS:
        errors.append("pre-common shift decomposition mismatch")
    else:
        if (EXPECTED_STARTS["F06"] - EXPECTED_STARTS["F03"]) * 8 != shifts["F06_minus_F03_bytes"]:
            errors.append("F06 start-shift arithmetic mismatch")
        if (EXPECTED_STARTS["F07"] - EXPECTED_STARTS["F03"]) * 8 != shifts["F07_minus_F03_bytes"]:
            errors.append("F07 start-shift arithmetic mismatch")
        if (EXPECTED_STARTS["F07"] - EXPECTED_STARTS["F06"]) * 8 != shifts["F07_minus_F06_bytes"]:
            errors.append("F07/F06 start-shift arithmetic mismatch")

    if record.get("logical_length_deltas") != EXPECTED_LOGICAL_DELTAS:
        errors.append("logical-length deltas mismatch")

    post = record.get("post_common_growth", {})
    if post.get("F06_minus_F03_bytes") != 2467 or post.get("F07_minus_F03_bytes") != 2467:
        errors.append("post-common growth mismatch")
    if record.get("cadence_bytes") != 2456 or record.get("other_bytes") != 11:
        errors.append("2456+11 decomposition mismatch")
    if record.get("cadence_bytes", 0) + record.get("other_bytes", 0) != 2467:
        errors.append("cadence decomposition arithmetic mismatch")

    neg = record.get("boundary_scalar_negative_control", {})
    if neg.get("window_bytes") != 2048:
        errors.append("negative-control window mismatch")
    if neg.get("candidate_configurations_evaluated") != 40928:
        errors.append("negative-control candidate count mismatch")
    if neg.get("hard_pass_count") != 0:
        errors.append("direct boundary-relative scalar family was not rejected")
    if neg.get("rejection_scope") != "DIRECT_RAW_SHARED_BOUNDARY_RELATIVE_SCALAR_ONLY":
        errors.append("negative-control scope must remain narrow")

    unresolved = record.get("semantic_state", {})
    required_unresolved = {
        "geometry": "UNRESOLVED",
        "index_topology": "UNRESOLVED",
        "serializer_field_read": "UNRESOLVED",
        "controlled_fixture_to_consumer_match": "UNRESOLVED",
    }
    for key, expected in required_unresolved.items():
        if unresolved.get(key) != expected:
            errors.append(f"{key} must remain {expected}")

    return errors


def assert_valid(record: dict) -> None:
    errors = validate(record)
    if errors:
        raise ValueError("; ".join(errors))
