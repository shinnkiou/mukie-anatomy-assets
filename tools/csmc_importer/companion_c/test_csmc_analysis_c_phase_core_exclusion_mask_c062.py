#!/usr/bin/env python3
from copy import deepcopy
from csmc_analysis_c_phase_core_exclusion_mask_c062 import BASELINE, evaluate

def test_c062_extended_mask():
    out=evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["classification"]=="PHASE_CORE_EXCLUSION_MASK_EXTENDED_PHASE3_READY"
    assert out["fixture_count"]==8
    assert out["total_qwords"]==552204
    assert out["excluded_qwords"]==14430
    assert out["remaining_search_qwords"]==537774
    assert out["masks"]["R04"]["search_prefix"]==[0,480]
    assert out["masks"]["V01"]["search_terminal"]==[535740,535742]
    assert out["phase3_semantic_control"] is False

def test_c062_fail_closed():
    cases=[]
    b=deepcopy(BASELINE);b["fixtures"]["R04"]["core_end"]=2279;cases.append(b)
    b=deepcopy(BASELINE);b["fixtures"]["V01"]["qwords"]=535743;cases.append(b)
    b=deepcopy(BASELINE);b["fixtures"]["R04"]["evidence_class"]="TRANSITIVE_PHASE3";cases.append(b)
    b=deepcopy(BASELINE);del b["fixtures"]["F02"];cases.append(b)
    b=deepcopy(BASELINE);b["semantic_promotion_count"]=1;cases.append(b)
    b=deepcopy(BASELINE);b["blender_emit_ready"]=True;cases.append(b)
    b=deepcopy(BASELINE);b["runtime_dispatch"]=True;cases.append(b)
    for row in cases:
        assert evaluate(row)["accepted"] is False
