#!/usr/bin/env python3
"""Companion C end-to-end static pipeline gate classifier."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

CONFIRMED_SEMANTIC = "CONFIRMED_SEMANTIC"
CONFIRMED_CODEC_LEVELS = {"CONFIRMED_CODEC_BINDING", "CONFIRMED_SEMANTIC_BINDING"}


def analyze(e: dict) -> dict:
    intake = bool(e.get("intake_accepted"))
    route = str(e.get("route_state", "UNRESOLVED"))
    structural = bool(e.get("structural_ir_valid"))
    codec_level = str(e.get("codec_binding_level", "NO_BINDING"))
    slots = dict(e.get("semantic_slots") or {})

    if not intake:
        stage = "REJECTED_INPUT"
    elif not structural:
        stage = "INTAKE_ONLY"
    elif codec_level not in CONFIRMED_CODEC_LEVELS:
        stage = "STRUCTURAL_ONLY"
    elif not any(v == CONFIRMED_SEMANTIC for v in slots.values()):
        stage = "CODEC_BOUND"
    else:
        stage = "SEMANTIC_PARTIAL"

    geometry_ok = slots.get("geometry") == CONFIRMED_SEMANTIC
    index_ok = slots.get("index") == CONFIRMED_SEMANTIC
    transform_ok = slots.get("transform") == CONFIRMED_SEMANTIC
    hierarchy_ok = slots.get("hierarchy") == CONFIRMED_SEMANTIC
    material_ok = slots.get("material") == CONFIRMED_SEMANTIC

    mesh_emit_ready = intake and structural and geometry_ok and index_ok
    scene_emit_ready = mesh_emit_ready and transform_ok and hierarchy_ok

    return {
        "schema_version": "csmc_analysis_c_pipeline_contract_v1",
        "pipeline_stage": stage,
        "route_state": route,
        "codec_binding_level": codec_level,
        "mesh_emit_ready": mesh_emit_ready,
        "scene_emit_ready": scene_emit_ready,
        "material_ready": material_ok,
        "implicit_semantic_promotion": False,
        "implicit_codec_binding": False,
        "runtime_dispatch_requested": False,
        "guardrails": [
            "Accepted intake never implies codec binding.",
            "Confirmed codec binding never implies semantic binding.",
            "Mesh emit requires independently confirmed geometry and index semantics.",
            "Scene-aware emit additionally requires independently confirmed transform and hierarchy semantics.",
            "Material readiness is reported independently and does not back-propagate into other slots.",
        ],
    }


def self_test() -> None:
    base = {
        "intake_accepted": True,
        "route_state": "LIVE_RESOLVED_EDGE",
        "structural_ir_valid": True,
        "codec_binding_level": "NO_BINDING",
        "semantic_slots": {},
    }
    assert analyze(dict(base, intake_accepted=False))["pipeline_stage"] == "REJECTED_INPUT"
    assert analyze(base)["pipeline_stage"] == "STRUCTURAL_ONLY"
    c = dict(base, codec_binding_level="CONFIRMED_CODEC_BINDING")
    assert analyze(c)["pipeline_stage"] == "CODEC_BOUND"
    m = dict(c, semantic_slots={"geometry": CONFIRMED_SEMANTIC, "index": CONFIRMED_SEMANTIC})
    assert analyze(m)["mesh_emit_ready"] is True and analyze(m)["scene_emit_ready"] is False
    s = dict(m, semantic_slots={"geometry": CONFIRMED_SEMANTIC, "index": CONFIRMED_SEMANTIC, "transform": CONFIRMED_SEMANTIC, "hierarchy": CONFIRMED_SEMANTIC})
    assert analyze(s)["scene_emit_ready"] is True
    print("SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ns = ap.parse_args()
    if ns.self_test:
        self_test()
        return 0
    if ns.input is None:
        ap.error("input required unless --self-test")
    print(json.dumps(analyze(json.loads(ns.input.read_text(encoding="utf-8"))), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
