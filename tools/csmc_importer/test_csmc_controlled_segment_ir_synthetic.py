#!/usr/bin/env python3
from csmc_pair_invariant_evidence import PairInvariantEvidence
from csmc_controlled_segment_ir import build_segment_ir


def evidence(*, start_a=10, start_b=20, length=30, trail_a=2, trail_b=2):
    return PairInvariantEvidence(
        evidence_id="SYNTH_PAIR",
        corpus_sha256="a"*64,
        fixture_a="A",
        fixture_b="B",
        fixture_a_sha256="b"*64,
        fixture_b_sha256="c"*64,
        logical_mod8_a=3,
        logical_mod8_b=3,
        qword_count_a=start_a+length+trail_a,
        qword_count_b=start_b+length+trail_b,
        invariant_start_a=start_a,
        invariant_start_b=start_b,
        invariant_length_qwords=length,
        trailing_qwords_a=trail_a,
        trailing_qwords_b=trail_b,
    )


def test_segments_close_exactly():
    out=build_segment_ir(evidence())
    assert out["schema_version"]=="csmc_controlled_segment_ir_v0_1"
    assert out["fixture_a"]["segments"][0]["range_qwords"]==[0,10]
    assert out["fixture_a"]["segments"][1]["range_qwords"]==[10,40]
    assert out["fixture_a"]["segments"][2]["range_qwords"]==[40,42]
    assert out["fixture_b"]["segments"][0]["range_qwords"]==[0,20]
    assert out["fixture_b"]["segments"][1]["range_qwords"]==[20,50]
    assert out["fixture_b"]["segments"][2]["range_qwords"]==[50,52]
    assert out["semantic_promotion"] is False
    assert out["blender_emit_ready"] is False
    assert out["semantic_confidence_level"] == 0


def test_zero_terminal_remainder_is_allowed():
    out=build_segment_ir(evidence(trail_a=0,trail_b=0))
    assert out["fixture_a"]["segments"][2]["length_qwords"]==0
    assert out["fixture_b"]["segments"][2]["length_qwords"]==0


def main():
    test_segments_close_exactly()
    test_zero_terminal_remainder_is_allowed()
    print("SELF_TEST_PASS")


if __name__=="__main__":
    main()
