#!/usr/bin/env python3
from csmc_structural_importer_intake import (
    CADENCE_CANDIDATE_ID,
    StructuralIntakeError,
    build_structural_intake,
)

SHA = "a" * 64
ENV = {
    "align8_plus8_holds": True,
    "raw_payload_embedded": False,
    "payload_offset": 65,
    "stored_length": 4096,
}


def make_cadence(*, detected=True, lag=307, period=2456, count=7):
    return {
        "detected": detected,
        "lag_qwords": lag,
        "period_bytes": period,
        "cadence_count_candidate": count if detected else None,
        "raw_values_embedded": False,
        "semantic_promotion": False,
    }


def build(cadence, env=ENV):
    return build_structural_intake(
        file_sha256=SHA,
        route_table="character",
        route_column="character",
        outer_version=1,
        envelope=env,
        cadence=cadence,
    )


def main():
    hit = build(make_cadence())
    assert hit["mode"] == "STRUCTURAL_ONLY"
    assert hit["semantic_promotion_count"] == 0
    assert hit["semantic_projection"] is False
    assert hit["blender_emit_ready"] is False
    assert hit["runtime_dispatch"] is False
    assert hit["controlled_fixture_to_consumer_match"] == "UNRESOLVED"
    assert hit["accepted_structural_candidates"][0]["evidence_id"] == CADENCE_CANDIDATE_ID
    assert hit["accepted_structural_candidates"][0]["confidence_level"] == 4
    assert all(v == "unresolved" for v in hit["semantic_claims"].values())

    miss = build(make_cadence(detected=False))
    assert miss["accepted_structural_candidates"] == []

    wrong_period = build(make_cadence(period=999))
    assert wrong_period["accepted_structural_candidates"] == []

    bad_env = dict(ENV)
    bad_env["align8_plus8_holds"] = False
    try:
        build(make_cadence(), bad_env)
    except StructuralIntakeError:
        pass
    else:
        raise AssertionError("invalid envelope must fail closed")

    bad_semantic = make_cadence()
    bad_semantic["semantic_promotion"] = True
    try:
        build(bad_semantic)
    except StructuralIntakeError:
        pass
    else:
        raise AssertionError("semantic-promotion input must fail closed")

    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
