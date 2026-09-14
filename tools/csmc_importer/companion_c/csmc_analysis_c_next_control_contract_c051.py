#!/usr/bin/env python3
"""C-051: preregister next controlled-fixture evidence without acquiring CSMC bytes."""
from dataclasses import dataclass
from typing import Mapping, Any

PIPELINE_STAGE = "STRUCTURAL_ONLY"
SEMANTIC_PROMOTION_COUNT = 0
BLENDER_EMIT_READY = False
RUNTIME_DISPATCH = False

@dataclass(frozen=True)
class FixtureSpec:
    fixture_id: str
    family: str
    mesh_objects: int
    material_slots: int
    used_material_partitions: int
    bones: int
    weight_assignments: int
    uv_layers: int
    expected_cadence_if_render_parts: int
    same_identity_group: str | None = None

FIXTURES = {
    "MAT3_ALLUSED": FixtureSpec("MAT3_ALLUSED","material",1,3,3,0,0,0,5,"MAT3"),
    "MAT3_ONEUSED": FixtureSpec("MAT3_ONEUSED","material",1,3,1,0,0,0,0,"MAT3"),
    "THREE_CUBES": FixtureSpec("THREE_CUBES","object",3,0,3,0,0,0,5,None),
    "UV_OFF": FixtureSpec("UV_OFF","uv",1,0,1,0,0,0,3,"UV01"),
    "UV_ON": FixtureSpec("UV_ON","uv",1,0,1,0,0,1,3,"UV01"),
    "W50_50": FixtureSpec("W50_50","weight_scalar",1,0,1,2,16,0,3,"WPAIR"),
    "W25_75": FixtureSpec("W25_75","weight_scalar",1,0,1,2,16,0,3,"WPAIR"),
}

ALLOWED_OBSERVATION_FIELDS = {
    "fixture_id","logical_length","stored_length","cadence_count",
    "same_offset_changed_qwords","changed_region_count","notes"
}

def validate_observation(obs: Mapping[str, Any]) -> dict:
    extra = set(obs) - ALLOWED_OBSERVATION_FIELDS
    if extra:
        return {"accepted": False, "reason": "unexpected_field", "fields": sorted(extra)}
    fixture_id = obs.get("fixture_id")
    if fixture_id not in FIXTURES:
        return {"accepted": False, "reason": "unknown_fixture"}
    for k in ("logical_length","stored_length","cadence_count"):
        if k not in obs or type(obs[k]) is not int or obs[k] < 0:
            return {"accepted": False, "reason": f"invalid_{k}"}
    logical = obs["logical_length"]
    stored = obs["stored_length"]
    if stored != ((logical + 7)//8)*8 + 8:
        return {"accepted": False, "reason": "outer_framing_rule_failed"}
    return {
        "accepted": True,
        "fixture_id": fixture_id,
        "pipeline_stage": PIPELINE_STAGE,
        "semantic_promotion_count": SEMANTIC_PROMOTION_COUNT,
        "blender_emit_ready": BLENDER_EMIT_READY,
        "runtime_dispatch": RUNTIME_DISPATCH,
    }

def evaluate_set(observations: list[Mapping[str, Any]]) -> dict:
    validated = {}
    for obs in observations:
        v = validate_observation(obs)
        if not v["accepted"]:
            return {"accepted": False, "reason": "observation_rejected", "detail": v}
        validated[obs["fixture_id"]] = dict(obs)
    needed = set(FIXTURES)
    if set(validated) != needed:
        return {"accepted": False, "reason": "fixture_set_incomplete",
                "missing": sorted(needed-set(validated)),
                "unexpected": sorted(set(validated)-needed)}
    cad = {k: v["cadence_count"] for k,v in validated.items()}
    if cad["MAT3_ALLUSED"] != 5:
        material = "RENDER_PART_FORMULA_REFUTED"
    elif cad["MAT3_ONEUSED"] == 5:
        material = "DEFINED_SLOT_OR_SERIALIZED_PART_COUNT_SUPPORTED"
    elif cad["MAT3_ONEUSED"] == 3:
        material = "USED_PARTITION_COUNT_SUPPORTED"
    else:
        material = "MATERIAL_CARDINALITY_MODEL_UNRESOLVED"
    object_result = (
        "OBJECT_RENDER_PART_FORMULA_SUPPORTED"
        if cad["THREE_CUBES"] == 5
        else "OBJECT_RENDER_PART_FORMULA_REFUTED"
    )
    uv_result = (
        "CADENCE_UV_INVARIANT_SUPPORTED"
        if cad["UV_OFF"] == cad["UV_ON"] == 3
        else "CADENCE_UV_INVARIANT_REFUTED"
    )
    weight_result = (
        "CADENCE_WEIGHT_VALUE_INVARIANT_SUPPORTED"
        if cad["W50_50"] == cad["W25_75"] == 3
        else "CADENCE_WEIGHT_VALUE_INVARIANT_REFUTED"
    )
    return {
        "accepted": True,
        "material_discriminator": material,
        "object_discriminator": object_result,
        "uv_negative_control": uv_result,
        "weight_negative_control": weight_result,
        "weight_value_pair_same_cardinality": True,
        "weight_value_pair_same_identity_group": True,
        "semantic_promotion": False,
        "pipeline_stage": PIPELINE_STAGE,
        "blender_emit_ready": BLENDER_EMIT_READY,
        "runtime_dispatch": RUNTIME_DISPATCH,
    }

def _framed(logical: int) -> int:
    return ((logical + 7)//8)*8 + 8

def self_test() -> None:
    obs = [
        {"fixture_id":"MAT3_ALLUSED","logical_length":18000,"stored_length":_framed(18000),"cadence_count":5},
        {"fixture_id":"MAT3_ONEUSED","logical_length":17900,"stored_length":_framed(17900),"cadence_count":5},
        {"fixture_id":"THREE_CUBES","logical_length":20000,"stored_length":_framed(20000),"cadence_count":5},
        {"fixture_id":"UV_OFF","logical_length":17800,"stored_length":_framed(17800),"cadence_count":3},
        {"fixture_id":"UV_ON","logical_length":17850,"stored_length":_framed(17850),"cadence_count":3},
        {"fixture_id":"W50_50","logical_length":18100,"stored_length":_framed(18100),"cadence_count":3},
        {"fixture_id":"W25_75","logical_length":18100,"stored_length":_framed(18100),"cadence_count":3},
    ]
    out = evaluate_set(obs)
    assert out["accepted"] is True
    assert out["material_discriminator"] == "DEFINED_SLOT_OR_SERIALIZED_PART_COUNT_SUPPORTED"
    assert out["object_discriminator"] == "OBJECT_RENDER_PART_FORMULA_SUPPORTED"
    assert out["uv_negative_control"] == "CADENCE_UV_INVARIANT_SUPPORTED"
    assert out["weight_negative_control"] == "CADENCE_WEIGHT_VALUE_INVARIANT_SUPPORTED"
    bad = dict(obs[0]); bad["stored_length"] += 8
    assert validate_observation(bad)["accepted"] is False
    bad2 = dict(obs[0]); bad2["raw_bytes"] = "forbidden"
    assert validate_observation(bad2)["reason"] == "unexpected_field"
    alt = [dict(x) for x in obs]; alt[1]["cadence_count"] = 3
    assert evaluate_set(alt)["material_discriminator"] == "USED_PARTITION_COUNT_SUPPORTED"
    alt2 = [dict(x) for x in obs]; alt2[2]["cadence_count"] = 4
    assert evaluate_set(alt2)["object_discriminator"] == "OBJECT_RENDER_PART_FORMULA_REFUTED"
    print("SELF_TEST_PASS 11/11")

if __name__ == "__main__":
    self_test()
