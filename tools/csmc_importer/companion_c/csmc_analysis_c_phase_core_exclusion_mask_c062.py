#!/usr/bin/env python3
"""C-062: extend the proven-core exclusion mask with the new phase-3 R04/V01 holdout."""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Mapping

PIPELINE_STAGE = "STRUCTURAL_ONLY"
CLASSIFICATION = "PHASE_CORE_EXCLUSION_MASK_EXTENDED_PHASE3_READY"

BASELINE = {
    "pipeline_stage": PIPELINE_STAGE,
    "semantic_promotion_count": 0,
    "blender_emit_ready": False,
    "runtime_dispatch": False,
    "raw_private_bytes_published": False,
    "source_c060_head": "e1d574764c4c783be4670519c094078b460e3bae",
    "source_c061_head": "10fedd81d49fdeb26d6e471b9b8d88fae639dec5",
    "source_mainline_phase3_head": "7ab466ac495cbb09792fad20f0d30e2bb4ed551a",
    "fixtures": {
        "F02":{"evidence_class":"TRANSITIVE_PHASE7","phase":7,"qwords":2212,"core_start":402,"core_end":2211},
        "F04":{"evidence_class":"TRANSITIVE_PHASE7","phase":7,"qwords":2320,"core_start":510,"core_end":2319},
        "R01":{"evidence_class":"TRANSITIVE_PHASE7","phase":7,"qwords":2233,"core_start":423,"core_end":2232},
        "F06":{"evidence_class":"TRANSITIVE_PHASE1","phase":1,"qwords":2564,"core_start":762,"core_end":2563},
        "F07":{"evidence_class":"TRANSITIVE_PHASE1","phase":1,"qwords":2576,"core_start":774,"core_end":2575},
        "R03":{"evidence_class":"TRANSITIVE_PHASE1","phase":1,"qwords":2275,"core_start":473,"core_end":2274},
        "R04":{"evidence_class":"INDEPENDENT_PHASE3_HOLDOUT_PAIR","phase":3,"qwords":2282,"core_start":480,"core_end":2280},
        "V01":{"evidence_class":"INDEPENDENT_PHASE3_HOLDOUT_PAIR","phase":3,"qwords":535742,"core_start":533940,"core_end":535740},
    },
}

EXPECTED = {
    "F02":("TRANSITIVE_PHASE7",7,2212,402,2211),
    "F04":("TRANSITIVE_PHASE7",7,2320,510,2319),
    "R01":("TRANSITIVE_PHASE7",7,2233,423,2232),
    "F06":("TRANSITIVE_PHASE1",1,2564,762,2563),
    "F07":("TRANSITIVE_PHASE1",1,2576,774,2575),
    "R03":("TRANSITIVE_PHASE1",1,2275,473,2274),
    "R04":("INDEPENDENT_PHASE3_HOLDOUT_PAIR",3,2282,480,2280),
    "V01":("INDEPENDENT_PHASE3_HOLDOUT_PAIR",3,535742,533940,535740),
}

def evaluate(row: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"accepted":False,"errors":["input_not_mapping"],"classification":"REJECTED"}
    errors=[]
    for key, expected in (
        ("pipeline_stage",PIPELINE_STAGE),
        ("semantic_promotion_count",0),
        ("blender_emit_ready",False),
        ("runtime_dispatch",False),
        ("raw_private_bytes_published",False),
        ("source_c060_head","e1d574764c4c783be4670519c094078b460e3bae"),
        ("source_c061_head","10fedd81d49fdeb26d6e471b9b8d88fae639dec5"),
        ("source_mainline_phase3_head","7ab466ac495cbb09792fad20f0d30e2bb4ed551a"),
    ):
        if row.get(key) != expected or type(row.get(key)) is not type(expected):
            errors.append(f"{key}_mismatch")
    fixtures=row.get("fixtures")
    if not isinstance(fixtures,Mapping) or set(fixtures)!=set(EXPECTED):
        errors.append("fixture_set_mismatch")
    else:
        for fid, exp in EXPECTED.items():
            x=fixtures[fid]
            vals=tuple(x.get(k) for k in ("evidence_class","phase","qwords","core_start","core_end")) if isinstance(x,Mapping) else ()
            if vals != exp:
                errors.append(f"{fid}_core_mismatch")
                continue
            _, phase, total, start, end = vals
            core=end-start
            tail=total-end
            expected_core=1809 if phase==7 else 1801 if phase==1 else 1800
            expected_tail=1 if phase in (1,7) else 2
            if core != expected_core:
                errors.append(f"{fid}_core_length_unexpected")
            if tail != expected_tail:
                errors.append(f"{fid}_tail_unexpected")
    if errors:
        return {"accepted":False,"errors":errors,"classification":"REJECTED"}
    masks={}
    total_qwords=excluded_qwords=remaining_qwords=0
    for fid,x in fixtures.items():
        total=x["qwords"]; start=x["core_start"]; end=x["core_end"]
        core=end-start; remain=start+(total-end)
        total_qwords += total; excluded_qwords += core; remaining_qwords += remain
        masks[fid]={
            "evidence_class":x["evidence_class"],
            "phase":x["phase"],
            "search_prefix":[0,start],
            "exclude_validated_invariant_core":[start,end],
            "search_terminal":[end,total],
            "excluded_qwords":core,
            "remaining_search_qwords":remain,
        }
    return {
        "accepted":True,
        "errors":[],
        "classification":CLASSIFICATION,
        "fixture_count":len(masks),
        "masks":masks,
        "total_qwords":total_qwords,
        "excluded_qwords":excluded_qwords,
        "remaining_search_qwords":remaining_qwords,
        "excluded_fraction":excluded_qwords/total_qwords,
        "remaining_fraction":remaining_qwords/total_qwords,
        "scope":"EIGHT_FIXTURES_C060_PLUS_PHASE3_HOLDOUT",
        "phase3_semantic_control":False,
        "semantic_binding":"UNRESOLVED",
        "semantic_promotion_count":0,
        "blender_emit_ready":False,
        "runtime_dispatch":False,
    }

def self_test() -> None:
    out=evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["fixture_count"] == 8
    assert out["total_qwords"] == 552204
    assert out["excluded_qwords"] == 14430
    assert out["remaining_search_qwords"] == 537774
    assert out["masks"]["R04"]["search_terminal"] == [2280,2282]
    assert out["masks"]["V01"]["search_prefix"] == [0,533940]
    assert out["phase3_semantic_control"] is False
    cases=[]
    bad=deepcopy(BASELINE);bad["fixtures"]["R04"]["core_end"]=2279;cases.append(bad)
    bad=deepcopy(BASELINE);bad["fixtures"]["V01"]["qwords"]=535743;cases.append(bad)
    bad=deepcopy(BASELINE);bad["fixtures"]["R04"]["evidence_class"]="TRANSITIVE_PHASE3";cases.append(bad)
    bad=deepcopy(BASELINE);bad["semantic_promotion_count"]=1;cases.append(bad)
    bad=deepcopy(BASELINE);bad["runtime_dispatch"]=True;cases.append(bad)
    for x in cases:
        assert evaluate(x)["accepted"] is False
    print("C062_SELF_TEST_PASS 13/13")

if __name__=="__main__":
    self_test()
