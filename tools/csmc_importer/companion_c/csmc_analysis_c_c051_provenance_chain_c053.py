#!/usr/bin/env python3
"""C-053: end-to-end provenance continuity gate for C-051/C-052 controlled fixtures.

Binds public-safe Blender source hashes and teacher-row fingerprints to external
CSMC container hashes and then to aggregate-only structural observations.

No raw CSMC bytes, MODELER/runtime dispatch, mainline mutation, or semantic promotion.
"""
from __future__ import annotations
from hashlib import sha256
from typing import Any, Mapping
import json
import re

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

FORBIDDEN_FIELDS = {
    "raw_csmc_bytes", "csmc_payload", "csmc_blob", "raw_payload",
    "raw_blend_bytes", "binary_blob", "payload_base64",
}

HEX64 = re.compile(r"^[0-9a-f]{64}$")

TEACHER_FINGERPRINT_FIELDS = (
    "fixture_id",
    "source_blend_filename",
    "source_blend_sha256",
    "mesh_object_names",
    "mesh_data_names",
    "mesh_object_count",
    "vertices_total",
    "triangles_total",
    "material_slot_names",
    "material_slots_total",
    "used_material_indices_total",
    "uv_layers_total",
    "armature_object_names",
    "bone_names",
    "bones_total",
    "vertex_group_names",
    "weight_assignments_total",
    "weight_histogram",
)


def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def teacher_row_fingerprint(row: Mapping[str, Any]) -> str:
    payload = {k: row.get(k) for k in TEACHER_FINGERPRINT_FIELDS}
    return sha256(_canonical_json(payload)).hexdigest()


def _is_hex64(v: Any) -> bool:
    return isinstance(v, str) and HEX64.fullmatch(v) is not None


def _reject_forbidden(row: Mapping[str, Any]) -> dict | None:
    hit = sorted(FORBIDDEN_FIELDS.intersection(row))
    if hit:
        return {"accepted": False, "reason": "forbidden_raw_field", "fields": hit}
    return None


def _framed(logical: int) -> int:
    return ((logical + 7) // 8) * 8 + 8


def validate_teacher_provenance(rows: list[Mapping[str, Any]]) -> dict:
    if not isinstance(rows, list) or not rows:
        return {"accepted": False, "reason": "teacher_rows_missing"}
    by_id: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            return {"accepted": False, "reason": "teacher_row_not_mapping"}
        bad = _reject_forbidden(row)
        if bad:
            return bad
        fixture_id = row.get("fixture_id")
        if fixture_id not in REQUIRED_IDS:
            return {"accepted": False, "reason": "unknown_fixture", "fixture_id": fixture_id}
        if fixture_id in by_id:
            return {"accepted": False, "reason": "duplicate_teacher_fixture", "fixture_id": fixture_id}
        if not _is_hex64(row.get("source_blend_sha256")):
            return {"accepted": False, "reason": "invalid_source_blend_sha256", "fixture_id": fixture_id}
        expected_fp = teacher_row_fingerprint(row)
        if row.get("teacher_row_sha256") != expected_fp:
            return {
                "accepted": False,
                "reason": "teacher_row_fingerprint_mismatch",
                "fixture_id": fixture_id,
            }
        by_id[fixture_id] = row
    if set(by_id) != REQUIRED_IDS:
        return {
            "accepted": False,
            "reason": "teacher_fixture_set_incomplete",
            "missing": sorted(REQUIRED_IDS - set(by_id)),
            "unexpected": sorted(set(by_id) - REQUIRED_IDS),
        }
    return {
        "accepted": True,
        "teacher_fixture_count": len(by_id),
        "teacher_bindings": {
            fixture_id: {
                "source_blend_sha256": row["source_blend_sha256"],
                "teacher_row_sha256": row["teacher_row_sha256"],
            }
            for fixture_id, row in sorted(by_id.items())
        },
        "pipeline_stage": PIPELINE_STAGE,
        "semantic_promotion_count": SEMANTIC_PROMOTION_COUNT,
        "blender_emit_ready": BLENDER_EMIT_READY,
        "runtime_dispatch": RUNTIME_DISPATCH,
    }


def validate_conversion_manifest(
    teacher_rows: list[Mapping[str, Any]],
    conversion_rows: list[Mapping[str, Any]],
) -> dict:
    teacher = validate_teacher_provenance(teacher_rows)
    if not teacher.get("accepted"):
        return {"accepted": False, "reason": "teacher_provenance_rejected", "detail": teacher}
    if not isinstance(conversion_rows, list) or not conversion_rows:
        return {"accepted": False, "reason": "conversion_rows_missing"}

    bindings = teacher["teacher_bindings"]
    by_id: dict[str, Mapping[str, Any]] = {}
    for row in conversion_rows:
        if not isinstance(row, Mapping):
            return {"accepted": False, "reason": "conversion_row_not_mapping"}
        bad = _reject_forbidden(row)
        if bad:
            return bad
        fixture_id = row.get("fixture_id")
        if fixture_id not in REQUIRED_IDS:
            return {"accepted": False, "reason": "unknown_conversion_fixture", "fixture_id": fixture_id}
        if fixture_id in by_id:
            return {"accepted": False, "reason": "duplicate_conversion_fixture", "fixture_id": fixture_id}
        if row.get("source_blend_sha256") != bindings[fixture_id]["source_blend_sha256"]:
            return {"accepted": False, "reason": "source_blend_hash_mismatch", "fixture_id": fixture_id}
        if row.get("teacher_row_sha256") != bindings[fixture_id]["teacher_row_sha256"]:
            return {"accepted": False, "reason": "teacher_binding_mismatch", "fixture_id": fixture_id}
        if not _is_hex64(row.get("csmc_container_sha256")):
            return {"accepted": False, "reason": "invalid_csmc_container_sha256", "fixture_id": fixture_id}
        converter = row.get("converter_id")
        if not isinstance(converter, str) or not converter.strip():
            return {"accepted": False, "reason": "converter_id_missing", "fixture_id": fixture_id}
        by_id[fixture_id] = row

    if set(by_id) != REQUIRED_IDS:
        return {
            "accepted": False,
            "reason": "conversion_fixture_set_incomplete",
            "missing": sorted(REQUIRED_IDS - set(by_id)),
            "unexpected": sorted(set(by_id) - REQUIRED_IDS),
        }

    return {
        "accepted": True,
        "fixture_count": len(by_id),
        "conversion_bindings": {
            fixture_id: {
                "source_blend_sha256": row["source_blend_sha256"],
                "teacher_row_sha256": row["teacher_row_sha256"],
                "csmc_container_sha256": row["csmc_container_sha256"],
            }
            for fixture_id, row in sorted(by_id.items())
        },
        "provenance_continuity": "SOURCE_BLEND_HASH_AND_TEACHER_ROW_HASH_BOUND",
        "pipeline_stage": PIPELINE_STAGE,
        "semantic_promotion_count": SEMANTIC_PROMOTION_COUNT,
        "blender_emit_ready": BLENDER_EMIT_READY,
        "runtime_dispatch": RUNTIME_DISPATCH,
    }


def validate_analysis_manifest(
    teacher_rows: list[Mapping[str, Any]],
    conversion_rows: list[Mapping[str, Any]],
    analysis_rows: list[Mapping[str, Any]],
) -> dict:
    conversion = validate_conversion_manifest(teacher_rows, conversion_rows)
    if not conversion.get("accepted"):
        return {"accepted": False, "reason": "conversion_manifest_rejected", "detail": conversion}
    if not isinstance(analysis_rows, list) or not analysis_rows:
        return {"accepted": False, "reason": "analysis_rows_missing"}

    bindings = conversion["conversion_bindings"]
    by_id: dict[str, Mapping[str, Any]] = {}
    for row in analysis_rows:
        if not isinstance(row, Mapping):
            return {"accepted": False, "reason": "analysis_row_not_mapping"}
        bad = _reject_forbidden(row)
        if bad:
            return bad
        fixture_id = row.get("fixture_id")
        if fixture_id not in REQUIRED_IDS:
            return {"accepted": False, "reason": "unknown_analysis_fixture", "fixture_id": fixture_id}
        if fixture_id in by_id:
            return {"accepted": False, "reason": "duplicate_analysis_fixture", "fixture_id": fixture_id}

        binding = bindings[fixture_id]
        for field in ("source_blend_sha256", "teacher_row_sha256", "csmc_container_sha256"):
            if row.get(field) != binding[field]:
                return {"accepted": False, "reason": f"{field}_analysis_binding_mismatch", "fixture_id": fixture_id}

        for field in ("logical_length", "stored_length", "cadence_count"):
            if type(row.get(field)) is not int or row[field] < 0:
                return {"accepted": False, "reason": f"invalid_{field}", "fixture_id": fixture_id}
        if row["stored_length"] != _framed(row["logical_length"]):
            return {"accepted": False, "reason": "outer_framing_rule_failed", "fixture_id": fixture_id}
        by_id[fixture_id] = row

    if set(by_id) != REQUIRED_IDS:
        return {
            "accepted": False,
            "reason": "analysis_fixture_set_incomplete",
            "missing": sorted(REQUIRED_IDS - set(by_id)),
            "unexpected": sorted(set(by_id) - REQUIRED_IDS),
        }

    return {
        "accepted": True,
        "fixture_count": len(by_id),
        "provenance_chain": "BLEND_SHA256->TEACHER_ROW_SHA256->CSMC_SHA256->AGGREGATE_OBSERVATION",
        "outer_framing_validated": True,
        "semantic_claim": "NONE",
        "pipeline_stage": PIPELINE_STAGE,
        "semantic_promotion_count": SEMANTIC_PROMOTION_COUNT,
        "blender_emit_ready": BLENDER_EMIT_READY,
        "runtime_dispatch": RUNTIME_DISPATCH,
    }


def _hash(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


def _teacher_rows() -> list[dict]:
    rows = []
    for fixture_id in sorted(REQUIRED_IDS):
        row = {
            "fixture_id": fixture_id,
            "source_blend_filename": f"CSMC_C051_{fixture_id}.blend",
            "source_blend_sha256": _hash(f"blend:{fixture_id}"),
            "mesh_object_names": ["CONTROL_CUBE"],
            "mesh_data_names": ["CONTROL_CUBE_MESH"],
            "mesh_object_count": 1,
            "vertices_total": 8,
            "triangles_total": 12,
            "material_slot_names": [],
            "material_slots_total": 0,
            "used_material_indices_total": 0,
            "uv_layers_total": 0,
            "armature_object_names": [],
            "bone_names": [],
            "bones_total": 0,
            "vertex_group_names": [],
            "weight_assignments_total": 0,
            "weight_histogram": {},
        }
        row["teacher_row_sha256"] = teacher_row_fingerprint(row)
        rows.append(row)
    return rows


def _conversion_rows(teacher_rows: list[Mapping[str, Any]]) -> list[dict]:
    return [
        {
            "fixture_id": row["fixture_id"],
            "source_blend_sha256": row["source_blend_sha256"],
            "teacher_row_sha256": row["teacher_row_sha256"],
            "csmc_container_sha256": _hash(f"csmc:{row['fixture_id']}"),
            "converter_id": "EXTERNAL_AUTHORIZED_CONVERTER",
        }
        for row in teacher_rows
    ]


def _analysis_rows(teacher_rows: list[Mapping[str, Any]], conversion_rows: list[Mapping[str, Any]]) -> list[dict]:
    c_by_id = {row["fixture_id"]: row for row in conversion_rows}
    rows = []
    for n, teacher in enumerate(teacher_rows):
        fixture_id = teacher["fixture_id"]
        logical = 18000 + n * 17
        rows.append({
            "fixture_id": fixture_id,
            "source_blend_sha256": teacher["source_blend_sha256"],
            "teacher_row_sha256": teacher["teacher_row_sha256"],
            "csmc_container_sha256": c_by_id[fixture_id]["csmc_container_sha256"],
            "logical_length": logical,
            "stored_length": _framed(logical),
            "cadence_count": 3,
        })
    return rows


def self_test() -> None:
    teachers = _teacher_rows()
    conversions = _conversion_rows(teachers)
    analyses = _analysis_rows(teachers, conversions)

    assert validate_teacher_provenance(teachers)["accepted"] is True
    assert validate_conversion_manifest(teachers, conversions)["accepted"] is True
    out = validate_analysis_manifest(teachers, conversions, analyses)
    assert out["accepted"] is True
    assert out["semantic_promotion_count"] == 0
    assert out["runtime_dispatch"] is False

    bad = [dict(x) for x in teachers]
    bad[0]["source_blend_sha256"] = "nope"
    assert validate_teacher_provenance(bad)["reason"] == "invalid_source_blend_sha256"

    bad = [dict(x) for x in teachers]
    bad[0]["vertices_total"] += 1
    assert validate_teacher_provenance(bad)["reason"] == "teacher_row_fingerprint_mismatch"

    bad = [dict(x) for x in teachers]
    bad[0]["raw_blend_bytes"] = "forbidden"
    assert validate_teacher_provenance(bad)["reason"] == "forbidden_raw_field"

    bad = [dict(x) for x in conversions]
    bad[0]["source_blend_sha256"] = _hash("other-source")
    assert validate_conversion_manifest(teachers, bad)["reason"] == "source_blend_hash_mismatch"

    bad = [dict(x) for x in conversions]
    bad[0]["teacher_row_sha256"] = _hash("other-teacher-row")
    assert validate_conversion_manifest(teachers, bad)["reason"] == "teacher_binding_mismatch"

    bad = [dict(x) for x in conversions]
    bad[0]["csmc_container_sha256"] = "bad"
    assert validate_conversion_manifest(teachers, bad)["reason"] == "invalid_csmc_container_sha256"

    bad = [dict(x) for x in conversions]
    bad[0]["converter_id"] = ""
    assert validate_conversion_manifest(teachers, bad)["reason"] == "converter_id_missing"

    bad = [dict(x) for x in analyses]
    bad[0]["csmc_container_sha256"] = _hash("wrong-csmc")
    assert validate_analysis_manifest(teachers, conversions, bad)["reason"] == "csmc_container_sha256_analysis_binding_mismatch"

    bad = [dict(x) for x in analyses]
    bad[0]["stored_length"] += 8
    assert validate_analysis_manifest(teachers, conversions, bad)["reason"] == "outer_framing_rule_failed"

    bad = [dict(x) for x in analyses]
    bad[0]["raw_csmc_bytes"] = "forbidden"
    assert validate_analysis_manifest(teachers, conversions, bad)["reason"] == "forbidden_raw_field"

    bad = [dict(x) for x in analyses[:-1]]
    assert validate_analysis_manifest(teachers, conversions, bad)["reason"] == "analysis_fixture_set_incomplete"

    print("SELF_TEST_PASS 17/17")


if __name__ == "__main__":
    self_test()
