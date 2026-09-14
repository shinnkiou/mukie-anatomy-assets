#!/usr/bin/env python3
from csmc_lab_candidate_intake import REQUIRED_SAFETY, SCHEMA_VERSION, validate_and_admit


def base(kind="STRUCTURAL_CANDIDATE"):
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": "SYNTHETIC-001",
        "candidate_kind": kind,
        "producer_lane": "IMPORTER_LAB",
        "source_run_key": "SYNTHETIC-RUN",
        "source_sha256": "a" * 64,
        "generation": 1,
        "family": "RELATIONSHIP_ONLY",
        "candidate_payload": {"region": "synthetic", "offset": 16, "relation": "bounded"},
        "evidence_refs": [{"type": "synthetic", "id": "fixture-1"}],
        "safety": dict(REQUIRED_SAFETY),
    }


def expect_reject(record):
    try:
        validate_and_admit(record)
    except ValueError:
        return
    raise AssertionError("candidate should have been rejected")


def main():
    structural = validate_and_admit(base())
    assert structural["intake_status"] == "ADMITTED_NON_SEMANTIC_REFERENCE_ONLY"
    assert structural["downstream_scope"] == "STRUCTURAL_IR_CANDIDATE_ONLY"
    assert structural["semantic_projection"] is False
    assert structural["semantic_promotion"] is False
    assert structural["proof_grade"] is False
    assert structural["blender_emit"] is False
    assert structural["runtime_dispatch"] is False
    assert structural["physical_oracle_required_for_intake"] is False
    assert structural["independent_evidence_required_for_semantic_promotion"] is True
    assert structural["mainline_state"] == "ACTIVE"

    codec = validate_and_admit(base("CODEC_CANDIDATE"))
    assert codec["downstream_scope"] == "CODEC_DIAGNOSTIC_CANDIDATE_ONLY"

    bad = base()
    bad["safety"]["semantic_promotion"] = True
    expect_reject(bad)

    bad = base()
    bad["candidate_payload"]["semantic_claim"] = "geometry"
    expect_reject(bad)

    bad = base()
    bad["candidate_payload"]["raw_bytes"] = "00ff"
    expect_reject(bad)

    bad = base()
    bad["source_sha256"] = "bad"
    expect_reject(bad)

    bad = base("SEMANTIC_CANDIDATE")
    expect_reject(bad)

    bad = base()
    bad["producer_lane"] = "UNKNOWN"
    expect_reject(bad)

    bad = base()
    bad["safety"]["runtime_dispatch"] = True
    expect_reject(bad)

    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
