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
    print("PASS: next-evidence gate is fail-closed and does not reauthorize runtime")


if __name__ == "__main__":
    main()
