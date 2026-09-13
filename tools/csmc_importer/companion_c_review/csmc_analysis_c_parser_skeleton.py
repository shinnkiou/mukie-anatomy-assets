#!/usr/bin/env python3
"""Semantics-gated parser skeleton for CSMC Analysis Companion C.

Consumes public-safe aggregate IR only and separates route resolution,
structural normalization, codec catalog annotation, and semantic gating.
No raw payload bytes or Blender mutation are performed.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_EMIT_SLOTS = ("geometry", "index")
CONFIRMED = "CONFIRMED"


def _slot_confirmed(slot: dict[str, Any]) -> bool:
    return (
        slot.get("status") == CONFIRMED
        and bool(slot.get("evidence_ids"))
        and float(slot.get("confidence", 0.0)) > 0.0
    )


def build_parser_state(
    minimal_ir: dict[str, Any],
    owner_map: dict[str, Any],
    numeric_result: dict[str, Any],
    record_owner_result: dict[str, Any],
) -> dict[str, Any]:
    routes = owner_map.get("importer_routes", {})
    semantics = minimal_ir.get("semantic_slots", {})
    confirmed_codecs = list(numeric_result.get("confirmed_encoding_ids", []))
    semantic_promotions = list(numeric_result.get("semantic_slots_promoted", []))

    codec_bindings: list[dict[str, Any]] = []

    character_route = routes.get("character")
    character_regimes = []
    if character_route and record_owner_result.get("coarse_route_correlation", {}).get("route") == "character":
        character_regimes.append(
            {
                "regime_id": "REGIME_PLUS_965",
                "route": "character",
                "semantic_role": "UNRESOLVED",
                "record_family_count": int(record_owner_result.get("record_family_count", 0)),
                "record_instance_count": int(record_owner_result.get("record_instance_count", 0)),
                "internal_section_owner": "UNRESOLVED",
            }
        )

    blocked = []
    for slot_name in REQUIRED_EMIT_SLOTS:
        slot = semantics.get(slot_name, {})
        if not _slot_confirmed(slot):
            blocked.append(slot_name)

    return {
        "schema_version": "csmc_analysis_c_parser_skeleton_v1",
        "stages": [
            "route_resolution",
            "structural_normalization",
            "typed_codec_catalog_annotation",
            "semantic_gate",
        ],
        "route_resolution": {"routes": routes, "route_count": len(routes)},
        "structural_normalization": {
            "boundary_classes": minimal_ir.get("structural_grammar", {}).get("boundary_classes_observed", []),
            "record_families": minimal_ir.get("structural_grammar", {}).get("record_families", []),
            "character_regimes": character_regimes,
        },
        "codec_annotation": {
            "confirmed_codec_catalog": confirmed_codecs,
            "bindings": codec_bindings,
            "binding_count": 0,
            "note": "Confirmed encoding does not bind itself to +965 or another record family.",
        },
        "semantic_gate": {
            "semantic_slots": semantics,
            "semantic_promotions_from_numeric_evidence": semantic_promotions,
            "required_for_blender_geometry_emit": list(REQUIRED_EMIT_SLOTS),
            "blocked_slots": blocked,
            "can_emit_blender_geometry": not blocked,
        },
        "guardrails": [
            "Route kind is not payload semantics.",
            "Structural record family is not a mesh/bone/material type.",
            "Confirmed codec grammar is not a record-family binding.",
            "Blender geometry emission requires CONFIRMED geometry and index slots with evidence IDs.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", required=True, type=Path)
    ap.add_argument("--owner-map", required=True, type=Path)
    ap.add_argument("--numeric-result", required=True, type=Path)
    ap.add_argument("--record-owner-result", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ns = ap.parse_args()
    state = build_parser_state(
        json.loads(ns.ir.read_text(encoding="utf-8")),
        json.loads(ns.owner_map.read_text(encoding="utf-8")),
        json.loads(ns.numeric_result.read_text(encoding="utf-8")),
        json.loads(ns.record_owner_result.read_text(encoding="utf-8")),
    )
    text = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if ns.out:
        ns.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
