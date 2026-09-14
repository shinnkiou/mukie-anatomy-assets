#!/usr/bin/env python3
from csmc_pair_invariant_evidence import PairInvariantEvidence
from csmc_pair_search_mask import build_search_mask


def make_evidence(**overrides):
    data = dict(
        evidence_id="E1",
        corpus_sha256="a" * 64,
        fixture_a="A",
        fixture_b="B",
        fixture_a_sha256="b" * 64,
        fixture_b_sha256="c" * 64,
        logical_mod8_a=7,
        logical_mod8_b=7,
        qword_count_a=10,
        qword_count_b=12,
        invariant_start_a=3,
        invariant_start_b=5,
        invariant_length_qwords=6,
        trailing_qwords_a=1,
        trailing_qwords_b=1,
    )
    data.update(overrides)
    return PairInvariantEvidence(**data)


def test_mask():
    out = build_search_mask(make_evidence())
    assert out["fixture_a_mask"]["include_candidate_regions_qwords"] == [[0, 3], [9, 10]]
    assert out["fixture_b_mask"]["include_candidate_regions_qwords"] == [[0, 5], [11, 12]]
    assert out["fixture_a_mask"]["exclude_exact_invariant_region_qwords"] == [3, 9]
    assert out["semantic_promotion"] is False
    assert out["raw_values_embedded"] is False
    assert out["blender_emit_ready"] is False


def test_reject_bad_bounds():
    try:
        build_search_mask(make_evidence(invariant_start_a=4))
    except ValueError:
        pass
    else:
        raise AssertionError("invalid evidence accepted")


def main():
    test_mask()
    test_reject_bad_bounds()
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
