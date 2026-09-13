#!/usr/bin/env python3
"""C-048: Companion C adapter for the public-safe mainline next-evidence gate.

The mainline router is workflow control, not an acquisition mechanism. This
adapter preserves that boundary inside Companion C and reconciles the stricter
mainline six-bit I2 route with C-047's optional five-bit quota-assisted
normalizer.

No evidence acquisition, runtime dispatch, semantic promotion, Blender emit,
or mainline mutation is authorized here.
"""
from __future__ import annotations

import json
from typing import Any

I2_REQUIRED_ROWS = (2, 3, 8, 14, 15, 21)
DECISIVE_OWNER_EDGES = {
    "EXPLICIT_PARENT_RECORD_BOUNDARY",
    "EXPLICIT_PARENT_LENGTH_FIELD",
    "EXPLICIT_CONSUMER_CROSSREF",
}
UNLOCK_ALIASES = {
    "I1": "I1_ISOLATED_PLUS965_STATIC_REF",
    "I2": "I2_PUBLIC_SAFE_POSITIONAL_AGGREGATE",
    "I3": "I3_INTERPRETABLE_CONTROLLED_PAIR_OR_LABELED_DIFFERENTIAL",
    "I4": "I4_CURRENT_MODEL_NODE_MAPPING_ARTIFACT",
}
VALID_UNLOCK_CLASSES = set(UNLOCK_ALIASES.values())


def _valid_bit(value: Any) -> bool:
    return not isinstance(value, bool) and value in (0, 1)


def reconcile_event(manifest: dict) -> dict:
    """Map already-present validated evidence metadata to bounded Companion actions."""
    reasons: list[str] = []
    actions: list[dict] = []

    if manifest.get("acquisition_requested") is True:
        reasons.append("companion_c_must_not_acquire_evidence")
    if manifest.get("runtime_dispatch_requested") is True:
        reasons.append("companion_c_must_not_dispatch_runtime")
    if manifest.get("auto_semantic_promotion") is not False:
        reasons.append("auto_semantic_promotion_must_be_false")
    if manifest.get("auto_blender_emit") is not False:
        reasons.append("auto_blender_emit_must_be_false")

    if reasons:
        return _result(False, "REJECTED", [], reasons)

    bits = manifest.get("i2_bits_by_record")
    if bits is not None:
        if not isinstance(bits, dict):
            reasons.append("i2_bits_by_record_must_be_mapping")
        else:
            keys = set(bits)
            complete = (
                keys == set(I2_REQUIRED_ROWS)
                and all(_valid_bit(bits[index]) for index in keys)
                and manifest.get("i2_provenance_valid") is True
                and manifest.get("c047_residual_patch_accepted") is True
            )
            partial_five = (
                len(keys) == 5
                and keys.issubset(set(I2_REQUIRED_ROWS))
                and all(_valid_bit(bits[index]) for index in keys)
            )
            if complete:
                actions.append({
                    "action": "ASSEMBLE_COMPLETE_I2_AND_RUN_C040_FULL_VALIDATOR",
                    "scope": list(I2_REQUIRED_ROWS),
                    "note": (
                        "C-047 normalization is complete, but the full 22-row C-040 "
                        "I2 validator remains mandatory before intake acceptance."
                    ),
                })
            elif partial_five:
                actions.append({
                    "action": "ROUTE_PARTIAL_I2_THROUGH_C047_ONLY",
                    "scope": sorted(keys),
                    "note": (
                        "The mainline router intentionally requires a complete six-bit "
                        "artifact. A five-bit artifact is not sent directly to mainline; "
                        "it may first pass C-047 quota-assisted normalization."
                    ),
                })
            else:
                reasons.append("i2_artifact_not_complete_or_not_c047_normalized")

    owner_edges = sorted(
        set(manifest.get("decisive_owner_edges") or ()).intersection(DECISIVE_OWNER_EDGES)
    )
    if owner_edges:
        actions.append({
            "action": "REVIEW_NEW_BOUNDARY_LOCAL_OWNER_EDGE_ONLY",
            "scope": owner_edges,
            "rerun_c045_search": False,
        })

    normalized_unlocks: list[str] = []
    for unlock_class in manifest.get("validated_unlock_classes") or ():
        normalized = UNLOCK_ALIASES.get(unlock_class, unlock_class)
        if normalized in VALID_UNLOCK_CLASSES and normalized not in normalized_unlocks:
            normalized_unlocks.append(normalized)
    if normalized_unlocks:
        actions.append({
            "action": "PROCESS_VALIDATED_STATIC_UNLOCK_CLASS_ONLY",
            "scope": sorted(normalized_unlocks),
            "intake_implies_semantics": False,
        })

    if manifest.get("external_authorized_pair_present") is True:
        if (
            manifest.get("external_pair_hash_match_verified") is True
            and manifest.get("i1_static_validation_accepted") is True
        ):
            actions.append({
                "action": "ALLOW_PREREGISTERED_FIXED_ROLE_PROBE_ONLY",
                "scope": [
                    "record_whole",
                    "stable_prefix_0_20",
                    "control_zone_21_27",
                    "preserved_island_25_26",
                ],
                "posthoc_window_widening": False,
                "acquire_pair": False,
            })
        else:
            reasons.append("external_pair_not_i1_validated")

    if reasons:
        return _result(False, "REJECTED", [], reasons)

    status = (
        "NEW_ADMISSIBLE_EVIDENCE_PRESENT"
        if actions
        else "NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS"
    )
    return _result(True, status, actions, [])


def _result(accepted: bool, status: str, actions: list[dict], reasons: list[str]) -> dict:
    return {
        "schema_version": "csmc_analysis_c_next_evidence_router_adapter_v1",
        "accepted": accepted,
        "status": status,
        "selected_companion_actions": actions,
        "reasons": reasons,
        "runtime_dispatch": False,
        "evidence_acquisition": False,
        "semantic_promotion": False,
        "blender_emit": False,
        "mainline_mutation": False,
        "rio26_mutation": False,
    }


if __name__ == "__main__":
    print(json.dumps(reconcile_event({
        "auto_semantic_promotion": False,
        "auto_blender_emit": False,
    }), indent=2, sort_keys=True))
