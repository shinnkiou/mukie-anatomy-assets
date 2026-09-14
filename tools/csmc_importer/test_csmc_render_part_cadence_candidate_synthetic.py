#!/usr/bin/env python3
from csmc_render_part_cadence_candidate import build_level4_candidate, semantic_gate_summary


def test_level4_candidate_is_fail_closed():
    e = build_level4_candidate(
        relationship_holds_count=13,
        full_match_lags=(307,),
        robustness_pass_count=35,
        robustness_total_count=35,
    )
    s = semantic_gate_summary(e)
    assert e.confidence_level == 4
    assert e.validation_status == "I3_PARTIAL"
    assert e.semantic_promotion is False
    assert s["semantic_status"] == "CANDIDATE_ONLY"
    assert s["confirmed"] is False
    assert s["blender_emit_ready"] is False


def test_nonunique_lag_is_rejected():
    try:
        build_level4_candidate(
            relationship_holds_count=13,
            full_match_lags=(306, 307),
            robustness_pass_count=35,
            robustness_total_count=35,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("non-unique lag accepted")


def test_partial_fixture_support_is_rejected():
    try:
        build_level4_candidate(
            relationship_holds_count=12,
            full_match_lags=(307,),
            robustness_pass_count=35,
            robustness_total_count=35,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("partial controlled relation accepted as Level 4")


def main():
    test_level4_candidate_is_fail_closed()
    test_nonunique_lag_is_rejected()
    test_partial_fixture_support_is_rejected()
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
