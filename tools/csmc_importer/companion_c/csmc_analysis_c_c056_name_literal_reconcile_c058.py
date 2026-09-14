#!/usr/bin/env python3
"""C-058: reconcile C-056 localized prefix delta with name-literal negative control.

Public-safe aggregate metadata only. This rejects only the narrow explanation that
the localized F06/F07 12-qword differential is caused by direct plaintext copies
of known teacher identifiers in the tested encodings/surfaces. It does not claim
that identity/name metadata is absent, and it does not bind material/object semantics.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Mapping

PIPELINE_STAGE = "STRUCTURAL_ONLY"
CLASSIFICATION = "C056_PREFIX_PLAINTEXT_NAME_EXPLANATION_REJECTED"

BASELINE = {
    "pipeline_stage": PIPELINE_STAGE,
    "semantic_promotion_count": 0,
    "blender_emit_ready": False,
    "runtime_dispatch": False,
    "raw_private_bytes_published": False,
    "c056": {
        "accepted": True,
        "classification": "PHASE_LOCALIZED_RESIDUAL_DIFFERENTIAL_CANDIDATE",
        "fixture_a": "CSMC_F06_CUBE_MAT2",
        "fixture_b": "CSMC_F07_TWO_CUBES",
        "localized_delta_qwords": 12,
        "semantic_binding": "UNRESOLVED",
        "i3_valid": False,
    },
    "name_literal_probe": {
        "source_fixture_sha256": "be6132ef83959167ffd19218810e099f0bd164714fbd1ec4770f9296b38643b6",
        "fixture_count": 12,
        "teacher_identifier_count": 53,
        "encodings": ["ascii", "utf-16le", "utf-16be"],
        "search_surfaces": ["sqlite_file_bytes", "character_blob_bytes"],
        "literal_searches_total": 318,
        "sqlite_file_literal_occurrences_total": 0,
        "character_blob_literal_occurrences_total": 0,
        "name_metadata_region_confirmed": False,
        "fixtures": {
            "CSMC_F06_CUBE_MAT2": {
                "teacher_identifier_count": 4,
                "sqlite_file_literal_occurrences": 0,
                "character_blob_literal_occurrences": 0,
            },
            "CSMC_F07_TWO_CUBES": {
                "teacher_identifier_count": 5,
                "sqlite_file_literal_occurrences": 0,
                "character_blob_literal_occurrences": 0,
            },
        },
    },
}


def _nonneg_int(value: Any) -> bool:
    return type(value) is int and value >= 0


def evaluate(row: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(row, Mapping):
        return {"accepted": False, "classification": "REJECTED", "errors": ["input_not_mapping"]}

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

    c056 = row.get("c056")
    probe = row.get("name_literal_probe")
    if not isinstance(c056, Mapping) or not isinstance(probe, Mapping):
        errors.append("missing_source_sections")
        return {"accepted": False, "classification": "REJECTED", "errors": errors}

    if c056.get("accepted") is not True:
        errors.append("c056_not_accepted")
    if c056.get("classification") != "PHASE_LOCALIZED_RESIDUAL_DIFFERENTIAL_CANDIDATE":
        errors.append("wrong_c056_classification")
    if c056.get("fixture_a") != "CSMC_F06_CUBE_MAT2" or c056.get("fixture_b") != "CSMC_F07_TWO_CUBES":
        errors.append("wrong_c056_fixture_pair")
    if c056.get("localized_delta_qwords") != 12:
        errors.append("wrong_c056_localized_delta")
    if c056.get("semantic_binding") != "UNRESOLVED":
        errors.append("c056_semantic_binding_overclaimed")
    if c056.get("i3_valid") is not False:
        errors.append("c056_i3_must_remain_false")

    for key in ("fixture_count", "teacher_identifier_count", "literal_searches_total",
                "sqlite_file_literal_occurrences_total", "character_blob_literal_occurrences_total"):
        if not _nonneg_int(probe.get(key)):
            errors.append(f"invalid_{key}")
    if probe.get("fixture_count") != 12:
        errors.append("unexpected_fixture_count")
    if probe.get("teacher_identifier_count") != 53:
        errors.append("unexpected_teacher_identifier_count")
    if probe.get("literal_searches_total") != 318:
        errors.append("unexpected_literal_search_total")

    encodings = probe.get("encodings")
    surfaces = probe.get("search_surfaces")
    if not isinstance(encodings, list) or not {"ascii", "utf-16le", "utf-16be"}.issubset(set(encodings)):
        errors.append("required_encodings_missing")
    if not isinstance(surfaces, list) or not {"sqlite_file_bytes", "character_blob_bytes"}.issubset(set(surfaces)):
        errors.append("required_search_surfaces_missing")
    if probe.get("sqlite_file_literal_occurrences_total") != 0:
        errors.append("sqlite_literal_occurrence_nonzero")
    if probe.get("character_blob_literal_occurrences_total") != 0:
        errors.append("character_blob_literal_occurrence_nonzero")
    if probe.get("name_metadata_region_confirmed") is not False:
        errors.append("name_metadata_region_must_remain_unconfirmed")

    fixtures = probe.get("fixtures")
    if not isinstance(fixtures, Mapping):
        errors.append("fixture_details_missing")
    else:
        for fid, expected_ids in (("CSMC_F06_CUBE_MAT2", 4), ("CSMC_F07_TWO_CUBES", 5)):
            item = fixtures.get(fid)
            if not isinstance(item, Mapping):
                errors.append(f"{fid}_missing")
                continue
            if item.get("teacher_identifier_count") != expected_ids:
                errors.append(f"{fid}_teacher_identifier_count_mismatch")
            if item.get("sqlite_file_literal_occurrences") != 0:
                errors.append(f"{fid}_sqlite_literal_occurrence_nonzero")
            if item.get("character_blob_literal_occurrences") != 0:
                errors.append(f"{fid}_character_blob_literal_occurrence_nonzero")

    if errors:
        return {"accepted": False, "classification": "REJECTED", "errors": errors}

    return {
        "accepted": True,
        "classification": CLASSIFICATION,
        "localized_pair": ["CSMC_F06_CUBE_MAT2", "CSMC_F07_TWO_CUBES"],
        "localized_delta_qwords": 12,
        "plaintext_known_identifier_explanation": "REJECTED_WITHIN_TESTED_ENCODINGS_AND_SURFACES",
        "tested_encodings": ["ascii", "utf-16le", "utf-16be"],
        "tested_surfaces": ["sqlite_file_bytes", "character_blob_bytes"],
        "transformed_or_remapped_identity_confounder": "OPEN",
        "modeler_generated_identity_confounder": "OPEN",
        "non_name_structural_explanation": "OPEN",
        "material_semantic_binding": "UNRESOLVED",
        "object_semantic_binding": "UNRESOLVED",
        "owner_consumer_binding": "UNRESOLVED",
        "i3_valid": False,
        "semantic_promotion": False,
        "blender_emit_ready": False,
        "runtime_dispatch": False,
    }


def self_test() -> None:
    out = evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["plaintext_known_identifier_explanation"] == "REJECTED_WITHIN_TESTED_ENCODINGS_AND_SURFACES"
    assert out["transformed_or_remapped_identity_confounder"] == "OPEN"
    assert out["semantic_promotion"] is False

    cases = []
    bad = deepcopy(BASELINE); bad["name_literal_probe"]["fixtures"]["CSMC_F06_CUBE_MAT2"]["character_blob_literal_occurrences"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); bad["name_literal_probe"]["sqlite_file_literal_occurrences_total"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); del bad["name_literal_probe"]["fixtures"]["CSMC_F07_TWO_CUBES"]; cases.append(bad)
    bad = deepcopy(BASELINE); bad["name_literal_probe"]["name_metadata_region_confirmed"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["c056"]["localized_delta_qwords"] = 13; cases.append(bad)
    bad = deepcopy(BASELINE); bad["semantic_promotion_count"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); bad["blender_emit_ready"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["runtime_dispatch"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["raw_private_bytes_published"] = True; cases.append(bad)

    for candidate in cases:
        assert evaluate(candidate)["accepted"] is False

    print("C058_SELF_TEST_PASS 10/10")


if __name__ == "__main__":
    self_test()
