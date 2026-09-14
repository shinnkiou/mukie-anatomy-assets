#!/usr/bin/env python3
"""Fail-closed next-evidence router with controlled-fixture intake support."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict

AUTHORIZED_CLIP_SHA256 = "ed391b6fef0f425165f6dd4719ec9000966742efde5428cb2c1446f63640e933"
AUTHORIZED_CSMC_SHA256 = "388726bd12a433f36ced922077d80cf8ed3f18e543d0106d844715185b77528c"
I2_REQUIRED_ROWS = (2, 3, 8, 14, 15, 21)
DECISIVE_OWNER_EDGES = (
    "EXPLICIT_PARENT_RECORD_BOUNDARY",
    "EXPLICIT_PARENT_LENGTH_FIELD",
    "EXPLICIT_CONSUMER_CROSSREF",
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
    decisive_owner_edges: tuple[str, ...] = ()
    validated_unlock_classes: tuple[str, ...] = ()
    controlled_fixture_bundle_present: bool = False
    controlled_fixture_bundle_sha256: str | None = None
    controlled_fixture_manifest_valid: bool = False
    controlled_fixture_count: int = 0
    controlled_i3_valid_pairs: int = 0
    runtime_authorized: bool = False


def _raw_pair_valid(s: EvidenceState) -> bool:
    return s.clip_present and s.csmc_present and s.clip_sha256 == AUTHORIZED_CLIP_SHA256 and s.csmc_sha256 == AUTHORIZED_CSMC_SHA256


def _i2_complete(s: EvidenceState) -> bool:
    bits=s.i2_bits_by_record or {}
    return s.i2_provenance_valid and set(bits)==set(I2_REQUIRED_ROWS) and all(bits[i] in (0,1) for i in I2_REQUIRED_ROWS)


def _controlled_valid(s: EvidenceState) -> bool:
    return (
        s.controlled_fixture_bundle_present
        and isinstance(s.controlled_fixture_bundle_sha256,str)
        and bool(SHA256_RE.fullmatch(s.controlled_fixture_bundle_sha256))
        and s.controlled_fixture_manifest_valid
        and s.controlled_fixture_count >= 2
        and s.controlled_i3_valid_pairs >= 0
    )


def route(s: EvidenceState) -> dict:
    owner_edges=sorted(set(s.decisive_owner_edges).intersection(DECISIVE_OWNER_EDGES))
    valid_unlock=sorted(set(s.validated_unlock_classes).intersection({"I1","I2","I3","I4"}))
    candidates=[]
    controlled=_controlled_valid(s)
    if controlled:
        candidates.append({
            "action":"PROCESS_CONTROLLED_FIXTURE_CORPUS",
            "scope":["container_frame","controlled_differentials","confidence_sidecar","importer_container_parser"],
            "semantic_promotion":False,
            "i3_valid_pairs_available": s.controlled_i3_valid_pairs,
            "semantic_gate_required": True,
            "runtime_dispatch":False,
        })
    if _i2_complete(s):
        candidates.append({"action":"COMPLETE_I2_SIGNATURES_FROM_VALIDATED_BITS","scope":"records_2_3_8_14_15_21_only","semantic_promotion":False})
    if owner_edges:
        candidates.append({"action":"REVIEW_NEW_BOUNDARY_LOCAL_OWNER_EDGE","scope":owner_edges,"semantic_promotion":False})
    if valid_unlock:
        candidates.append({"action":"PROCESS_VALIDATED_STATIC_UNLOCK_ARTIFACT","scope":valid_unlock,"semantic_promotion":False})
    if _raw_pair_valid(s):
        candidates.append({"action":"RUN_PREDECLARED_COUNTED_BE_FIXED_ROLE_PROBE","scope":["record_whole","stable_prefix_0_20","control_zone_21_27","preserved_island_25_26"],"posthoc_window_widening":False,"semantic_promotion":False})

    if controlled:
        status="NEW_ADMISSIBLE_CONTROLLED_EVIDENCE"
    elif candidates:
        status="NEW_ADMISSIBLE_EVIDENCE_PRESENT"
    else:
        status="NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS"
    return {
        "schema_version":"csmc_p4_next_evidence_gate_v2",
        "status":status,
        "selected_static_actions":candidates,
        "runtime_dispatch":False,
        "runtime_authorized_input":bool(s.runtime_authorized),
        "runtime_policy":"router_does_not_authorize_runtime",
        "semantic_projection":False,
        "blender_emit":False,
        "current_known_gaps": {
            "i2_missing_records": list(I2_REQUIRED_ROWS),
            "owner_decisive_edges_required": list(DECISIVE_OWNER_EDGES),
            "raw_pair_needed_for_fixed_role_real_probe": True,
            "controlled_content_semantics_confirmed": False,
        },
        "closed_actions_not_to_repeat":[
            "V4.2 idle-memory scan","broad GUID scanning","unchanged exact-qword LCS/literal-size rescans",
            "duplicate BND_197_TO_195 owner-edge search over current durable corpus",
            "guessing six I2 signatures from marginals/supergroup aesthetics","post-hoc counted-BE window expansion after a miss",
        ],
        "input":asdict(s),
    }


def self_test():
    assert route(EvidenceState())["status"]=="NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS"
    c=route(EvidenceState(controlled_fixture_bundle_present=True,controlled_fixture_bundle_sha256="a"*64,controlled_fixture_manifest_valid=True,controlled_fixture_count=13,controlled_i3_valid_pairs=0))
    assert c["status"]=="NEW_ADMISSIBLE_CONTROLLED_EVIDENCE"
    assert c["selected_static_actions"][0]["action"]=="PROCESS_CONTROLLED_FIXTURE_CORPUS"
    assert c["selected_static_actions"][0]["i3_valid_pairs_available"] == 0
    assert c["selected_static_actions"][0]["semantic_gate_required"] is True
    assert c["runtime_dispatch"] is False and c["semantic_projection"] is False and c["blender_emit"] is False
    bad=route(EvidenceState(controlled_fixture_bundle_present=True,controlled_fixture_bundle_sha256="bad",controlled_fixture_manifest_valid=True,controlled_fixture_count=13))
    assert bad["status"]=="NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS"
    raw=route(EvidenceState(clip_present=True,csmc_present=True,clip_sha256=AUTHORIZED_CLIP_SHA256,csmc_sha256=AUTHORIZED_CSMC_SHA256))
    assert raw["selected_static_actions"][0]["action"]=="RUN_PREDECLARED_COUNTED_BE_FIXED_ROLE_PROBE"
    print("SELF_TEST_PASS")

if __name__=="__main__":
    self_test()
    current=EvidenceState(controlled_fixture_bundle_present=True,controlled_fixture_bundle_sha256="be6132ef83959167ffd19218810e099f0bd164714fbd1ec4770f9296b38643b6",controlled_fixture_manifest_valid=True,controlled_fixture_count=13,controlled_i3_valid_pairs=0)
    print(json.dumps(route(current),indent=2,sort_keys=True))
