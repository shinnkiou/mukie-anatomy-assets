#!/usr/bin/env python3
"""Build a public-safe binding graph across Companion C evidence layers."""
from __future__ import annotations
import argparse
import json
from collections import defaultdict, deque
from pathlib import Path


def has_path(edges, starts, targets):
    adj = defaultdict(list)
    for e in edges:
        adj[e["source"]].append(e["target"])
    q = deque(starts)
    seen = set(starts)
    targets = set(targets)
    while q:
        n = q.popleft()
        if n in targets:
            return True
        for m in adj[n]:
            if m not in seen:
                seen.add(m)
                q.append(m)
    return False


def build_graph() -> dict:
    nodes = [
        "ROUTE_character", "ROUTE_scene", "REGIME_plus965",
        "RF_00", "RF_01", "RF_02", "RF_03", "RF_04",
        "CODEC_counted_be_numeric", "SCHEMA_ModelNodeInfo3D",
        "SEM_geometry", "SEM_index", "SEM_transform", "SEM_hierarchy",
    ]
    edges = [
        {"source": "ROUTE_character", "target": "REGIME_plus965", "level": "STRUCTURAL_PROVENANCE", "evidence": "C-011"},
        *[
            {"source": "REGIME_plus965", "target": f"RF_{i:02d}", "level": "STRUCTURAL_FAMILY", "evidence": "C-002/C-011"}
            for i in range(5)
        ],
    ]
    record_nodes = [f"RF_{i:02d}" for i in range(5)]
    return {
        "schema_version": "csmc_analysis_c_binding_graph_v1",
        "nodes": nodes,
        "edges": edges,
        "counts": {
            "route_bindings": 2,
            "structural_provenance_bindings": 1,
            "record_family_bindings": 5,
            "record_to_confirmed_codec_bindings": 0,
            "record_to_schema_bindings": 0,
            "record_to_semantic_bindings": 0,
        },
        "paths": {
            "record_to_confirmed_codec": has_path(edges, record_nodes, ["CODEC_counted_be_numeric"]),
            "record_to_node_schema": has_path(edges, record_nodes, ["SCHEMA_ModelNodeInfo3D"]),
            "record_to_geometry_or_index": has_path(edges, record_nodes, ["SEM_geometry", "SEM_index"]),
            "record_to_transform_or_hierarchy": has_path(edges, record_nodes, ["SEM_transform", "SEM_hierarchy"]),
        },
        "separate_evidence_surfaces": {
            "counted_be_codec_scope": "active Manager3DOd named BLOB fields",
            "node_schema_scope": "latent ParamScheme ModelNodeInfo3D",
            "record_family_scope": "character +965 cross-serialization regime",
        },
        "guardrails": [
            "Shared product family is not a binding edge.",
            "Similar numeric shape is not a binding edge.",
            "A route/provenance edge does not imply codec or semantic binding.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    ns = ap.parse_args()
    out = build_graph()
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if ns.out:
        ns.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
