#!/usr/bin/env python3
from copy import deepcopy
from csmc_analysis_c_name_literal_negative_control_c058 import BASELINE, evaluate


def test_c058_baseline() -> None:
    out = evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["classification"] == "PLAINTEXT_SOURCE_NAME_CONFOUNDER_NEGATIVE_CONTROL"
    assert out["plain_source_name_carving"] == "REJECTED_FOR_CURRENT_12_FIXTURES"
    assert out["names_absent_from_serialization"] == "NOT_PROVEN"
    assert out["name_codec_or_cipher"] == "NOT_INFERRED"
    assert out["i3_state"] == "PARTIAL_UNCHANGED"
    assert out["semantic_promotion_count"] == 0
    assert out["runtime_dispatch"] is False


def test_c058_fail_closed() -> None:
    cases = []
    bad = deepcopy(BASELINE); bad["sqlite_file_literal_occurrences_total"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); bad["teacher_identifier_count"] = 52; cases.append(bad)
    bad = deepcopy(BASELINE); bad["semantic_promotion"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["name_metadata_region_confirmed"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["runtime_dispatch"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["blender_emit_ready"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["raw_private_bytes_published"] = True; cases.append(bad)
    for candidate in cases:
        assert evaluate(candidate)["accepted"] is False
