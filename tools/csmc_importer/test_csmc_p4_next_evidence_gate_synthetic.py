#!/usr/bin/env python3
from csmc_p4_next_evidence_gate import (
    ACTIVE_CONSUMER_CANDIDATES,
    CLOSED_CONSUMER_EVIDENCE,
    ORACLE_INDEPENDENT_MAINLINE_ACTIONS,
    SEMANTIC_GATE_BLOCKED_ACTIONS,
    EvidenceState,
    route,
)


def main():
    closed = route(EvidenceState(decisive_owner_edges=CLOSED_CONSUMER_EVIDENCE))
    assert closed["status"] == "STRUCTURAL_DEVELOPMENT_ACTIVE_NO_NEW_SEMANTIC_UNLOCK"
    assert closed["evidence_status"] == "NO_NEW_ADMISSIBLE_EVIDENCE_CURRENT_DURABLE_CORPUS"
    assert closed["selected_static_actions"] == []
    assert closed["mainline_state"] == "ACTIVE"
    assert closed["structural_development"] == "ACTIVE"
    assert closed["semantic_gate"] == "CLOSED"
    assert closed["physical_oracle"] == "PENDING_MANUAL_ORACLE"
    assert closed["oracle_pending_is_global_pause"] is False
    assert closed["maintenance_only"] is False
    assert closed["broad_blind_semantic_expansion"] == "BLOCKED"
    assert closed["oracle_independent_importer_structural_work"] == "AUTHORIZED"
    assert set(closed["oracle_independent_development_actions"]) == set(ORACLE_INDEPENDENT_MAINLINE_ACTIONS)
    assert set(closed["semantic_gate_blocked_actions"]) == set(SEMANTIC_GATE_BLOCKED_ACTIONS)
    assert closed["consumer_side_policy"] == "REFERENCE_ONLY_UNTIL_PROOF_BUT_ADMISSION_PATH_DEVELOPMENT_AUTHORIZED"
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
    assert controlled["mainline_state"] == "ACTIVE"
    assert controlled["semantic_projection"] is False
    assert controlled["blender_emit"] is False

    bad = route(EvidenceState(
        controlled_fixture_bundle_present=True,
        controlled_fixture_bundle_sha256="not-a-sha",
        controlled_fixture_manifest_valid=True,
        controlled_fixture_count=13,
    ))
    assert bad["status"] == "STRUCTURAL_DEVELOPMENT_ACTIVE_NO_NEW_SEMANTIC_UNLOCK"
    assert bad["mainline_state"] == "ACTIVE"
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
