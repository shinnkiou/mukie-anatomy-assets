#!/usr/bin/env python3
"""C-054 fail-closed stage-order gate for the preregistered C-051 evidence path."""
from __future__ import annotations
from typing import Any, Mapping

REQUIRED_FIXTURES = {
    "MAT3_ALLUSED","MAT3_ONEUSED","THREE_CUBES","UV_OFF","UV_ON","W50_50","W25_75"
}
FORBIDDEN_FIELDS = {"raw_csmc_bytes","csmc_payload","csmc_blob","raw_payload","raw_blend_bytes","binary_blob","payload_base64"}
ZERO_FIELDS = ("runtime_jobs","modeler_actions","worker_actions","canary_actions","control_gate_actions","mainline_mutations","rio26_mutations","semantic_promotion_count")


def _bool(m: Mapping[str, Any], key: str) -> bool | None:
    v = m.get(key)
    return v if type(v) is bool else None


def evaluate(pkg: Mapping[str, Any]) -> dict:
    if not isinstance(pkg, Mapping):
        return {"accepted": False, "state": "REJECTED", "reason": "package_not_mapping"}
    leaked = sorted(FORBIDDEN_FIELDS.intersection(pkg))
    if leaked:
        return {"accepted": False, "state": "REJECTED", "reason": "forbidden_raw_field", "fields": leaked}
    if pkg.get("pipeline_stage") != "STRUCTURAL_ONLY":
        return {"accepted": False, "state": "REJECTED", "reason": "pipeline_stage_not_structural_only"}
    for field in ZERO_FIELDS:
        if type(pkg.get(field)) is not int or pkg[field] != 0:
            return {"accepted": False, "state": "REJECTED", "reason": f"nonzero_or_missing_{field}"}
    for field in ("blender_emit_ready", "runtime_dispatch", "automatic_integration", "raw_private_bytes_published"):
        if _bool(pkg, field) is not False:
            return {"accepted": False, "state": "REJECTED", "reason": f"unsafe_or_missing_{field}"}

    fixture_ids = pkg.get("fixture_ids")
    if not isinstance(fixture_ids, list) or set(fixture_ids) != REQUIRED_FIXTURES or len(fixture_ids) != 7:
        return {"accepted": False, "state": "REJECTED", "reason": "fixture_set_invalid"}

    teacher_present = _bool(pkg, "teacher_manifest_present")
    teacher_pass = _bool(pkg, "c052_teacher_validation_pass")
    conversion_present = _bool(pkg, "conversion_manifest_present")
    provenance_pass = _bool(pkg, "c053_provenance_validation_pass")
    aggregate_present = _bool(pkg, "aggregate_manifest_present")
    aggregate_pass = _bool(pkg, "c051_aggregate_validation_pass")
    if any(v is None for v in (teacher_present, teacher_pass, conversion_present, provenance_pass, aggregate_present, aggregate_pass)):
        return {"accepted": False, "state": "REJECTED", "reason": "stage_boolean_missing_or_malformed"}

    # Impossible/out-of-order claims fail closed rather than being downgraded.
    if teacher_pass and not teacher_present:
        return {"accepted": False, "state": "REJECTED", "reason": "teacher_pass_without_manifest"}
    if conversion_present and not teacher_pass:
        return {"accepted": False, "state": "REJECTED", "reason": "conversion_before_c052_pass"}
    if provenance_pass and not conversion_present:
        return {"accepted": False, "state": "REJECTED", "reason": "provenance_pass_without_conversion"}
    if aggregate_present and not provenance_pass:
        return {"accepted": False, "state": "REJECTED", "reason": "aggregate_before_c053_pass"}
    if aggregate_pass and not aggregate_present:
        return {"accepted": False, "state": "REJECTED", "reason": "aggregate_pass_without_manifest"}

    if not teacher_present:
        state = "WAITING_C051_SOURCE_MANIFEST"
    elif not teacher_pass:
        state = "SOURCE_REALIZATION_REJECTED"
    elif not conversion_present:
        state = "SOURCE_VALIDATED_WAITING_EXTERNAL_CONVERSION"
    elif not provenance_pass:
        state = "PROVENANCE_REJECTED"
    elif not aggregate_present:
        state = "PROVENANCE_VALIDATED_WAITING_AGGREGATE"
    elif not aggregate_pass:
        state = "AGGREGATE_REJECTED"
    else:
        state = "C051_EVIDENCE_ADMISSIBLE_STRUCTURAL_ONLY"

    return {
        "accepted": state not in {"SOURCE_REALIZATION_REJECTED", "PROVENANCE_REJECTED", "AGGREGATE_REJECTED"},
        "state": state,
        "semantic_claim": "NONE",
        "pipeline_stage": "STRUCTURAL_ONLY",
        "semantic_promotion_count": 0,
        "blender_emit_ready": False,
        "runtime_dispatch": False,
        "automatic_integration": False,
    }


def base_package():
    return {
        "fixture_ids": sorted(REQUIRED_FIXTURES),
        "pipeline_stage": "STRUCTURAL_ONLY",
        "runtime_jobs": 0, "modeler_actions": 0, "worker_actions": 0, "canary_actions": 0, "control_gate_actions": 0,
        "mainline_mutations": 0, "rio26_mutations": 0, "semantic_promotion_count": 0,
        "blender_emit_ready": False, "runtime_dispatch": False, "automatic_integration": False, "raw_private_bytes_published": False,
        "teacher_manifest_present": False, "c052_teacher_validation_pass": False,
        "conversion_manifest_present": False, "c053_provenance_validation_pass": False,
        "aggregate_manifest_present": False, "c051_aggregate_validation_pass": False,
    }


def self_test():
    p = base_package(); assert evaluate(p)["state"] == "WAITING_C051_SOURCE_MANIFEST"
    p = base_package(); p.update(teacher_manifest_present=True, c052_teacher_validation_pass=True); assert evaluate(p)["state"] == "SOURCE_VALIDATED_WAITING_EXTERNAL_CONVERSION"
    p = base_package(); p.update(teacher_manifest_present=True, c052_teacher_validation_pass=True, conversion_manifest_present=True, c053_provenance_validation_pass=True); assert evaluate(p)["state"] == "PROVENANCE_VALIDATED_WAITING_AGGREGATE"
    p = base_package(); p.update(teacher_manifest_present=True, c052_teacher_validation_pass=True, conversion_manifest_present=True, c053_provenance_validation_pass=True, aggregate_manifest_present=True, c051_aggregate_validation_pass=True); out = evaluate(p); assert out["state"] == "C051_EVIDENCE_ADMISSIBLE_STRUCTURAL_ONLY" and out["semantic_promotion_count"] == 0
    p = base_package(); p["c052_teacher_validation_pass"] = True; assert evaluate(p)["reason"] == "teacher_pass_without_manifest"
    p = base_package(); p["conversion_manifest_present"] = True; assert evaluate(p)["reason"] == "conversion_before_c052_pass"
    p = base_package(); p["aggregate_manifest_present"] = True; assert evaluate(p)["reason"] == "aggregate_before_c053_pass"
    p = base_package(); p["runtime_jobs"] = 1; assert evaluate(p)["reason"] == "nonzero_or_missing_runtime_jobs"
    p = base_package(); p["raw_csmc_bytes"] = "x"; assert evaluate(p)["reason"] == "forbidden_raw_field"
    p = base_package(); p["semantic_promotion_count"] = 1; assert evaluate(p)["reason"] == "nonzero_or_missing_semantic_promotion_count"
    print("SELF_TEST_PASS 10/10")


if __name__ == "__main__":
    self_test()
