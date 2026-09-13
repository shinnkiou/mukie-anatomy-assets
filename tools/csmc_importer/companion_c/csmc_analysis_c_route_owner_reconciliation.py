#!/usr/bin/env python3
"""C-043: reconcile public-safe file routes with boundary owner scope.

This module deliberately separates outer payload routing from semantic owner identity.
It consumes public-safe metadata only and never promotes CSMC semantics.
"""
from __future__ import annotations

REQUIRED_DIRECT_ROUTES = {
    "Canvas3DModelLoader.ModelData": "catalog_character",
    "Manager3DOd.SceneData": "scene",
}


def reconcile_route_graph(facts: dict) -> dict:
    routes = facts.get("routes", {})
    reasons: list[str] = []
    direct: dict[str, str] = {}

    for name, expected_kind in REQUIRED_DIRECT_ROUTES.items():
        route = routes.get(name, {})
        if route.get("state") != "LIVE_ROWS" or route.get("resolves_kind") != expected_kind:
            reasons.append(f"direct_route_not_verified:{name}")
        else:
            direct[name] = expected_kind

    layer = routes.get("ModelData3D.Layer3DModelData", {})
    if (
        layer.get("state") == "SCHEMA_ONLY"
        and layer.get("physical_table") is False
        and layer.get("row_count") == 0
    ):
        layer_class = "NO_LIVE_ROUTE_SCHEMA_ONLY"
    else:
        layer_class = "UNRESOLVED_OR_LIVE"

    bank = routes.get("Canvas3DModelBank.BankData", {})
    if (
        bank.get("table_state") == "LIVE_ROWS"
        and bank.get("bankdata_physical_column") is False
        and bank.get("first_loader_index") == bank.get("loader_row_id")
        and bank.get("loader_route") == "Canvas3DModelLoader.ModelData"
    ):
        bank_class = "LIVE_INDIRECTION_TO_EXISTING_LOADER_ROUTE"
    else:
        bank_class = "UNRESOLVED_OR_INDEPENDENT"

    independent = sorted(direct)
    if layer_class != "NO_LIVE_ROUTE_SCHEMA_ONLY":
        independent.append("ModelData3D.Layer3DModelData")
    if bank_class != "LIVE_INDIRECTION_TO_EXISTING_LOADER_ROUTE":
        independent.append("Canvas3DModelBank.BankData")

    boundary = facts.get("boundary", {})
    same_owner_support = int(boundary.get("same_owner_support_count", 0) or 0)
    owner_switch_support = int(boundary.get("owner_switch_support_count", 0) or 0)
    if (
        boundary.get("container_route") == "character"
        and same_owner_support > 0
        and owner_switch_support == 0
    ):
        owner_scope = "SAME_HIGHER_LEVEL_OWNER_FAVORED_NOT_PROVEN"
    else:
        owner_scope = "UNRESOLVED"

    return {
        "accepted": not reasons,
        "reasons": reasons,
        "direct_payload_routes": direct,
        "independent_file_route_count": len(independent),
        "independent_file_routes": independent,
        "layer3d_classification": layer_class,
        "bankdata_classification": bank_class,
        "boundary_owner_scope": owner_scope,
        "consumer_scope": boundary.get("consumer_scope", "UNRESOLVED"),
        "semantic_owner": "UNRESOLVED",
        "consumer_function": "UNRESOLVED",
        "semantic_promotion_count": 0,
        "blender_emit_ready": False,
    }


def self_test() -> None:
    facts = {
        "routes": {
            "Canvas3DModelLoader.ModelData": {
                "state": "LIVE_ROWS",
                "resolves_kind": "catalog_character",
            },
            "Manager3DOd.SceneData": {
                "state": "LIVE_ROWS",
                "resolves_kind": "scene",
            },
            "ModelData3D.Layer3DModelData": {
                "state": "SCHEMA_ONLY",
                "physical_table": False,
                "row_count": 0,
            },
            "Canvas3DModelBank.BankData": {
                "table_state": "LIVE_ROWS",
                "bankdata_physical_column": False,
                "first_loader_index": 1,
                "loader_row_id": 1,
                "loader_route": "Canvas3DModelLoader.ModelData",
            },
        },
        "boundary": {
            "container_route": "character",
            "same_owner_support_count": 6,
            "owner_switch_support_count": 0,
            "consumer_scope": "DISTINCT_LOCAL_CHILD_GRAMMAR_CANDIDATE_INSIDE_CHARACTER_ROUTE",
        },
    }
    out = reconcile_route_graph(facts)
    checks = [
        out["accepted"],
        out["independent_file_route_count"] == 2,
        out["layer3d_classification"] == "NO_LIVE_ROUTE_SCHEMA_ONLY",
        out["bankdata_classification"] == "LIVE_INDIRECTION_TO_EXISTING_LOADER_ROUTE",
        out["boundary_owner_scope"] == "SAME_HIGHER_LEVEL_OWNER_FAVORED_NOT_PROVEN",
        out["semantic_owner"] == "UNRESOLVED",
        out["semantic_promotion_count"] == 0 and out["blender_emit_ready"] is False,
    ]
    assert all(checks), (checks, out)
    print("SELF_TEST_PASS 7/7")


if __name__ == "__main__":
    self_test()
