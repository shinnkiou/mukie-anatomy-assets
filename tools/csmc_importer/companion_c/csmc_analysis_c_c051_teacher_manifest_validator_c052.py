#!/usr/bin/env python3
"""C-052: validate Blender teacher manifests for the preregistered C-051 controls.

Public-safe metadata only. No CSMC bytes, MODELER, runtime, or semantic promotion.
"""
from __future__ import annotations
from typing import Any, Mapping

PIPELINE_STAGE = "STRUCTURAL_ONLY"
SEMANTIC_PROMOTION_COUNT = 0
BLENDER_EMIT_READY = False
RUNTIME_DISPATCH = False

REQUIRED_IDS = {
    "MAT3_ALLUSED",
    "MAT3_ONEUSED",
    "THREE_CUBES",
    "UV_OFF",
    "UV_ON",
    "W50_50",
    "W25_75",
}

COUNT_FIELDS = (
    "mesh_object_count",
    "vertices_total",
    "triangles_total",
    "material_slots_total",
    "used_material_indices_total",
    "uv_layers_total",
    "bones_total",
    "weight_assignments_total",
)

FORBIDDEN_FIELDS = {"raw_csmc_bytes", "csmc_payload", "csmc_blob", "raw_payload"}


def _is_nonneg_int(v: Any) -> bool:
    return type(v) is int and v >= 0


def _identity(row: Mapping[str, Any], fields: tuple[str, ...]) -> tuple[Any, ...]:
    return tuple(row.get(k) for k in fields)


def validate_teacher_manifest(rows: list[Mapping[str, Any]]) -> dict:
    if not isinstance(rows, list) or not rows:
        return {"accepted": False, "reason": "rows_missing"}

    by_id: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            return {"accepted": False, "reason": "row_not_mapping"}
        if FORBIDDEN_FIELDS.intersection(row):
            return {
                "accepted": False,
                "reason": "forbidden_raw_field",
                "fields": sorted(FORBIDDEN_FIELDS.intersection(row)),
            }
        fixture_id = row.get("fixture_id")
        if fixture_id not in REQUIRED_IDS:
            return {"accepted": False, "reason": "unknown_fixture", "fixture_id": fixture_id}
        if fixture_id in by_id:
            return {"accepted": False, "reason": "duplicate_fixture", "fixture_id": fixture_id}
        for field in COUNT_FIELDS:
            if field not in row or not _is_nonneg_int(row[field]):
                return {"accepted": False, "reason": f"invalid_{field}", "fixture_id": fixture_id}
        by_id[fixture_id] = row

    if set(by_id) != REQUIRED_IDS:
        return {
            "accepted": False,
            "reason": "fixture_set_incomplete",
            "missing": sorted(REQUIRED_IDS - set(by_id)),
            "unexpected": sorted(set(by_id) - REQUIRED_IDS),
        }

    mat_a = by_id["MAT3_ALLUSED"]
    mat_b = by_id["MAT3_ONEUSED"]
    mat_identity_fields = (
        "mesh_object_names", "mesh_data_names", "vertices_total", "triangles_total",
        "material_slot_names", "material_slots_total",
    )
    if _identity(mat_a, mat_identity_fields) != _identity(mat_b, mat_identity_fields):
        return {"accepted": False, "reason": "material_pair_identity_mismatch"}
    if mat_a["material_slots_total"] != 3 or mat_b["material_slots_total"] != 3:
        return {"accepted": False, "reason": "material_slot_count_not_three"}
    if mat_a["used_material_indices_total"] != 3 or mat_b["used_material_indices_total"] != 1:
        return {"accepted": False, "reason": "material_usage_discriminator_not_realized"}

    obj = by_id["THREE_CUBES"]
    if obj["mesh_object_count"] != 3:
        return {"accepted": False, "reason": "three_cubes_object_count_not_three"}

    uv0 = by_id["UV_OFF"]
    uv1 = by_id["UV_ON"]
    uv_identity_fields = (
        "mesh_object_names", "mesh_data_names", "vertices_total", "triangles_total",
        "material_slot_names", "material_slots_total",
    )
    if _identity(uv0, uv_identity_fields) != _identity(uv1, uv_identity_fields):
        return {"accepted": False, "reason": "uv_pair_identity_mismatch"}
    if uv0["uv_layers_total"] != 0 or uv1["uv_layers_total"] != 1:
        return {"accepted": False, "reason": "uv_absence_presence_not_realized"}

    w0 = by_id["W50_50"]
    w1 = by_id["W25_75"]
    # Check intended cardinality first so failure cause stays explicit.
    if w0["bones_total"] != 2 or w1["bones_total"] != 2:
        return {"accepted": False, "reason": "weight_pair_bone_count_not_two"}
    if w0["weight_assignments_total"] != 16 or w1["weight_assignments_total"] != 16:
        return {"accepted": False, "reason": "weight_pair_assignment_count_not_sixteen"}
    weight_identity_fields = (
        "mesh_object_names", "mesh_data_names", "armature_object_names", "bone_names",
        "vertex_group_names", "vertices_total", "triangles_total", "bones_total",
        "weight_assignments_total",
    )
    if _identity(w0, weight_identity_fields) != _identity(w1, weight_identity_fields):
        return {"accepted": False, "reason": "weight_pair_identity_mismatch"}

    h0 = w0.get("weight_histogram")
    h1 = w1.get("weight_histogram")
    if not isinstance(h0, Mapping) or not isinstance(h1, Mapping):
        return {"accepted": False, "reason": "weight_histogram_missing"}
    if h0 == h1:
        return {"accepted": False, "reason": "weight_scalar_change_not_realized"}

    return {
        "accepted": True,
        "fixture_count": len(by_id),
        "material_control": "SAME_IDENTITY_3SLOTS_USAGE_3_VS_1",
        "object_control": "THREE_MESH_OBJECTS_REALIZED",
        "uv_control": "SAME_IDENTITY_0_VS_1_LAYER",
        "weight_control": "SAME_IDENTITY_16_ASSIGNMENTS_DIFFERENT_SCALARS",
        "pipeline_stage": PIPELINE_STAGE,
        "semantic_promotion_count": SEMANTIC_PROMOTION_COUNT,
        "blender_emit_ready": BLENDER_EMIT_READY,
        "runtime_dispatch": RUNTIME_DISPATCH,
        "csmc_evidence_status": "NOT_ACQUIRED",
    }


def _base_rows():
    common_mat = {
        "mesh_object_names": ["CONTROL_CUBE"], "mesh_data_names": ["CONTROL_CUBE_MESH"],
        "mesh_object_count": 1, "vertices_total": 8, "triangles_total": 12,
        "material_slot_names": ["CONTROL_MAT_A", "CONTROL_MAT_B", "CONTROL_MAT_C"],
        "material_slots_total": 3, "uv_layers_total": 1, "bones_total": 0,
        "weight_assignments_total": 0, "armature_object_names": [], "bone_names": [],
        "vertex_group_names": [],
    }
    common_uv = {
        "mesh_object_names": ["CONTROL_CUBE"], "mesh_data_names": ["CONTROL_CUBE_MESH"],
        "mesh_object_count": 1, "vertices_total": 8, "triangles_total": 12,
        "material_slot_names": [], "material_slots_total": 0, "used_material_indices_total": 0,
        "bones_total": 0, "weight_assignments_total": 0,
        "armature_object_names": [], "bone_names": [], "vertex_group_names": [],
    }
    common_w = {
        "mesh_object_names": ["CONTROL_CUBE"], "mesh_data_names": ["CONTROL_CUBE_MESH"],
        "mesh_object_count": 1, "vertices_total": 8, "triangles_total": 12,
        "material_slot_names": [], "material_slots_total": 0, "used_material_indices_total": 0,
        "uv_layers_total": 1, "armature_object_names": ["CONTROL_ARM"],
        "bone_names": ["BONE_001", "BONE_002"], "vertex_group_names": ["BONE_001", "BONE_002"],
        "bones_total": 2, "weight_assignments_total": 16,
    }
    return [
        dict(common_mat, fixture_id="MAT3_ALLUSED", used_material_indices_total=3),
        dict(common_mat, fixture_id="MAT3_ONEUSED", used_material_indices_total=1),
        {
            "fixture_id": "THREE_CUBES",
            "mesh_object_names": ["CONTROL_CUBE_001", "CONTROL_CUBE_002", "CONTROL_CUBE_003"],
            "mesh_data_names": ["CONTROL_CUBE_MESH_001", "CONTROL_CUBE_MESH_002", "CONTROL_CUBE_MESH_003"],
            "mesh_object_count": 3, "vertices_total": 24, "triangles_total": 36,
            "material_slot_names": [], "material_slots_total": 0, "used_material_indices_total": 0,
            "uv_layers_total": 3, "armature_object_names": [], "bone_names": [],
            "vertex_group_names": [], "bones_total": 0, "weight_assignments_total": 0,
        },
        dict(common_uv, fixture_id="UV_OFF", uv_layers_total=0),
        dict(common_uv, fixture_id="UV_ON", uv_layers_total=1),
        dict(common_w, fixture_id="W50_50", weight_histogram={"0.5": 16}),
        dict(common_w, fixture_id="W25_75", weight_histogram={"0.25": 8, "0.75": 8}),
    ]


def self_test() -> None:
    rows = _base_rows()
    out = validate_teacher_manifest(rows)
    assert out["accepted"] is True
    assert out["semantic_promotion_count"] == 0
    assert out["runtime_dispatch"] is False

    bad = [dict(x) for x in rows]; bad[0]["raw_csmc_bytes"] = "forbidden"
    assert validate_teacher_manifest(bad)["reason"] == "forbidden_raw_field"
    bad = [dict(x) for x in rows]; bad[1]["used_material_indices_total"] = 2
    assert validate_teacher_manifest(bad)["reason"] == "material_usage_discriminator_not_realized"
    bad = [dict(x) for x in rows]; bad[2]["mesh_object_count"] = 2
    assert validate_teacher_manifest(bad)["reason"] == "three_cubes_object_count_not_three"
    bad = [dict(x) for x in rows]; bad[4]["uv_layers_total"] = 0
    assert validate_teacher_manifest(bad)["reason"] == "uv_absence_presence_not_realized"
    bad = [dict(x) for x in rows]; bad[6]["weight_assignments_total"] = 15
    assert validate_teacher_manifest(bad)["reason"] == "weight_pair_assignment_count_not_sixteen"
    bad = [dict(x) for x in rows]; bad[6]["weight_histogram"] = {"0.5": 16}
    assert validate_teacher_manifest(bad)["reason"] == "weight_scalar_change_not_realized"
    bad = [dict(x) for x in rows[:-1]]
    assert validate_teacher_manifest(bad)["reason"] == "fixture_set_incomplete"
    bad = [dict(x) for x in rows]; bad[0]["vertices_total"] = -1
    assert validate_teacher_manifest(bad)["reason"] == "invalid_vertices_total"
    bad = [dict(x) for x in rows]; bad[1]["mesh_data_names"] = ["DIFFERENT_MESH"]
    assert validate_teacher_manifest(bad)["reason"] == "material_pair_identity_mismatch"
    bad = [dict(x) for x in rows]; bad[4]["mesh_data_names"] = ["DIFFERENT_MESH"]
    assert validate_teacher_manifest(bad)["reason"] == "uv_pair_identity_mismatch"
    print("SELF_TEST_PASS 12/12")


if __name__ == "__main__":
    self_test()
