#!/usr/bin/env python3
"""C-058: reference-only reconciliation of the mainline name-literal negative control.

Consumes only public-safe aggregate counts/flags. It does not read CSMC bytes and
cannot promote NAME_METADATA or any other semantic slot.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Mapping

PIPELINE_STAGE = "STRUCTURAL_ONLY"
INTERPRETATION = "SOURCE_IDENTIFIER_PLAINTEXT_ASCII_UTF16_NOT_OBSERVED"
CLASSIFICATION = "PLAINTEXT_SOURCE_NAME_CONFOUNDER_NEGATIVE_CONTROL"

BASELINE = {
    "fixture_count": 12,
    "teacher_identifier_count": 53,
    "encoding_count": 3,
    "encodings": ["ascii", "utf-16le", "utf-16be"],
    "search_surfaces": ["sqlite_file_bytes", "character_blob_bytes"],
    "literal_searches_per_surface": 159,
    "literal_searches_total": 318,
    "sqlite_file_literal_occurrences_total": 0,
    "character_blob_literal_occurrences_total": 0,
    "interpretation": INTERPRETATION,
    "semantic_promotion": False,
    "name_metadata_region_confirmed": False,
    "raw_values_embedded": False,
    "pipeline_stage": PIPELINE_STAGE,
    "semantic_promotion_count": 0,
    "blender_emit_ready": False,
    "runtime_dispatch": False,
    "raw_private_bytes_published": False,
}

def _exact_int(row: Mapping[str, Any], key: str, expected: int, errors: list[str]) -> None:
    value = row.get(key)
    if type(value) is not int or value != expected:
        errors.append(f"{key}_mismatch")

def evaluate(row: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"accepted": False, "errors": ["input_not_mapping"], "classification": "REJECTED"}
    errors: list[str] = []
    for key, expected in (
        ("fixture_count", 12),
        ("teacher_identifier_count", 53),
        ("encoding_count", 3),
        ("literal_searches_per_surface", 159),
        ("literal_searches_total", 318),
        ("sqlite_file_literal_occurrences_total", 0),
        ("character_blob_literal_occurrences_total", 0),
        ("semantic_promotion_count", 0),
    ):
        _exact_int(row, key, expected, errors)
    if row.get("encodings") != ["ascii", "utf-16le", "utf-16be"]:
        errors.append("encoding_set_mismatch")
    if row.get("search_surfaces") != ["sqlite_file_bytes", "character_blob_bytes"]:
        errors.append("search_surfaces_mismatch")
    if row.get("interpretation") != INTERPRETATION:
        errors.append("interpretation_mismatch")
    for key in (
        "semantic_promotion",
        "name_metadata_region_confirmed",
        "raw_values_embedded",
        "blender_emit_ready",
        "runtime_dispatch",
        "raw_private_bytes_published",
    ):
        if row.get(key) is not False:
            errors.append(f"{key}_must_be_false")
    if row.get("pipeline_stage") != PIPELINE_STAGE:
        errors.append("pipeline_not_structural_only")
    if errors:
        return {"accepted": False, "errors": errors, "classification": "REJECTED"}
    return {
        "accepted": True,
        "errors": [],
        "classification": CLASSIFICATION,
        "observed": INTERPRETATION,
        "plain_source_name_carving": "REJECTED_FOR_CURRENT_12_FIXTURES",
        "names_absent_from_serialization": "NOT_PROVEN",
        "name_codec_or_cipher": "NOT_INFERRED",
        "random_printable_runs_as_name_metadata": "FORBIDDEN_WITHOUT_RELATIONSHIP_EVIDENCE",
        "i3_state": "PARTIAL_UNCHANGED",
        "semantic_binding": "UNRESOLVED",
        "semantic_promotion_count": 0,
        "blender_emit_ready": False,
        "runtime_dispatch": False,
    }

def self_test() -> None:
    out = evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["names_absent_from_serialization"] == "NOT_PROVEN"
    assert out["i3_state"] == "PARTIAL_UNCHANGED"
    cases = []
    bad = deepcopy(BASELINE); bad["sqlite_file_literal_occurrences_total"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); bad["teacher_identifier_count"] = 52; cases.append(bad)
    bad = deepcopy(BASELINE); bad["encodings"] = ["ascii"]; cases.append(bad)
    bad = deepcopy(BASELINE); bad["semantic_promotion"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["name_metadata_region_confirmed"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["raw_values_embedded"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["pipeline_stage"] = "SEMANTIC"; cases.append(bad)
    bad = deepcopy(BASELINE); bad["runtime_dispatch"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["blender_emit_ready"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["raw_private_bytes_published"] = True; cases.append(bad)
    for candidate in cases:
        assert evaluate(candidate)["accepted"] is False
    print("C058_SELF_TEST_PASS 11/11")

if __name__ == "__main__":
    self_test()
