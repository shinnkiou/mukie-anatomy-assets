#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path

EDGE_LEVELS={"LIVE_RESOLVED_EDGE","SCHEMA_ONLY_EDGE","UNRESOLVED_ROUTE"}

def validate_edge(e: dict) -> None:
    lvl=e.get("level")
    if lvl not in EDGE_LEVELS: raise ValueError(f"invalid level {lvl}")
    if lvl=="LIVE_RESOLVED_EDGE":
        for k in ("source","relation","target"):
            if not e.get(k): raise ValueError(f"live resolved edge missing {k}")
        if not e.get("target_kind"): raise ValueError("live resolved edge missing target_kind")
        if e.get("schema_only"): raise ValueError("live resolved edge cannot be schema_only")
    if lvl=="SCHEMA_ONLY_EDGE" and not e.get("schema_only"):
        raise ValueError("schema-only edge must be marked schema_only")
    if lvl=="UNRESOLVED_ROUTE" and e.get("target_kind"):
        raise ValueError("unresolved route must not claim target_kind")

def analyze(graph: dict) -> dict:
    edges=[]; counts=Counter(); routes={}
    for e in graph.get("edges",[]):
        validate_edge(e); row=dict(e); edges.append(row); counts[row["level"]]+=1
        if row["level"]=="LIVE_RESOLVED_EDGE" and row.get("importer_route"):
            routes[row["importer_route"]]={"source":row["source"],"target":row["target"],"target_kind":row["target_kind"],"semantic_payload_role":"UNRESOLVED"}
    return {
        "schema_version":"csmc_analysis_c_owner_container_map_v1",
        "nodes":graph.get("nodes",[]),
        "edges":edges,
        "edge_counts":dict(counts),
        "importer_routes":routes,
        "serializer_owner_claimed":False,
        "payload_semantics_claimed":False,
        "guardrails":[
            "Route ownership means a live container/table field resolves to an external payload; it is not proof of the serializer implementation owner.",
            "Schema-only legacy relations are never upgraded to live edges without live table/row evidence.",
            "Resolved target kind (catalog_character/scene) does not identify mesh, bone, material, index, or transform encoding inside that payload."
        ]
    }

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("input",type=Path); ap.add_argument("--out",type=Path)
    ns=ap.parse_args(); out=analyze(json.loads(ns.input.read_text(encoding="utf-8")))
    text=json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if ns.out: ns.out.write_text(text,encoding="utf-8")
    else: print(text,end="")
    return 0
if __name__=="__main__": raise SystemExit(main())
