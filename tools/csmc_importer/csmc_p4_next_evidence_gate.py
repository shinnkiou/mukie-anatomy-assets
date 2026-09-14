#!/usr/bin/env python3
"""Fail-closed next-evidence router with active oracle-independent mainline development.

v4 progression-policy correction:
- PHYSICAL_ORACLE_PENDING and unresolved serializer-field proof are semantic gates,
  not a global mainline pause.
- oracle-independent importer / Structural IR / validation / evidence-admission
  development remains authorized.
- broad blind semantic exploration and semantic promotion remain blocked.
- former parent-record/length/consumer-crossref Scout gaps remain CLOSED.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict

AUTHORIZED_CLIP_SHA256 = "ed391b6fef0f425165f6dd4719ec9000966742efde5428cb2c1446f63640e933"
AUTHORIZED_CSMC_SHA256 = "388726bd12a433f36ced922077d80cf8ed3f18e543d0106d844715185b77528c"
I2_REQUIRED_ROWS = (2, 3, 8, 14, 15, 21)

CLOSED_CONSUMER_EVIDENCE = (
    "EXPLICIT_PARENT_RECORD_BOUNDARY",
    "EXPLICIT_PARENT_LENGTH_FIELD",
    "EXPLICIT_CONSUMER_CROSSREF",
)
ACTIVE_CONSUMER_CANDIDATES = (
    "EXPLICIT_CSMC_HANDLER_ENTRY",
    "EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP",
    "EXPLICIT_MODELDATA_LOOKUP",
    "EXPLICIT_CANVAS3D_LOAD_ENTRY",
    "EXPLICIT_SERIALIZER_FIELD_READ",
    "EXPLICIT_INTERNAL_MODEL_CONSTRUCTION",
    "CONTROLLED_FIXTURE_TO_CONSUMER_MATCH",
)

ORACLE_INDEPENDENT_MAINLINE_ACTIONS = (
    "STRENGTHEN_IMPORTER_INTAKE_STRUCTURAL_IR_BRIDGE",
    "RUN_FAIL_CLOSED_VALIDATION_AND_REGRESSION",
    "ADMIT_NEW_STRUCTURAL_FACTS_NON_SEMANTIC",
    "ADMIT_LAB_STRUCTURAL_OR_CODEC_CANDIDATES_NON_SEMANTIC",
    "PREPARE_PROOF_GRADE_EVIDENCE_PACKET_SCHEMA",
    "VALIDATE_CONTROLLED_FIXTURE_TO_CONSUMER_MATCH_ADMISSION_GATE",
    "PREPARE_DIRECT_STATIC_EVIDENCE_ADMISSION_PATH",
    "PREPARE_SAME_IDENTITY_FIXTURE_PROVENANCE_ADMISSION",
    "PREPARE_CANDIDATE_TO_DISCRIMINATING_QUESTION_HANDOFF",
    "STRENGTHEN_IMPORTER_CI_SMOKE_GUARDS",
)

SEMANTIC_GATE_BLOCKED_ACTIONS = (
    "CONFIRM_GEOMETRY_OR_INDEX_SEMANTICS",
    "CONFIRM_UV_MATERIAL_BONE_WEIGHT_SEMANTICS",
    "BLENDER_PRODUCTION_EMIT",
    "PROMOTE_VISUAL_RESULT_AS_SEMANTIC_PROOF",
    "PROMOTE_LAB_SCORE_AS_SEMANTIC_PROOF",
    "START_BLIND_PHASE10_FAMILY_EXPANSION",
    "REOPEN_REJECTED_FAMILY_WITHOUT_NEW_INDEPENDENT_EVIDENCE",
    "INFER_UNOBSERVED_ORACLE_VALUES",
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class EvidenceState:
    clip_present: bool = False
    clip_sha256: str | None = None
    csmc_present: bool = False
    csmc_sha256: str | None = None
    i2_bits_by_record: dict[int, int] | None = None
    i2_provenance_valid: bool = False
    # Backward-compatible field. Closed items here are recorded but never re-routed.
    decisive_owner_edges: tuple[str, ...] = ()
    validated_unlock_classes: tuple[str, ...] = ()
    controlled_fixture_bundle_present: bool = False
    controlled_fixture_bundle_sha256: str | None = None
    controlled_fixture_manifest_valid: bool = False
    controlled_fixture_count: int = 0
    controlled_i3_valid_pairs: int = 0
    runtime_authorized: bool = False


def _raw_pair_valid(s: EvidenceState) -> bool:
    return (
        s.clip_present
        and s.csmc_present
        and s.clip_sha256 == AUTHORIZED_CLIP_SHA256
        and s.csmc_sha256 == AUTHORIZED_CSMC_SHA256
    )


def _i2_complete(s: EvidenceState) -> bool:
    bits = s.i2_bits_by_record or {}
    return (
        s.i2_provenance_valid
        and set(bits) == set(I2_REQUIRED_ROWS)
        and all(bits[i] in (0, 1) for i in I2_REQUIRED_ROWS)
    )


def _controlled_valid(s: EvidenceState) -> bool:
    return (
        s.controlled_fixture_bundle_present
        and isinstance(s.controlled_fixture_bundle_sha256, str)
        and bool(SHA256_RE.fullmatch(s.controlled_fixture_bundle_sha256))
        and s.controlled_fixture_manifest_valid
        and s.controlled_fixture_count >= 2
        and s.controlled_i3_valid_pairs >= 0
    )


def route(s: EvidenceState) -> dict:
    closed_seen = sorted(set(s.decisive_owner_edges).intersection(CLOSED_CONSUMER_EVIDENCE))
    valid_unlock = sorted(set(s.validated_unlock_classes).intersection({"I1", "I2", "I3", "I4"}))
    candidates = []
    controlled = _controlled_valid(s)

    if controlled:
        candidates.append({
            "action": "PROCESS_CONTROLLED_FIXTURE_CORPUS",
            "scope": [
                "container_frame",
                "controlled_differentials",
                "phase_segment_ir",
                "confidence_sidecar",
                "importer_container_parser",
            ],
            "semantic_promotion": False,
            "i3_valid_pairs_available": s.controlled_i3_valid_pairs,
            "semantic_gate_required": True,
            "runtime_dispatch": False,
        })
    if _i2_complete(s):
        candidates.append({
            "action": "COMPLETE_I2_SIGNATURES_FROM_VALIDATED_BITS",
            "scope": "records_2_3_8_14_15_21_only",
            "semantic_promotion": False,
        })
    if valid_unlock:
        candidates.append({
            "action": "PROCESS_VALIDATED_STATIC_UNLOCK_ARTIFACT",
            "scope": valid_unlock,
            "semantic_promotion": False,
        })
    if _raw_pair_valid(s):
        candidates.append({
            "action": "RUN_PREDECLARED_COUNTED_BE_FIXED_ROLE_PROBE",
            "scope": [
                "record_whole",
                "stable_prefix_0_20",
                "control_zone_21_27",
                "preserved_island_25_26",
            ],
            "posthoc_window_widening": False,
            "semantic_promotion": False,
        })

    if controlled:
        evidence_status = "NEW_ADMISSIBLE_CONTROLLED_EVIDENCE"
    elif candidates:
        evidence_status = "NEW_ADMISSIBLE_EVIDENCE_PRESENT"
    else:
        evidence_status = "NO_NEW_ADMISSIBLE_EVIDENCE_CURRENT_DURABLE_CORPUS"

    if candidates:
        status = evidence_status
    else:
        status = "STRUCTURAL_DEVELOPMENT_ACTIVE_NO_NEW_SEMANTIC_UNLOCK"

    return {
        "schema_version": "csmc_p4_next_evidence_gate_v4",
        "status": status,
        "evidence_status": evidence_status,
        "mainline_state": "ACTIVE",
        "structural_development": "ACTIVE",
        "semantic_gate": "CLOSED",
        "physical_oracle": "PENDING_MANUAL_ORACLE",
        "oracle_pending_is_global_pause": False,
        "maintenance_only": False,
        "broad_blind_semantic_expansion": "BLOCKED",
        "oracle_independent_importer_structural_work": "AUTHORIZED",
        "oracle_independent_development_actions": list(ORACLE_INDEPENDENT_MAINLINE_ACTIONS),
        "semantic_gate_blocked_actions": list(SEMANTIC_GATE_BLOCKED_ACTIONS),
        "selected_static_actions": candidates,
        "runtime_dispatch": False,
        "runtime_authorized_input": bool(s.runtime_authorized),
        "runtime_policy": "router_does_not_authorize_runtime",
        "semantic_projection": False,
        "blender_emit": False,
        "validated_closed_consumer_evidence": list(CLOSED_CONSUMER_EVIDENCE),
        "closed_consumer_evidence_seen_in_input": closed_seen,
        "consumer_side_reference_candidates": list(ACTIVE_CONSUMER_CANDIDATES),
        "consumer_side_policy": "REFERENCE_ONLY_UNTIL_PROOF_BUT_ADMISSION_PATH_DEVELOPMENT_AUTHORIZED",
        "blocked_by_evidence_policy": (
            "Only the individual task that requires new semantic evidence is BLOCKED_BY_EVIDENCE; "
            "the router must continue to the next oracle-independent mainline task."
        ),
        "current_known_gaps": {
            "i2_missing_records": list(I2_REQUIRED_ROWS),
            "raw_pair_needed_for_fixed_role_real_probe": True,
            "controlled_content_semantics_confirmed": False,
            "geometry_confirmed": False,
            "index_topology_confirmed": False,
        },
        "closed_actions_not_to_repeat": [
            "V4.2 idle-memory scan",
            "broad GUID scanning",
            "unchanged exact-qword LCS/literal-size rescans",
            "duplicate BND_197_TO_195 owner-edge search over current durable corpus",
            "re-search EXPLICIT_PARENT_RECORD_BOUNDARY",
            "re-search EXPLICIT_PARENT_LENGTH_FIELD",
            "re-search EXPLICIT_CONSUMER_CROSSREF",
            "guessing six I2 signatures from marginals/supergroup aesthetics",
            "post-hoc counted-BE window expansion after a miss",
        ],
        "input": asdict(s),
    }


def self_test():
    empty = route(EvidenceState())
    assert empty["status"] == "STRUCTURAL_DEVELOPMENT_ACTIVE_NO_NEW_SEMANTIC_UNLOCK"
    assert empty["evidence_status"] == "NO_NEW_ADMISSIBLE_EVIDENCE_CURRENT_DURABLE_CORPUS"
    assert empty["mainline_state"] == "ACTIVE"
    assert empty["semantic_gate"] == "CLOSED"
    assert empty["oracle_independent_importer_structural_work"] == "AUTHORIZED"
    assert empty["oracle_pending_is_global_pause"] is False
    assert empty["maintenance_only"] is False
    assert "EXPLICIT_PARENT_RECORD_BOUNDARY" in empty["validated_closed_consumer_evidence"]

    old_closed = route(EvidenceState(decisive_owner_edges=CLOSED_CONSUMER_EVIDENCE))
    assert old_closed["status"] == "STRUCTURAL_DEVELOPMENT_ACTIVE_NO_NEW_SEMANTIC_UNLOCK"
    assert old_closed["selected_static_actions"] == []
    assert set(old_closed["closed_consumer_evidence_seen_in_input"]) == set(CLOSED_CONSUMER_EVIDENCE)

    c = route(EvidenceState(
        controlled_fixture_bundle_present=True,
        controlled_fixture_bundle_sha256="a"*64,
        controlled_fixture_manifest_valid=True,
        controlled_fixture_count=13,
        controlled_i3_valid_pairs=0,
    ))
    assert c["status"] == "NEW_ADMISSIBLE_CONTROLLED_EVIDENCE"
    assert c["selected_static_actions"][0]["action"] == "PROCESS_CONTROLLED_FIXTURE_CORPUS"
    assert "phase_segment_ir" in c["selected_static_actions"][0]["scope"]
    assert c["runtime_dispatch"] is False
    assert c["semantic_projection"] is False
    assert c["blender_emit"] is False
    assert c["mainline_state"] == "ACTIVE"

    bad = route(EvidenceState(
        controlled_fixture_bundle_present=True,
        controlled_fixture_bundle_sha256="bad",
        controlled_fixture_manifest_valid=True,
        controlled_fixture_count=13,
    ))
    assert bad["status"] == "STRUCTURAL_DEVELOPMENT_ACTIVE_NO_NEW_SEMANTIC_UNLOCK"

    raw = route(EvidenceState(
        clip_present=True,
        csmc_present=True,
        clip_sha256=AUTHORIZED_CLIP_SHA256,
        csmc_sha256=AUTHORIZED_CSMC_SHA256,
    ))
    assert raw["selected_static_actions"][0]["action"] == "RUN_PREDECLARED_COUNTED_BE_FIXED_ROLE_PROBE"
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    self_test()
    current = EvidenceState(
        controlled_fixture_bundle_present=True,
        controlled_fixture_bundle_sha256="be6132ef83959167ffd19218810e099f0bd164714fbd1ec4770f9296b38643b6",
        controlled_fixture_manifest_valid=True,
        controlled_fixture_count=13,
        controlled_i3_valid_pairs=0,
        decisive_owner_edges=CLOSED_CONSUMER_EVIDENCE,
    )
    print(json.dumps(route(current), indent=2, sort_keys=True))
