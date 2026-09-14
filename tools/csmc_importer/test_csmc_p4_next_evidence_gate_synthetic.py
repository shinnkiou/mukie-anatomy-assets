#!/usr/bin/env python3
from csmc_p4_next_evidence_gate import (
    AUTHORIZED_CLIP_SHA256,
    AUTHORIZED_CSMC_SHA256,
    EvidenceState,
    route,
)


def main() -> None:
    out = route(EvidenceState())
    assert out["status"] == "NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS"
    assert out["selected_static_actions"] == []
    assert out["runtime_dispatch"] is False
    assert out["semantic_projection"] is False
    assert out["blender_emit"] is False

    out = route(EvidenceState(
        i2_bits_by_record={2:1,3:0,8:1,14:0,15:1,21:0},
        i2_provenance_valid=True,
    ))
    assert [x["action"] for x in out["selected_static_actions"]] == ["COMPLETE_I2_SIGNATURES_FROM_VALIDATED_BITS"]

    out = route(EvidenceState(
        clip_present=True,
        csmc_present=True,
        clip_sha256=AUTHORIZED_CLIP_SHA256,
        csmc_sha256=AUTHORIZED_CSMC_SHA256,
    ))
    assert [x["action"] for x in out["selected_static_actions"]] == ["RUN_PREDECLARED_COUNTED_BE_FIXED_ROLE_PROBE"]
    assert out["selected_static_actions"][0]["posthoc_window_widening"] is False

    out = route(EvidenceState(
        decisive_owner_edges=("EXPLICIT_CONSUMER_CROSSREF",),
        validated_unlock_classes=("I3",),
        runtime_authorized=True,
    ))
    assert {x["action"] for x in out["selected_static_actions"]} == {
        "REVIEW_NEW_BOUNDARY_LOCAL_OWNER_EDGE",
        "PROCESS_VALIDATED_STATIC_UNLOCK_ARTIFACT",
    }
    assert out["runtime_dispatch"] is False

    out = route(EvidenceState(
        controlled_fixture_bundle_present=True,
        controlled_fixture_bundle_sha256="be6132ef83959167ffd19218810e099f0bd164714fbd1ec4770f9296b38643b6",
        controlled_fixture_manifest_valid=True,
        controlled_fixture_count=13,
        controlled_i3_valid_pairs=0,
    ))
    assert out["status"] == "NEW_ADMISSIBLE_CONTROLLED_EVIDENCE"
    assert out["selected_static_actions"][0]["action"] == "PROCESS_CONTROLLED_FIXTURE_CORPUS"
    assert out["selected_static_actions"][0]["i3_valid_pairs_available"] == 0
    assert out["selected_static_actions"][0]["semantic_gate_required"] is True
    assert out["runtime_dispatch"] is False
    assert out["semantic_projection"] is False
    assert out["blender_emit"] is False

    bad = route(EvidenceState(
        controlled_fixture_bundle_present=True,
        controlled_fixture_bundle_sha256="not-a-sha",
        controlled_fixture_manifest_valid=True,
        controlled_fixture_count=13,
    ))
    assert bad["status"] == "NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS"

    print("PASS: next-evidence gate accepts controlled evidence while remaining fail-closed for runtime/semantic/emit")


if __name__ == "__main__":
    main()
