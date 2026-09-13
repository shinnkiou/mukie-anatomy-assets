#!/usr/bin/env python3
"""C-044: fail-closed audit for the three decisive BND_197_TO_195 owner edges.

Container-level or schema-only references remain useful context but cannot satisfy a
boundary-local owner edge.
"""
from __future__ import annotations

DECISIVE_EDGE_TYPES = {
    "EXPLICIT_PARENT_RECORD_BOUNDARY",
    "EXPLICIT_PARENT_LENGTH_FIELD",
    "EXPLICIT_CONSUMER_CROSSREF",
}


def audit_decisive_edges(
    edges: list[dict], *, boundary_id: str = "BND_197_TO_195"
) -> dict:
    satisfied: set[str] = set()
    contextual: list[str | None] = []
    rejected_as_decisive: list[str | None] = []

    for edge in edges:
        edge_type = edge.get("edge_type")
        if edge_type not in DECISIVE_EDGE_TYPES:
            contextual.append(edge.get("edge_id"))
            continue
        if (
            edge.get("boundary_id") == boundary_id
            and edge.get("evidence_level") == "LIVE_BOUNDARY_LOCAL"
            and edge.get("explicit") is True
        ):
            satisfied.add(edge_type)
        else:
            rejected_as_decisive.append(edge.get("edge_id"))

    missing = sorted(DECISIVE_EDGE_TYPES - satisfied)
    return {
        "boundary_id": boundary_id,
        "satisfied_decisive_edges": sorted(satisfied),
        "missing_decisive_edges": missing,
        "contextual_edge_ids": sorted(x for x in contextual if x),
        "rejected_as_decisive_edge_ids": sorted(x for x in rejected_as_decisive if x),
        "owner_scope_proven": not missing,
        "semantic_owner": "UNRESOLVED",
        "semantic_promotion_count": 0,
        "runtime_dispatch_requested": False,
    }


def self_test() -> None:
    existing = [
        {
            "edge_id": "BANK_FIRST_LOADER_INDEX",
            "edge_type": "EXPLICIT_CONSUMER_CROSSREF",
            "boundary_id": None,
            "evidence_level": "LIVE_CONTAINER_LEVEL",
            "explicit": True,
        },
        {
            "edge_id": "MODELINFO_FIRST_INDEX",
            "edge_type": "EXPLICIT_PARENT_RECORD_BOUNDARY",
            "boundary_id": None,
            "evidence_level": "SCHEMA_ONLY",
            "explicit": True,
        },
        {
            "edge_id": "MODELINFO_COUNT",
            "edge_type": "EXPLICIT_PARENT_LENGTH_FIELD",
            "boundary_id": None,
            "evidence_level": "SCHEMA_ONLY",
            "explicit": True,
        },
    ]
    out = audit_decisive_edges(existing)
    checks = [
        out["satisfied_decisive_edges"] == [],
        set(out["missing_decisive_edges"]) == DECISIVE_EDGE_TYPES,
        "BANK_FIRST_LOADER_INDEX" in out["rejected_as_decisive_edge_ids"],
        "MODELINFO_FIRST_INDEX" in out["rejected_as_decisive_edge_ids"],
        out["owner_scope_proven"] is False,
        out["semantic_owner"] == "UNRESOLVED" and out["runtime_dispatch_requested"] is False,
    ]
    assert all(checks), (checks, out)

    synthetic = existing + [
        {
            "edge_id": "SYNTH_PARENT_LENGTH",
            "edge_type": "EXPLICIT_PARENT_LENGTH_FIELD",
            "boundary_id": "BND_197_TO_195",
            "evidence_level": "LIVE_BOUNDARY_LOCAL",
            "explicit": True,
        }
    ]
    out2 = audit_decisive_edges(synthetic)
    assert "EXPLICIT_PARENT_LENGTH_FIELD" in out2["satisfied_decisive_edges"]
    print("SELF_TEST_PASS 7/7")


if __name__ == "__main__":
    self_test()
