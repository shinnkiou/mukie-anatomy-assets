#!/usr/bin/env python3
"""Build public-safe Base44 ingest records from BP3D Zone Review artifacts.
No private textbook/V4/Special Suit content is read or emitted.

R6 repair: summary["final"][mode]["motion"] may be a mapping keyed by motion
name (current producer) or a legacy list of row objects. Normalize both shapes.
"""
from pathlib import Path
import json, sys
from collections import Counter, defaultdict

ZONE_IDS = {
  "HEAD_NECK": {1,2,3},
  "SHOULDER_AXILLA": {5,6,101,102},
  "TORSO_FRONT": {7,8,9,10,11},
  "BACK": {4,12,13,42},
  "ARM": set(range(16,24)) | {44,45,46,47,105},
  "HAND": {24,25} | set(range(60,72)),
  "HIP_GLUTEAL": {14,15,26,27,43,103},
  "THIGH": set(range(28,34)),
  "KNEE": {34,35,104},
  "LOWER_LEG": {36,37,38,39,48,49},
  "FOOT": {40,41} | set(range(50,60)),
}
MOTION_ZONES = {
  "SHOULDER_RAISE": ["SHOULDER_AXILLA","ARM"],
  "ELBOW_BEND": ["ARM"],
  "HIP_FLEX": ["HIP_GLUTEAL","THIGH"],
  "KNEE_BEND": ["KNEE","LOWER_LEG","THIGH"],
  "ANKLE_TOE": ["LOWER_LEG","FOOT"],
}


def motion_rows(final_doc):
    """Return normalized motion row dicts from dict or legacy-list schemas."""
    raw = final_doc.get("motion", {})
    rows = []
    if isinstance(raw, dict):
        for name, payload in raw.items():
            row = dict(payload) if isinstance(payload, dict) else {}
            row["motion"] = str(name)
            rows.append(row)
    elif isinstance(raw, list):
        for payload in raw:
            if isinstance(payload, dict):
                rows.append(dict(payload))
    else:
        raise TypeError(f"unsupported motion schema: {type(raw).__name__}")
    return rows


def faces_by_zone(face_rows):
    out=defaultdict(list)
    for f in face_rows:
        lid=int(f.get("label_id",0) or 0)
        for z,ids in ZONE_IDS.items():
            if lid in ids:
                out[z].append(f); break
    return out


def aggregate(mode, summary, face_doc):
    zones=[]; byz=faces_by_zone(face_doc["faces"]); final=summary["final"][mode]
    motions = motion_rows(final)
    for zone in ZONE_IDS:
        rows=byz.get(zone,[]); n=len(rows); unresolved=sum(1 for x in rows if int(x.get("label_id",0) or 0)>=100); upct=(100*unresolved/n) if n else 100.0
        conf=sum(float(x.get("confidence",0) or 0) for x in rows)/n if n else 0.0
        counts=Counter(int(x.get("label_id",0) or 0) for x in rows)
        fragments=sum(1 for _,c in counts.items() if c and c < 10)
        slivers=sum(1 for _,c in counts.items() if c and c < 4)
        score=max(0.0,min(100.0,conf*100-upct*1.5-fragments*.8-slivers*2))
        status="UNRESOLVED" if unresolved else ("WARN" if fragments>=4 or slivers else "PASS")
        motion_bad=max((float(m.get("bad_pct",0) or 0) for m in motions if zone in MOTION_ZONES.get(m.get("motion"),[])),default=0.0)
        zones.append({"run_key":f"GH{summary.get('run_id','UNKNOWN')}_{mode}_{zone}","cycle":5,"mode":mode,"revision":5,"zone":zone,"score":round(score,3),"mean_confidence":round(conf,6),"face_count":n,"anatomy_status":status,"fragment_count":fragments,"sliver_count":slivers,"unresolved_faces":unresolved,"unresolved_pct":round(upct,6),"motion_bad_pct":round(motion_bad,6),"evidence_status":"DERIVED","status":"解析済"})
    return zones


def main(root):
    root=Path(root); summary=json.loads((root/"summary.json").read_text())
    records=[]; motions=[]
    for mode in ("SAFE","BALANCED","FINE"):
        face=json.loads((root/"reports"/f"{mode}_face_labels.json").read_text())
        records.extend(aggregate(mode,summary,face))
        for m in motion_rows(summary["final"][mode]):
            name=m.get("motion")
            for zone in MOTION_ZONES.get(name,[]):
                extreme=float(m.get("max_stretch_or_collapse",0) or 0)>10
                motions.append({"finding_key":f"GH{summary.get('run_id','UNKNOWN')}_{mode}_{zone}_{name}","run_key":f"GH{summary.get('run_id','UNKNOWN')}_{mode}_{zone}","zone":zone,"motion":name,"mode":mode,"bad_edge_pct":m.get("bad_pct",0),"severe_edges":m.get("severe_edges",0),"max_stretch_or_collapse":m.get("max_stretch_or_collapse",0),"cause_hypothesis":"Proxy deformation; real Armature retest required." if extreme else "Transition/proxy triage; real Armature confirmation required.","cause_confidence":"LOW" if extreme else "MEDIUM","remedy_type":"PROXY" if extreme else "RESPLIT","status":"未解決" if extreme else "再試験"})
    if len(records) != 33:
        raise RuntimeError(f"expected 33 zone records, got {len(records)}")
    if len(motions) != 30:
        raise RuntimeError(f"expected 30 motion records, got {len(motions)}")
    out={"schema_version":"bp3d_base44_ingest_records_v1","adapter_revision":"R6_MOTION_SCHEMA_REPAIR_20260830","source_unchanged":summary.get("source_unchanged"),"source_master_modified":summary.get("source_master_modified"),"abc_abcd_modified":summary.get("abc_abcd_modified"),"zone_records":records,"motion_records":motions}
    dest=root/"reports"/"base44_ingest_records.json";dest.write_text(json.dumps(out,ensure_ascii=False,indent=2));print(dest)

if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else "artifacts")
