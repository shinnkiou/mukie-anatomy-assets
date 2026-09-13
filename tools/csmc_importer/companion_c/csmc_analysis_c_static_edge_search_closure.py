#!/usr/bin/env python3
"""C-045: bounded closure for public-safe static owner-edge search.

This does not globally prove that no decisive edge exists. It records whether the
currently durable, preregistered public-safe surfaces yielded one.
"""
from __future__ import annotations

REQUIRED_SURFACES = {
    "exact_target_p1p2",
    "transition_object",
    "transition_graph",
    "owner_scope_matrix",
    "supabase_boundary_query",
    "drive_boundary_query",
}


def close_bounded_search(surfaces: list[dict]) -> dict:
    by_name = {surface.get("name"): surface for surface in surfaces}
    missing_surfaces = sorted(REQUIRED_SURFACES - set(by_name))
    decisive: list[dict] = []

    for surface in surfaces:
        for edge in surface.get("decisive_edges", []):
            if (
                edge.get("boundary_id") == "BND_197_TO_195"
                and edge.get("evidence_level") == "LIVE_BOUNDARY_LOCAL"
                and edge.get("explicit") is True
            ):
                decisive.append(edge)

    complete = not missing_surfaces
    if decisive:
        closure_state = "NEW_DECISIVE_EDGE_FOUND"
    elif complete:
        closure_state = "BOUNDED_DURABLE_CORPUS_EXHAUSTED_NO_DECISIVE_EDGE"
    else:
        closure_state = "SEARCH_INCOMPLETE"

    return {
        "searched_surface_count": len(set(by_name) & REQUIRED_SURFACES),
        "required_surface_count": len(REQUIRED_SURFACES),
        "missing_search_surfaces": missing_surfaces,
        "decisive_edge_count": len(decisive),
        "closure_state": closure_state,
        "owner_scope_proven": bool(decisive),
        "semantic_owner": "UNRESOLVED",
        "runtime_dispatch_requested": False,
        "mainline_runtime_gate_change_requested": False,
        "semantic_promotion_count": 0,
    }


def self_test() -> None:
    base = [{"name": name, "decisive_edges": []} for name in sorted(REQUIRED_SURFACES)]
    out = close_bounded_search(base)
    checks = [
        out["searched_surface_count"] == 6,
        out["missing_search_surfaces"] == [],
        out["decisive_edge_count"] == 0,
        out["closure_state"] == "BOUNDED_DURABLE_CORPUS_EXHAUSTED_NO_DECISIVE_EDGE",
        out["runtime_dispatch_requested"] is False
        and out["mainline_runtime_gate_change_requested"] is False,
    ]
    assert all(checks), (checks, out)

    synthetic = base + [
        {
            "name": "synthetic_extra",
            "decisive_edges": [
                {
                    "boundary_id": "BND_197_TO_195",
                    "evidence_level": "LIVE_BOUNDARY_LOCAL",
                    "explicit": True,
                }
            ],
        }
    ]
    assert close_bounded_search(synthetic)["closure_state"] == "NEW_DECISIVE_EDGE_FOUND"
    print("SELF_TEST_PASS 6/6")


if __name__ == "__main__":
    self_test()
