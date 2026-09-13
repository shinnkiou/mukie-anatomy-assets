#!/usr/bin/env python3
"""Classify structural codec-binding scope without changing semantic evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

CONFIRMED = {"CONFIRMED_CODEC_BINDING", "CONFIRMED_SEMANTIC_BINDING"}


def classify_scope(binding_level: str, family_keys: list[str] | None) -> str:
    if binding_level not in CONFIRMED:
        return "UNCONFIRMED"
    keys = [str(x) for x in (family_keys or []) if str(x)]
    if not keys:
        return "ROLE_LEVEL_UNSCOPED"
    if len(set(keys)) == 1:
        return "FAMILY_LOCAL"
    return "CROSS_FAMILY_GENERALIZED"


def analyze(e: dict) -> dict:
    level = str(e.get("binding_level", "NO_BINDING"))
    family_keys = list(e.get("hit_family_keys") or [])
    scope = classify_scope(level, family_keys)
    return {
        "schema_version": "csmc_analysis_c_binding_scope_v1",
        "binding_id": e.get("binding_id"),
        "binding_level": level,
        "binding_scope": scope,
        "distinct_hit_family_count": len(set(str(x) for x in family_keys if str(x))),
        "semantic_state_changed": False,
        "blender_emit_gate_changed": False,
        "runtime_dispatch_requested": False,
        "guardrails": [
            "Binding scope describes structural generality only.",
            "Family-local does not imply a semantic record type.",
            "Cross-family-generalized does not identify geometry, index, transform, material, hierarchy, bone, or weight semantics.",
        ],
    }


def self_test() -> None:
    assert classify_scope("CANDIDATE_CODEC_BINDING", ["F1", "F1"]) == "UNCONFIRMED"
    assert classify_scope("CONFIRMED_CODEC_BINDING", []) == "ROLE_LEVEL_UNSCOPED"
    assert classify_scope("CONFIRMED_CODEC_BINDING", ["F1", "F1"]) == "FAMILY_LOCAL"
    assert classify_scope("CONFIRMED_CODEC_BINDING", ["F1", "F2"]) == "CROSS_FAMILY_GENERALIZED"
    print("SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ns = ap.parse_args()
    if ns.self_test:
        self_test()
        return 0
    if ns.input is None:
        ap.error("input is required unless --self-test is used")
    out = analyze(json.loads(ns.input.read_text(encoding="utf-8")))
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if ns.out:
        ns.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
