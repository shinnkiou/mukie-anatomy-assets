#!/usr/bin/env python3
"""C-060: fail-closed search masks from C-057 proven transitive suffix cores."""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Mapping
PIPELINE_STAGE="STRUCTURAL_ONLY"; CLASSIFICATION="PHASE_CORE_EXCLUSION_MASK_READY"
BASELINE={"pipeline_stage":PIPELINE_STAGE,"semantic_promotion_count":0,"blender_emit_ready":False,"runtime_dispatch":False,"raw_private_bytes_published":False,"fixtures":{"F02":{"phase":7,"qwords":2212,"core_start":402,"core_end":2211},"F04":{"phase":7,"qwords":2320,"core_start":510,"core_end":2319},"R01":{"phase":7,"qwords":2233,"core_start":423,"core_end":2232},"F06":{"phase":1,"qwords":2564,"core_start":762,"core_end":2563},"F07":{"phase":1,"qwords":2576,"core_start":774,"core_end":2575},"R03":{"phase":1,"qwords":2275,"core_start":473,"core_end":2274}}}
EXPECTED={"F02":(7,2212,402,2211),"F04":(7,2320,510,2319),"R01":(7,2233,423,2232),"F06":(1,2564,762,2563),"F07":(1,2576,774,2575),"R03":(1,2275,473,2274)}
def evaluate(row:Mapping[str,Any])->dict[str,Any]:
    if not isinstance(row,Mapping): return {"accepted":False,"errors":["input_not_mapping"]}
    errors=[]
    if row.get("pipeline_stage")!=PIPELINE_STAGE: errors.append("pipeline_not_structural_only")
    for k,e in (("semantic_promotion_count",0),("blender_emit_ready",False),("runtime_dispatch",False),("raw_private_bytes_published",False)):
        if row.get(k)!=e or type(row.get(k)) is not type(e): errors.append(f"{k}_mismatch")
    f=row.get("fixtures")
    if not isinstance(f,Mapping) or set(f)!=set(EXPECTED): errors.append("fixture_set_mismatch")
    else:
        for fid,e in EXPECTED.items():
            x=f[fid]; a=tuple(x.get(k) for k in ("phase","qwords","core_start","core_end")) if isinstance(x,Mapping) else ()
            if a!=e or any(type(v) is not int for v in a): errors.append(f"{fid}_core_mismatch"); continue
            _,total,start,end=a
            if end-start not in (1809,1801): errors.append(f"{fid}_core_length_unexpected")
            if end+1!=total: errors.append(f"{fid}_terminal_qword_not_one")
    if errors:return {"accepted":False,"errors":errors,"classification":"REJECTED"}
    masks={}; tq=ex=rem=0
    for fid,x in f.items():
        total=x["qwords"]; start=x["core_start"]; end=x["core_end"]; core=end-start; left=start+(total-end)
        tq+=total; ex+=core; rem+=left
        masks[fid]={"phase":x["phase"],"search_prefix":[0,start],"exclude_proven_invariant_core":[start,end],"search_terminal":[end,total],"excluded_qwords":core,"remaining_search_qwords":left}
    return {"accepted":True,"errors":[],"classification":CLASSIFICATION,"fixture_count":len(masks),"masks":masks,"total_qwords":tq,"excluded_qwords":ex,"remaining_search_qwords":rem,"excluded_fraction":ex/tq,"remaining_fraction":rem/tq,"scope":"CURRENT_SIX_FIXTURES_ONLY","semantic_binding":"UNRESOLVED","semantic_promotion_count":0,"blender_emit_ready":False,"runtime_dispatch":False}
def self_test()->None:
    out=evaluate(BASELINE); assert out["accepted"] is True; assert out["total_qwords"]==14180; assert out["excluded_qwords"]==10830; assert out["remaining_search_qwords"]==3350; assert out["masks"]["F07"]["search_prefix"]==[0,774]; assert out["masks"]["F07"]["search_terminal"]==[2575,2576]
    cases=[]
    b=deepcopy(BASELINE);b["fixtures"]["F07"]["core_start"]=773;cases.append(b)
    b=deepcopy(BASELINE);b["fixtures"]["R03"]["qwords"]=2276;cases.append(b)
    b=deepcopy(BASELINE);del b["fixtures"]["F02"];cases.append(b)
    b=deepcopy(BASELINE);b["semantic_promotion_count"]=1;cases.append(b)
    b=deepcopy(BASELINE);b["runtime_dispatch"]=True;cases.append(b)
    for x in cases: assert evaluate(x)["accepted"] is False
    print("C060_SELF_TEST_PASS 10/10")
if __name__=="__main__":self_test()
