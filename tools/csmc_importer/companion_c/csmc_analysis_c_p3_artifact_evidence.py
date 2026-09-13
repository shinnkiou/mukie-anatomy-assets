#!/usr/bin/env python3
"""Classify archival P3 controlled-pair discovery evidence.

The classifier operates on aggregate discovery metadata only. It deliberately
separates a runbook/template/reference hit from an executed, interpretable
controlled differential.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_STAGES = ("A0", "C0", "B0")


def classify_candidate(candidate: dict) -> str:
    kind = candidate.get("kind")
    if kind in {"RUNBOOK", "TEMPLATE", "PLAN_REFERENCE"}:
        return "PLAN_ONLY"
    stages = candidate.get("stage_sha256", {})
    diff = candidate.get("c0_vs_b0_diff")
    interpretable = candidate.get("interpretable") is True
    if all(stages.get(s) for s in REQUIRED_STAGES) and diff not in (None, "", {}) and interpretable:
        return "EXECUTED_DIFFERENTIAL_EVIDENCE"
    if any(stages.get(s) for s in REQUIRED_STAGES) or diff not in (None, "", {}):
        return "INCOMPLETE_EXECUTION_EVIDENCE"
    return "NO_EXECUTION_EVIDENCE"


def analyze(discovery: dict) -> dict:
    candidates = []
    counts: dict[str, int] = {}
    for item in discovery.get("candidates", []):
        cls = classify_candidate(item)
        row = dict(item)
        row["classification"] = cls
        candidates.append(row)
        counts[cls] = counts.get(cls, 0) + 1

    executed = counts.get("EXECUTED_DIFFERENTIAL_EVIDENCE", 0)
    return {
        "schema_version": "csmc_analysis_c_p3_artifact_evidence_v1",
        "searched_experiment_ids": list(discovery.get("searched_experiment_ids", [])),
        "store_summary": discovery.get("store_summary", {}),
        "candidate_count": len(candidates),
        "classification_counts": counts,
        "candidates": candidates,
        "executed_interpretable_pair_found": executed > 0,
        "semantic_promotion_allowed": executed > 0,
        "guardrails": [
            "A runbook, template, or canonical mention is not execution evidence.",
            "At minimum A0/C0/B0 hashes, a C0-vs-B0 differential, and interpretable=true are required for semantic promotion.",
            "A negative archival search is scoped to the examined stores and documented naming conventions.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path)
    ns = ap.parse_args()
    result = analyze(json.loads(ns.input.read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if ns.out:
        ns.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
