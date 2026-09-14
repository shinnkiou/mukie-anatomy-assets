#!/usr/bin/env python3
from copy import deepcopy
from csmc_analysis_c_phase_core_exclusion_mask_c060 import BASELINE, evaluate

def test_c060_mask():
    out=evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["classification"]=="PHASE_CORE_EXCLUSION_MASK_READY"
    assert out["total_qwords"]==14180
    assert out["excluded_qwords"]==10830
    assert out["remaining_search_qwords"]==3350
    assert out["masks"]["F07"]["search_prefix"]==[0,774]
    assert out["semantic_binding"]=="UNRESOLVED"

def test_c060_fail_closed():
    cases=[]
    b=deepcopy(BASELINE);b["fixtures"]["F07"]["core_start"]=773;cases.append(b)
    b=deepcopy(BASELINE);b["fixtures"]["R03"]["qwords"]=2276;cases.append(b)
    b=deepcopy(BASELINE);del b["fixtures"]["F02"];cases.append(b)
    b=deepcopy(BASELINE);b["semantic_promotion_count"]=1;cases.append(b)
    b=deepcopy(BASELINE);b["runtime_dispatch"]=True;cases.append(b)
    for x in cases: assert evaluate(x)["accepted"] is False
