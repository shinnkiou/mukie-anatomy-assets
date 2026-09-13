#!/usr/bin/env python3
"""Classify side-lane BindingEvidence without dispatching runtime work."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

LEVELS = (
    "NO_BINDING",
    "CANDIDATE_CODEC_BINDING",
    "CONFIRMED_CODEC_BINDING",
    "CONFIRMED_SEMANTIC_BINDING",
)


def classify(e: dict) -> str:
    same_payload = bool(e.get("current_payload_mapping"))
    bounded = bool(e.get("bounded_region_id"))
    codec_confirmed = e.get("codec_evidence_level") == "CONFIRMED_ENCODING"
    exact_fits = int(e.get("exact_decode_fit_instances", 0))
    recurrent_role = bool(e.get("same_structural_role_recurrence"))
    semantic_ready = (
        bool(e.get("controlled_differential"))
        and bool(e.get("known_input_correlation"))
        and bool(e.get("localized_effect"))
        and bool(e.get("semantic_slot"))
    )
    if same_payload and bounded and codec_confirmed and exact_fits >= 2 and recurrent_role:
        if semantic_ready:
            return "CONFIRMED_SEMANTIC_BINDING"
        return "CONFIRMED_CODEC_BINDING"
    if same_payload and bounded and codec_confirmed and exact_fits >= 1:
        return "CANDIDATE_CODEC_BINDING"
    return "NO_BINDING"


def analyze(e: dict) -> dict:
    level = classify(e)
    return {
        "schema_version": "csmc_analysis_c_binding_evidence_contract_v1",
        "binding_id": e.get("binding_id"),
        "binding_level": level,
        "codec_binding_allowed": level in {"CONFIRMED_CODEC_BINDING", "CONFIRMED_SEMANTIC_BINDING"},
        "semantic_promotion_allowed": level == "CONFIRMED_SEMANTIC_BINDING",
        "runtime_dispatch_requested": False,
        "guardrails": [
            "A single exact fit is candidate-only for opaque current payload regions.",
            "Confirmed codec binding requires same current payload mapping, bounded region, independently confirmed codec, recurrent exact fits, and same structural-role recurrence.",
            "Semantic promotion additionally requires controlled differential, known-input correlation, localized effect, and explicit semantic slot.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path)
    ns = ap.parse_args()
    out = analyze(json.loads(ns.input.read_text(encoding="utf-8")))
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if ns.out:
        ns.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
