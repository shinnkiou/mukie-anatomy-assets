#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path

LEVELS = ["NO_DIRECT_EVIDENCE", "SCHEMA_HINT", "SEMANTIC_CANDIDATE", "CONFIRMED_ENCODING", "CONFIRMED_SEMANTIC"]

def classify(e: dict) -> str:
    if e.get("controlled_differential") and e.get("current_payload_mapping") and e.get("known_input_correlation"):
        return "CONFIRMED_SEMANTIC"
    if e.get("active_observation") and int(e.get("exact_length_fit_count", 0)) > 0 and e.get("decoder_rule"):
        return "CONFIRMED_ENCODING"
    if e.get("active_observation") and e.get("schema_hint") and e.get("pattern_consistent"):
        return "SEMANTIC_CANDIDATE"
    if e.get("schema_hint"):
        return "SCHEMA_HINT"
    return "NO_DIRECT_EVIDENCE"

def analyze(inventory: dict) -> dict:
    rows=[]; counts=Counter(); promoted=[]
    for e in inventory.get("evidence", []):
        row=dict(e)
        level=classify(row)
        row["evidence_level"] = level
        row["semantic_promotion_allowed"] = level == "CONFIRMED_SEMANTIC"
        if row["semantic_promotion_allowed"] and row.get("semantic_slot"):
            promoted.append(row["semantic_slot"])
        counts[level]+=1
        rows.append(row)
    return {
        "schema_version":"csmc_analysis_c_numeric_evidence_matrix_v1",
        "evidence_counts":dict(counts),
        "evidence":rows,
        "semantic_slots_promoted":sorted(set(promoted)),
        "semantic_promotion_count":len(set(promoted)),
        "guardrails":[
            "CONFIRMED_ENCODING proves a codec/grammar on the observed active field only; it does not identify an unrelated CSMC record family.",
            "SCHEMA_HINT from ParamScheme is not proof that the current scene/blob uses the same byte layout.",
            "Semantic promotion requires controlled differential + current-payload mapping + known-input correlation.",
        ],
    }

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("input", type=Path); ap.add_argument("--out", type=Path)
    ns=ap.parse_args(); out=analyze(json.loads(ns.input.read_text(encoding="utf-8")))
    text=json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True)+"\n"
    if ns.out: ns.out.write_text(text, encoding="utf-8")
    else: print(text,end="")
    return 0
if __name__ == "__main__": raise SystemExit(main())
