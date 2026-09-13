#!/usr/bin/env python3
"""Validate a reference-only Companion C handoff package.

This validator is intentionally conservative: a handoff is safe only when it
preserves the side-lane's unresolved semantic state and cannot imply runtime or
mainline action.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

REQUIRED_UNLOCKS = {
    "I1_ISOLATED_PLUS965_STATIC_REF",
    "I2_PUBLIC_SAFE_POSITIONAL_AGGREGATE",
    "I3_INTERPRETABLE_CONTROLLED_PAIR_OR_LABELED_DIFFERENTIAL",
    "I4_CURRENT_MODEL_NODE_MAPPING_ARTIFACT",
}


def validate(package: dict) -> dict:
    errors: list[str] = []
    if package.get("merge_policy") not in {None, "NO_AUTOMATIC_MERGE"}:
        errors.append("automatic_merge_not_allowed")
    if package.get("pipeline_stage") != "STRUCTURAL_ONLY":
        errors.append("unexpected_pipeline_stage")
    if int(package.get("semantic_promotion_count", -1)) != 0:
        errors.append("semantic_promotion_not_zero")
    if bool(package.get("blender_mesh_emit_ready")):
        errors.append("mesh_emit_must_remain_blocked")
    if bool(package.get("blender_scene_emit_ready")):
        errors.append("scene_emit_must_remain_blocked")

    isolation = dict(package.get("isolation") or {})
    for key in ("runtime_jobs", "modeler_actions", "worker_actions", "rio26_mutations", "mainline_mutations"):
        if int(isolation.get(key, 0)) != 0:
            errors.append(f"nonzero_{key}")
    if bool(isolation.get("automatic_merge")):
        errors.append("automatic_merge_true")
    if bool(isolation.get("private_bytes_in_public_repo")):
        errors.append("private_bytes_public")

    unlocks = set(package.get("future_unlock_inputs") or [])
    if not REQUIRED_UNLOCKS.issubset(unlocks):
        errors.append("unlock_contract_incomplete")

    accepted = not errors
    return {
        "schema_version": "csmc_analysis_c_handoff_contract_result_v1",
        "handoff_state": "HANDOFF_REFERENCE_SAFE" if accepted else "HANDOFF_REJECTED",
        "accepted": accepted,
        "errors": errors,
        "allowed_effects": ["read", "review", "reference_public_safe_findings"],
        "forbidden_effects": [
            "automatic_merge",
            "semantic_promotion",
            "blender_emit_enablement",
            "runtime_dispatch",
            "modeler_action",
            "worker_action",
            "rio26_mutation",
            "private_payload_publication",
        ],
    }


def self_test() -> None:
    base = {
        "merge_policy": "NO_AUTOMATIC_MERGE",
        "pipeline_stage": "STRUCTURAL_ONLY",
        "semantic_promotion_count": 0,
        "blender_mesh_emit_ready": False,
        "blender_scene_emit_ready": False,
        "future_unlock_inputs": sorted(REQUIRED_UNLOCKS),
        "isolation": {
            "runtime_jobs": 0,
            "modeler_actions": 0,
            "worker_actions": 0,
            "rio26_mutations": 0,
            "mainline_mutations": 0,
            "private_bytes_in_public_repo": False,
            "automatic_merge": False,
        },
    }
    assert validate(base)["accepted"] is True
    assert validate(dict(base, semantic_promotion_count=1))["accepted"] is False
    assert validate(dict(base, blender_mesh_emit_ready=True))["accepted"] is False
    assert validate(dict(base, merge_policy="AUTO_MERGE"))["accepted"] is False
    assert validate(dict(base, isolation={**base["isolation"], "runtime_jobs": 1}))["accepted"] is False
    print("SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ns = ap.parse_args()
    if ns.self_test:
        self_test()
        return 0
    if ns.input is None:
        ap.error("input required unless --self-test")
    print(json.dumps(validate(json.loads(ns.input.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
