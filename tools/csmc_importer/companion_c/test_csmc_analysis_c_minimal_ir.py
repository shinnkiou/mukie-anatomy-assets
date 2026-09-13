import copy

import pytest

from csmc_analysis_c_minimal_ir import build_ir, validate_ir


def _fixtures():
    boundary = {
        "boundaries": {
            "B0": {
                "class": "LOCAL_EXTINCTION_CANDIDATE",
                "cross_serialization_survival_distinct": 0,
                "net_relative_size_change_bytes": -16,
                "new_delta_barrier_match_density": 0.0,
                "old_delta_barrier_match_density": 0.0,
            }
        }
    }
    families = {
        "families": [
            {"length_blocks": 48, "signature": "0000111", "count": 3},
            {"length_blocks": 49, "signature": "0000111", "count": 3},
        ],
        "recommended_ir_axes": ["length_blocks", "preserve_signature"],
    }
    control = {
        "fixed_different_relative_blocks": [22, 23],
        "fixed_equal_relative_blocks": [25, 26],
        "conditional_relative_blocks": [21, 24, 27],
    }
    return boundary, families, control


def test_valid_semantics_free_ir():
    ir = build_ir(*_fixtures())
    validate_ir(ir)
    assert ir["semantic_slots"]["geometry"]["status"] == "UNRESOLVED"
    assert ir["structural_grammar"]["record_family_axes"] == ["length_blocks", "preserve_signature"]


def test_confirmed_semantic_requires_evidence():
    ir = build_ir(*_fixtures())
    bad = copy.deepcopy(ir)
    bad["semantic_slots"]["geometry"]["status"] = "CONFIRMED"
    bad["semantic_slots"]["geometry"]["confidence"] = 1.0
    with pytest.raises(ValueError, match="lacks evidence"):
        validate_ir(bad)


def test_raw_payload_flag_is_forbidden():
    ir = build_ir(*_fixtures())
    bad = copy.deepcopy(ir)
    bad["parser_contract"]["raw_payload_bytes_embedded"] = True
    with pytest.raises(ValueError, match="raw payload bytes"):
        validate_ir(bad)
