#!/usr/bin/env python3
from csmc_controlled_evidence_ir import ControlledEvidence, validate_evidence

H="a"*64

def make(**kw):
    base=dict(
        evidence_id="E1",
        evidence_source="controlled_fixture_corpus",
        controlled_fixture_ids=("F03","F05"),
        relationship_type="uv_layout",
        negative_control_ids=(),
        independent_validation_ids=(),
        supporting_relationship_ids=("PAIR_F03_F05",),
        candidate_semantic="uv",
        confidence_level=2,
        validation_status="I3_PARTIAL",
        source_sha256=(H,H),
        counterexample_count=0,
        semantic_promotion=False,
    )
    base.update(kw)
    return ControlledEvidence(**base)


def test_partial_candidate_allowed_without_promotion():
    assert validate_evidence(make())==[]


def test_false_semantic_promotion_rejected():
    errors=validate_evidence(make(semantic_promotion=True))
    assert any("confidence level 5" in x for x in errors)
    assert any("I3_VALID" in x for x in errors)
    assert any("negative control" in x for x in errors)
    assert any("independent validation" in x for x in errors)
    assert any("two supporting" in x for x in errors)


def test_level5_requires_full_ladder():
    errors=validate_evidence(make(confidence_level=5, validation_status="I3_VALID", semantic_promotion=True))
    assert any("negative control" in x for x in errors)
    assert any("independent validation" in x for x in errors)


def test_level5_full_contract_accepts():
    e=make(
        confidence_level=5,
        validation_status="I3_VALID",
        negative_control_ids=("NEG01",),
        independent_validation_ids=("VROID01",),
        supporting_relationship_ids=("PAIR01","PAIR02"),
        counterexample_count=0,
        semantic_promotion=True,
    )
    assert validate_evidence(e)==[]


def test_counterexample_blocks_promotion():
    e=make(
        confidence_level=5,
        validation_status="I3_VALID",
        negative_control_ids=("NEG01",),
        independent_validation_ids=("VROID01",),
        supporting_relationship_ids=("PAIR01","PAIR02"),
        counterexample_count=1,
        semantic_promotion=True,
    )
    assert any("zero counterexamples" in x for x in validate_evidence(e))


def main():
    test_partial_candidate_allowed_without_promotion()
    test_false_semantic_promotion_rejected()
    test_level5_requires_full_ladder()
    test_level5_full_contract_accepts()
    test_counterexample_blocks_promotion()
    print("SELF_TEST_PASS")

if __name__=="__main__": main()
