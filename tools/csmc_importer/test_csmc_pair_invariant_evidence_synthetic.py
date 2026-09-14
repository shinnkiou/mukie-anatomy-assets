#!/usr/bin/env python3
from csmc_pair_invariant_evidence import PairInvariantEvidence, validate_pair_invariant

SHA_A = "a" * 64
SHA_B = "b" * 64
CORPUS = "c" * 64


def good() -> PairInvariantEvidence:
    return PairInvariantEvidence(
        evidence_id="PAIR_F02_F04_PHASE7",
        corpus_sha256=CORPUS,
        fixture_a="CSMC_F02_QUAD",
        fixture_b="CSMC_F04_CUBE_SUBDIV",
        fixture_a_sha256=SHA_A,
        fixture_b_sha256=SHA_B,
        logical_mod8_a=7,
        logical_mod8_b=7,
        qword_count_a=2212,
        qword_count_b=2320,
        invariant_start_a=402,
        invariant_start_b=510,
        invariant_length_qwords=1809,
        trailing_qwords_a=1,
        trailing_qwords_b=1,
    )


def test_good():
    e = good()
    assert validate_pair_invariant(e) == []
    d = e.to_dict()
    assert d["schema_version"] == "csmc_pair_invariant_evidence_v0_1"
    assert d["semantic_promotion"] is False
    assert d["raw_values_embedded"] is False
    assert d["blender_emit_ready"] is False


def test_reject_different_phase():
    e = good()
    bad = PairInvariantEvidence(**{**e.__dict__, "logical_mod8_b": 6})
    assert any("equal logical_mod8" in x for x in validate_pair_invariant(bad))


def test_reject_bad_bounds():
    e = good()
    bad = PairInvariantEvidence(**{**e.__dict__, "invariant_length_qwords": 1808})
    errs = validate_pair_invariant(bad)
    assert any("bounds" in x for x in errs)


def test_reject_promotion_and_raw():
    e = good()
    bad = PairInvariantEvidence(**{
        **e.__dict__,
        "semantic_promotion": True,
        "raw_values_embedded": True,
        "blender_emit_ready": True,
    })
    errs = validate_pair_invariant(bad)
    assert any("promote" in x for x in errs)
    assert any("raw_values" in x for x in errs)
    assert any("blender_emit" in x for x in errs)


def main():
    test_good()
    test_reject_different_phase()
    test_reject_bad_bounds()
    test_reject_promotion_and_raw()
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
