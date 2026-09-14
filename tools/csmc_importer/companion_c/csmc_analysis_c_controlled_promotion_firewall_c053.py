#!/usr/bin/env python3
"""C-053: fail-closed promotion firewall for C-050/C-051/C-052 controlled evidence.

Public-safe metadata only. This module never acquires CSMC bytes, dispatches runtime,
or promotes semantics by itself.
"""
from __future__ import annotations
from typing import Any, Mapping

PIPELINE_STAGE = "STRUCTURAL_ONLY"
SEMANTIC_PROMOTION_COUNT = 0
BLENDER_EMIT_READY = False
RUNTIME_DISPATCH = False

FORBIDDEN_KEYS = {
    "raw_csmc_bytes",
    "csmc_payload",
    "csmc_blob",
    "raw_payload",
    "private_payload",
    "private_csmc_bytes",
}

ALLOWED_TEACHER_STATES = {
    "VALIDATOR_READY_TEACHER_MANIFEST_NOT_YET_ACQUIRED",
    "TEACHER_MANIFEST_VALIDATED",
}

ALLOWED_RENDER_PART_CONFIDENCE = {
    "HIGH_NOT_CONFIRMED",
    "LEVEL_4_CANDIDATE_ONLY",
}


def _forbidden_path(value: Any, path: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_s = str(key)
            child_path = f"{path}.{key_s}"
            if key_s in FORBIDDEN_KEYS:
                return child_path
            hit = _forbidden_path(child, child_path)
            if hit:
                return hit
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hit = _forbidden_path(child, f"{path}[{idx}]")
            if hit:
                return hit
    return None


def _is_nonneg_int(value: Any) -> bool:
    return type(value) is int and value >= 0


def evaluate_promotion_firewall(row: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"accepted": False, "reason": "input_not_mapping"}

    forbidden = _forbidden_path(row)
    if forbidden:
        return {"accepted": False, "reason": "forbidden_private_or_raw_field", "path": forbidden}

    required = {
        "pipeline_stage",
        "semantic_promotion_count",
        "semantic_promotion_requested",
        "blender_emit_ready",
        "runtime_dispatch",
        "render_part_level",
        "render_part_confidence",
        "owner_consumer_confirmed",
        "i3_partial_pairs",
        "i3_valid_pairs",
        "i3_unlock_claimed",
        "teacher_manifest_state",
        "c051_prediction_count",
        "c051_prediction_observation_count",
        "prediction_as_observation",
        "candidate_as_confirmed",
    }
    missing = sorted(required - set(row))
    if missing:
        return {"accepted": False, "reason": "missing_required_fields", "missing": missing}

    for field in (
        "semantic_promotion_count",
        "render_part_level",
        "i3_partial_pairs",
        "i3_valid_pairs",
        "c051_prediction_count",
        "c051_prediction_observation_count",
    ):
        if not _is_nonneg_int(row[field]):
            return {"accepted": False, "reason": f"invalid_{field}"}

    for field in (
        "semantic_promotion_requested",
        "blender_emit_ready",
        "runtime_dispatch",
        "owner_consumer_confirmed",
        "i3_unlock_claimed",
        "prediction_as_observation",
        "candidate_as_confirmed",
    ):
        if type(row[field]) is not bool:
            return {"accepted": False, "reason": f"invalid_{field}"}

    if row["pipeline_stage"] != PIPELINE_STAGE:
        return {"accepted": False, "reason": "pipeline_stage_not_structural_only"}
    if row["semantic_promotion_count"] != 0:
        return {"accepted": False, "reason": "semantic_promotion_count_nonzero"}
    if row["semantic_promotion_requested"]:
        return {"accepted": False, "reason": "semantic_promotion_request_forbidden"}
    if row["blender_emit_ready"]:
        return {"accepted": False, "reason": "blender_emit_forbidden"}
    if row["runtime_dispatch"]:
        return {"accepted": False, "reason": "runtime_dispatch_forbidden"}
    if row["prediction_as_observation"]:
        return {"accepted": False, "reason": "prediction_as_observation_forbidden"}
    if row["candidate_as_confirmed"]:
        return {"accepted": False, "reason": "candidate_as_confirmed_forbidden"}

    teacher_state = row["teacher_manifest_state"]
    if teacher_state not in ALLOWED_TEACHER_STATES:
        return {"accepted": False, "reason": "unknown_teacher_manifest_state"}

    if row["c051_prediction_observation_count"] > row["c051_prediction_count"]:
        return {"accepted": False, "reason": "prediction_observation_count_exceeds_preregistration"}
    if (
        row["c051_prediction_observation_count"] > 0
        and teacher_state != "TEACHER_MANIFEST_VALIDATED"
    ):
        return {"accepted": False, "reason": "prediction_promoted_before_teacher_manifest"}

    if row["i3_valid_pairs"] > row["i3_partial_pairs"]:
        return {"accepted": False, "reason": "i3_valid_pairs_exceed_partial_pairs"}
    if row["i3_unlock_claimed"] and row["i3_valid_pairs"] == 0:
        return {"accepted": False, "reason": "i3_unlock_without_valid_pair"}

    if row["render_part_level"] > 4:
        return {"accepted": False, "reason": "render_part_level_above_current_evidence"}
    if row["render_part_confidence"] not in ALLOWED_RENDER_PART_CONFIDENCE:
        return {"accepted": False, "reason": "render_part_confidence_overclaimed"}
    if row["owner_consumer_confirmed"]:
        # A future owner edge must go through the dedicated C-040/C-045 router path,
        # not silently upgrade this controlled-fixture evidence object.
        return {"accepted": False, "reason": "owner_consumer_evidence_requires_dedicated_unlock_route"}

    if teacher_state == "VALIDATOR_READY_TEACHER_MANIFEST_NOT_YET_ACQUIRED":
        next_action = "WAIT_FOR_C051_TEACHER_MANIFEST"
    elif row["c051_prediction_observation_count"] == 0:
        next_action = "WAIT_FOR_C051_CSMC_AGGREGATE"
    else:
        next_action = "EVALUATE_C051_PREREGISTERED_CONTRACT_ONLY"

    return {
        "accepted": True,
        "firewall_state": "ACTIVE_FAIL_CLOSED",
        "pipeline_stage": PIPELINE_STAGE,
        "semantic_promotion_count": SEMANTIC_PROMOTION_COUNT,
        "semantic_promotion_allowed": False,
        "blender_emit_ready": BLENDER_EMIT_READY,
        "runtime_dispatch": RUNTIME_DISPATCH,
        "render_part_claim_ceiling": "LEVEL_4_CANDIDATE_ONLY",
        "i3_partial_pairs": row["i3_partial_pairs"],
        "i3_valid_pairs": row["i3_valid_pairs"],
        "prediction_observations_admitted": row["c051_prediction_observation_count"],
        "next_static_action": next_action,
    }


def _base() -> dict[str, Any]:
    return {
        "pipeline_stage": "STRUCTURAL_ONLY",
        "semantic_promotion_count": 0,
        "semantic_promotion_requested": False,
        "blender_emit_ready": False,
        "runtime_dispatch": False,
        "render_part_level": 4,
        "render_part_confidence": "HIGH_NOT_CONFIRMED",
        "owner_consumer_confirmed": False,
        "i3_partial_pairs": 10,
        "i3_valid_pairs": 0,
        "i3_unlock_claimed": False,
        "teacher_manifest_state": "VALIDATOR_READY_TEACHER_MANIFEST_NOT_YET_ACQUIRED",
        "c051_prediction_count": 7,
        "c051_prediction_observation_count": 0,
        "prediction_as_observation": False,
        "candidate_as_confirmed": False,
    }


def self_test() -> None:
    base = _base()
    out = evaluate_promotion_firewall(base)
    assert out["accepted"] is True
    assert out["next_static_action"] == "WAIT_FOR_C051_TEACHER_MANIFEST"

    cases: list[tuple[dict[str, Any], str]] = []
    bad = dict(base); bad["raw_csmc_bytes"] = "forbidden"; cases.append((bad, "forbidden_private_or_raw_field"))
    bad = dict(base); bad["prediction_as_observation"] = True; cases.append((bad, "prediction_as_observation_forbidden"))
    bad = dict(base); bad["candidate_as_confirmed"] = True; cases.append((bad, "candidate_as_confirmed_forbidden"))
    bad = dict(base); bad["c051_prediction_observation_count"] = 1; cases.append((bad, "prediction_promoted_before_teacher_manifest"))
    bad = dict(base); bad["semantic_promotion_count"] = 1; cases.append((bad, "semantic_promotion_count_nonzero"))
    bad = dict(base); bad["semantic_promotion_requested"] = True; cases.append((bad, "semantic_promotion_request_forbidden"))
    bad = dict(base); bad["blender_emit_ready"] = True; cases.append((bad, "blender_emit_forbidden"))
    bad = dict(base); bad["runtime_dispatch"] = True; cases.append((bad, "runtime_dispatch_forbidden"))
    bad = dict(base); bad["render_part_level"] = 5; cases.append((bad, "render_part_level_above_current_evidence"))
    bad = dict(base); bad["render_part_confidence"] = "CONFIRMED"; cases.append((bad, "render_part_confidence_overclaimed"))
    bad = dict(base); bad["i3_unlock_claimed"] = True; cases.append((bad, "i3_unlock_without_valid_pair"))
    bad = dict(base); bad["i3_valid_pairs"] = 11; cases.append((bad, "i3_valid_pairs_exceed_partial_pairs"))
    bad = dict(base); bad["i3_partial_pairs"] = -1; cases.append((bad, "invalid_i3_partial_pairs"))
    bad = dict(base); bad["teacher_manifest_state"] = "PASS"; cases.append((bad, "unknown_teacher_manifest_state"))

    for row, reason in cases:
        result = evaluate_promotion_firewall(row)
        assert result["accepted"] is False, (reason, result)
        assert result["reason"] == reason, (reason, result)

    print("SELF_TEST_PASS 15/15")


if __name__ == "__main__":
    self_test()
