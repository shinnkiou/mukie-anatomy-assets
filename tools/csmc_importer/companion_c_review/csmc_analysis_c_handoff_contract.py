#!/usr/bin/env python3
"""Validate a reference-only Companion C handoff package.

This validator is intentionally conservative: a handoff is safe only when it
preserves the side-lane's unresolved semantic state and cannot imply runtime or
mainline action. Missing or malformed safety declarations are rejected rather
than assumed safe.
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
REQUIRED_ZERO_ISOLATION_KEYS = (
    "runtime_jobs",
    "modeler_actions",
    "worker_actions",
    "rio26_mutations",
    "mainline_mutations",
)
AUTOMATION_KEYS = ("automatic_merge", "automatic_integration")
PRIVATE_PUBLICATION_KEYS = (
    "private_bytes_in_public_repo",
    "public_repository_contains_private_payload",
)


def _require_zero(errors: list[str], obj: dict, key: str) -> None:
    if key not in obj:
        errors.append(f"missing_{key}")
        return
    try:
        value = int(obj[key])
    except (TypeError, ValueError):
        errors.append(f"invalid_{key}")
        return
    if value != 0:
        errors.append(f"nonzero_{key}")


def validate(package: dict) -> dict:
    errors: list[str] = []

    if "merge_policy" not in package:
        errors.append("missing_merge_policy")
    elif package["merge_policy"] != "NO_AUTOMATIC_MERGE":
        errors.append("automatic_merge_not_allowed")

    if package.get("pipeline_stage") != "STRUCTURAL_ONLY":
        errors.append("unexpected_pipeline_stage")

    if "semantic_promotion_count" not in package:
        errors.append("missing_semantic_promotion_count")
    else:
        try:
            semantic_promotion_count = int(package["semantic_promotion_count"])
        except (TypeError, ValueError):
            errors.append("invalid_semantic_promotion_count")
        else:
            if semantic_promotion_count != 0:
                errors.append("semantic_promotion_not_zero")

    for key, error_name in (
        ("blender_mesh_emit_ready", "mesh_emit_must_remain_blocked"),
        ("blender_scene_emit_ready", "scene_emit_must_remain_blocked"),
    ):
        if key not in package:
            errors.append(f"missing_{key}")
        elif package[key] is not False:
            errors.append(error_name)

    isolation = package.get("isolation")
    if not isinstance(isolation, dict):
        errors.append("missing_isolation_object")
        isolation = {}

    for key in REQUIRED_ZERO_ISOLATION_KEYS:
        _require_zero(errors, isolation, key)

    if not any(key in isolation for key in AUTOMATION_KEYS):
        errors.append("missing_automatic_integration_guardrail")
    elif any(bool(isolation.get(key)) for key in AUTOMATION_KEYS):
        errors.append("automatic_integration_true")

    if not any(key in isolation for key in PRIVATE_PUBLICATION_KEYS):
        errors.append("missing_private_publication_guardrail")
    elif any(bool(isolation.get(key)) for key in PRIVATE_PUBLICATION_KEYS):
        errors.append("private_bytes_public")

    unlocks = set(package.get("future_unlock_inputs") or [])
    if not REQUIRED_UNLOCKS.issubset(unlocks):
        errors.append("unlock_contract_incomplete")

    accepted = not errors
    return {
        "schema_version": "csmc_analysis_c_handoff_contract_result_v4",
        "handoff_state": "HANDOFF_REFERENCE_SAFE" if accepted else "HANDOFF_REJECTED",
        "accepted": accepted,
        "errors": errors,
        "allowed_effects": ["read", "review", "reference_public_safe_findings"],
        "forbidden_effects": [
            "automatic_merge",
            "automatic_integration",
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
            "public_repository_contains_private_payload": False,
            "automatic_integration": False,
        },
    }
    assert validate(base)["accepted"] is True
    assert validate(dict(base, semantic_promotion_count=1))["accepted"] is False
    assert validate(dict(base, blender_mesh_emit_ready=True))["accepted"] is False
    assert validate(dict(base, merge_policy="AUTO_MERGE"))["accepted"] is False
    assert validate(dict(base, isolation={**base["isolation"], "runtime_jobs": 1}))["accepted"] is False
    assert validate(dict(base, isolation={**base["isolation"], "automatic_integration": True}))["accepted"] is False
    assert validate(dict(base, isolation={**base["isolation"], "public_repository_contains_private_payload": True}))["accepted"] is False
    missing = dict(base, isolation={k: v for k, v in base["isolation"].items() if k != "worker_actions"})
    assert validate(missing)["accepted"] is False
    missing_merge = {k: v for k, v in base.items() if k != "merge_policy"}
    assert validate(missing_merge)["accepted"] is False
    missing_emit = {k: v for k, v in base.items() if k != "blender_mesh_emit_ready"}
    assert validate(missing_emit)["accepted"] is False
    malformed = dict(base, isolation={**base["isolation"], "worker_actions": "not-a-number"})
    assert validate(malformed)["accepted"] is False
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
