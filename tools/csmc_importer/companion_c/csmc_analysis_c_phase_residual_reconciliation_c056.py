#!/usr/bin/env python3
"""C-056: reconcile C-050 cadence residuals with the newer mainline phase-class aggregate.

Public-safe aggregate metadata only. No raw CSMC bytes are embedded or acquired.
The result localizes one controlled differential structurally; it does not bind
material/object semantics and cannot promote Blender emission.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Mapping

PIPELINE_STAGE = "STRUCTURAL_ONLY"
SEMANTIC_PROMOTION_COUNT = 0
BLENDER_EMIT_READY = False
RUNTIME_DISPATCH = False
CLASSIFICATION = "PHASE_LOCALIZED_RESIDUAL_DIFFERENTIAL_CANDIDATE"

BASELINE = {
    "schema_version": "csmc_analysis_c_phase_residual_reconciliation_c056_v1",
    "pipeline_stage": PIPELINE_STAGE,
    "semantic_promotion_count": 0,
    "blender_emit_ready": False,
    "runtime_dispatch": False,
    "raw_private_bytes_published": False,
    "c050": {
        "cadence_qwords": 307,
        "f03_to_f06_total_delta_qwords": 320,
        "f03_to_f07_total_delta_qwords": 332,
    },
    "phase_pair": {
        "fixture_a": "CSMC_F06_CUBE_MAT2",
        "fixture_b": "CSMC_F07_TWO_CUBES",
        "same_logical_mod8": True,
        "logical_mod8_a": 1,
        "logical_mod8_b": 1,
        "qword_count_a": 2564,
        "qword_count_b": 2576,
        "longest_run_start_a": 445,
        "longest_run_start_b": 457,
        "longest_run_qwords": 2118,
        "trailing_qwords_after_longest_a": 1,
        "trailing_qwords_after_longest_b": 1,
        "total_matching_qwords": 2118,
    },
}


def _int(row: Mapping[str, Any], key: str) -> int:
    value = row[key]
    if type(value) is not int:
        raise TypeError(key)
    return value


def reconcile(row: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(row, Mapping):
        return {"accepted": False, "errors": ["input_not_mapping"], "classification": "REJECTED"}

    if row.get("pipeline_stage") != PIPELINE_STAGE:
        errors.append("pipeline_not_structural_only")
    if row.get("semantic_promotion_count") != 0:
        errors.append("semantic_promotion_must_be_zero")
    if row.get("blender_emit_ready") is not False:
        errors.append("blender_emit_must_remain_blocked")
    if row.get("runtime_dispatch") is not False:
        errors.append("runtime_dispatch_must_remain_false")
    if row.get("raw_private_bytes_published") is not False:
        errors.append("raw_private_bytes_must_not_be_public")

    c050 = row.get("c050")
    phase = row.get("phase_pair")
    if not isinstance(c050, Mapping) or not isinstance(phase, Mapping):
        errors.append("missing_aggregate_sections")
        return {"accepted": False, "errors": errors, "classification": "REJECTED"}

    try:
        cadence = _int(c050, "cadence_qwords")
        d6 = _int(c050, "f03_to_f06_total_delta_qwords")
        d7 = _int(c050, "f03_to_f07_total_delta_qwords")
        qa = _int(phase, "qword_count_a")
        qb = _int(phase, "qword_count_b")
        sa = _int(phase, "longest_run_start_a")
        sb = _int(phase, "longest_run_start_b")
        run = _int(phase, "longest_run_qwords")
        total = _int(phase, "total_matching_qwords")
        tail_a = _int(phase, "trailing_qwords_after_longest_a")
        tail_b = _int(phase, "trailing_qwords_after_longest_b")
        mod_a = _int(phase, "logical_mod8_a")
        mod_b = _int(phase, "logical_mod8_b")
    except (KeyError, TypeError):
        errors.append("malformed_numeric_inputs")
        return {"accepted": False, "errors": errors, "classification": "REJECTED"}

    residual6 = d6 - cadence
    residual7 = d7 - cadence
    residual_diff = residual7 - residual6
    payload_delta = qb - qa
    invariant_start_delta = sb - sa

    if cadence != 307:
        errors.append("unexpected_cadence_qwords")
    if phase.get("same_logical_mod8") is not True or mod_a != mod_b:
        errors.append("phase_pair_not_same_mod8")
    if tail_a != tail_b:
        errors.append("trailing_qword_count_mismatch")
    if run != total:
        errors.append("phase_pair_not_single_reported_exact_run")
    if residual_diff != 12:
        errors.append("unexpected_residual_difference")
    if payload_delta != residual_diff:
        errors.append("payload_delta_does_not_equal_residual_difference")
    if invariant_start_delta != residual_diff:
        errors.append("invariant_start_shift_does_not_equal_residual_difference")
    if tail_a != 1:
        errors.append("unexpected_trailing_qwords")

    accepted = not errors
    return {
        "accepted": accepted,
        "errors": errors,
        "classification": CLASSIFICATION if accepted else "REJECTED",
        "derived": {
            "f03_to_f06_residual_qwords": residual6,
            "f03_to_f07_residual_qwords": residual7,
            "residual_difference_qwords": residual_diff,
            "f06_f07_payload_qword_delta": payload_delta,
            "invariant_run_start_delta_qwords": invariant_start_delta,
            "invariant_run_qwords": run,
            "trailing_qwords_each": tail_a if tail_a == tail_b else None,
        },
        "semantic_binding": "UNRESOLVED",
        "material_owner": "UNRESOLVED",
        "object_owner": "UNRESOLVED",
        "semantic_promotion": False,
        "blender_emit_ready": False,
        "runtime_dispatch": False,
    }


def self_test() -> None:
    out = reconcile(BASELINE)
    assert out["accepted"] is True
    assert out["derived"]["f03_to_f06_residual_qwords"] == 13
    assert out["derived"]["f03_to_f07_residual_qwords"] == 25
    assert out["derived"]["residual_difference_qwords"] == 12

    cases = []
    bad = deepcopy(BASELINE); bad["c050"]["f03_to_f07_total_delta_qwords"] = 333; cases.append(bad)
    bad = deepcopy(BASELINE); bad["phase_pair"]["longest_run_start_b"] = 458; cases.append(bad)
    bad = deepcopy(BASELINE); bad["phase_pair"]["qword_count_b"] = 2577; cases.append(bad)
    bad = deepcopy(BASELINE); bad["phase_pair"]["same_logical_mod8"] = False; cases.append(bad)
    bad = deepcopy(BASELINE); bad["phase_pair"]["trailing_qwords_after_longest_b"] = 2; cases.append(bad)
    bad = deepcopy(BASELINE); bad["semantic_promotion_count"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); bad["blender_emit_ready"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["raw_private_bytes_published"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["runtime_dispatch"] = True; cases.append(bad)

    for candidate in cases:
        assert reconcile(candidate)["accepted"] is False

    print("C056_SELF_TEST_PASS 10/10")


if __name__ == "__main__":
    self_test()
