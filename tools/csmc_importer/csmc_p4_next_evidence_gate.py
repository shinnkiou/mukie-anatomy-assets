#!/usr/bin/env python3
"""Fail-closed next-evidence router for CSMC P4.

The router prevents duplicate closed searches. It never acquires evidence and
never authorizes runtime by itself. It only selects a bounded next static action
when a genuinely new admissible artifact is already present and validated.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict

AUTHORIZED_CLIP_SHA256 = "ed391b6fef0f425165f6dd4719ec9000966742efde5428cb2c1446f63640e933"
AUTHORIZED_CSMC_SHA256 = "388726bd12a433f36ced922077d80cf8ed3f18e543d0106d844715185b77528c"
I2_REQUIRED_ROWS = (2, 3, 8, 14, 15, 21)
DECISIVE_OWNER_EDGES = (
    "EXPLICIT_PARENT_RECORD_BOUNDARY",
    "EXPLICIT_PARENT_LENGTH_FIELD",
    "EXPLICIT_CONSUMER_CROSSREF",
)


@dataclass(frozen=True)
class EvidenceState:
    clip_present: bool = False
    clip_sha256: str | None = None
    csmc_present: bool = False
    csmc_sha256: str | None = None
    i2_bits_by_record: dict[int, int] | None = None
    i2_provenance_valid: bool = False
    decisive_owner_edges: tuple[str, ...] = ()
    validated_unlock_classes: tuple[str, ...] = ()
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
        and all(bits[idx] in (0, 1) for idx in I2_REQUIRED_ROWS)
    )


def route(s: EvidenceState) -> dict:
    owner_edges = sorted(set(s.decisive_owner_edges).intersection(DECISIVE_OWNER_EDGES))
    valid_unlock = sorted(set(s.validated_unlock_classes).intersection({"I1", "I2", "I3", "I4"}))

    candidates: list[dict] = []
    if _i2_complete(s):
        candidates.append({
            "action": "COMPLETE_I2_SIGNATURES_FROM_VALIDATED_BITS",
            "scope": "records_2_3_8_14_15_21_only",
            "semantic_promotion": False,
        })
    if owner_edges:
        candidates.append({
            "action": "REVIEW_NEW_BOUNDARY_LOCAL_OWNER_EDGE",
            "scope": owner_edges,
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
            "scope": ["record_whole", "stable_prefix_0_20", "control_zone_21_27", "preserved_island_25_26"],
            "posthoc_window_widening": False,
            "semantic_promotion": False,
        })

    if candidates:
        status = "NEW_ADMISSIBLE_EVIDENCE_PRESENT"
    else:
        status = "NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS"

    return {
        "schema_version": "csmc_p4_next_evidence_gate_v1",
        "status": status,
        "selected_static_actions": candidates,
        "runtime_dispatch": False,
        "runtime_authorized_input": bool(s.runtime_authorized),
        "runtime_policy": "router_does_not_authorize_runtime",
        "closed_actions_not_to_repeat": [
            "V4.2 idle-memory scan",
            "broad GUID scanning",
            "unchanged exact-qword LCS/literal-size rescans",
            "duplicate BND_197_TO_195 owner-edge search over current durable corpus",
            "guessing six I2 signatures from marginals/supergroup aesthetics",
            "post-hoc counted-BE window expansion after a miss",
        ],
        "current_known_gaps": {
            "i2_missing_records": list(I2_REQUIRED_ROWS),
            "owner_decisive_edges_required": list(DECISIVE_OWNER_EDGES),
            "raw_pair_needed_for_fixed_role_real_probe": True,
        },
        "input": asdict(s),
    }


def self_test() -> None:
    empty = route(EvidenceState())
    assert empty["status"] == "NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS"
    assert empty["selected_static_actions"] == []
    assert empty["runtime_dispatch"] is False

    partial_i2 = route(EvidenceState(i2_bits_by_record={2: 1}, i2_provenance_valid=True))
    assert partial_i2["selected_static_actions"] == []

    full_i2 = route(EvidenceState(
        i2_bits_by_record={2:1,3:0,8:1,14:0,15:1,21:0},
        i2_provenance_valid=True,
    ))
    assert full_i2["selected_static_actions"][0]["action"] == "COMPLETE_I2_SIGNATURES_FROM_VALIDATED_BITS"

    wrong_raw = route(EvidenceState(clip_present=True, csmc_present=True, clip_sha256="0"*64, csmc_sha256="1"*64))
    assert wrong_raw["selected_static_actions"] == []

    good_raw = route(EvidenceState(
        clip_present=True, csmc_present=True,
        clip_sha256=AUTHORIZED_CLIP_SHA256, csmc_sha256=AUTHORIZED_CSMC_SHA256,
    ))
    assert good_raw["selected_static_actions"][0]["action"] == "RUN_PREDECLARED_COUNTED_BE_FIXED_ROLE_PROBE"
    assert good_raw["runtime_dispatch"] is False

    edge = route(EvidenceState(decisive_owner_edges=("EXPLICIT_PARENT_LENGTH_FIELD", "NOT_VALID")))
    assert edge["selected_static_actions"][0]["scope"] == ["EXPLICIT_PARENT_LENGTH_FIELD"]

    rt = route(EvidenceState(runtime_authorized=True))
    assert rt["runtime_dispatch"] is False
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    self_test()
    print(json.dumps(route(EvidenceState()), indent=2, sort_keys=True))
