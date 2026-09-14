#!/usr/bin/env python3
from csmc_p4_next_evidence_gate import (
    ACTIVE_CONSUMER_CANDIDATES,
    CLOSED_CONSUMER_EVIDENCE,
    EvidenceState,
    route,
)


def main():
    closed = route(EvidenceState(decisive_owner_edges=CLOSED_CONSUMER_EVIDENCE))
    assert closed["status"] == "NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS"
    assert closed["selected_static_actions"] == []
    assert closed["consumer_side_policy"] == "REFERENCE_ONLY_NOT_MANDATORY_MAINLINE_TASKS"
    assert set(closed["consumer_side_reference_candidates"]) == set(ACTIVE_CONSUMER_CANDIDATES)

    controlled = route(EvidenceState(
        controlled_fixture_bundle_present=True,
        controlled_fixture_bundle_sha256="a"*64,
        controlled_fixture_manifest_valid=True,
        controlled_fixture_count=13,
        controlled_i3_valid_pairs=0,
        decisive_owner_edges=CLOSED_CONSUMER_EVIDENCE,
    ))
    assert controlled["status"] == "NEW_ADMISSIBLE_CONTROLLED_EVIDENCE"
    assert controlled["semantic_projection"] is False
    assert controlled["blender_emit"] is False
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
