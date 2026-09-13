#!/usr/bin/env python3
"""Public-safe classifier for CSMC boundary motif aggregate reports.

Consumes only aggregate JSON produced by prior P4 probes. It never reads or emits
payload bytes/qword values. The goal is to distinguish clean local extinction
boundaries from mixed section-level repack/reorder boundaries.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def classify_boundary(b: dict) -> dict:
    old_hits = int(b.get("barrier_matches_old_delta", 0))
    new_hits = int(b.get("barrier_matches_new_delta", 0))
    clip_found = int(b.get("clip_barrier_distinct_found_anywhere_in_csmc", 0))
    csmc_found = int(b.get("csmc_barrier_distinct_found_anywhere_in_clip", 0))
    extinction = bool(b.get("complete_cross_serialization_extinction", False))

    if extinction and old_hits == 0 and new_hits == 0 and clip_found == 0 and csmc_found == 0:
        cls = "LOCAL_EXTINCTION_CANDIDATE"
    elif old_hits + new_hits > 0 or clip_found + csmc_found > 0:
        cls = "MIXED_REUSE_REPACK_CANDIDATE"
    else:
        cls = "UNRESOLVED_BOUNDARY"

    clip_q = max(int(b.get("clip_barrier_qwords", 0)), 1)
    return {
        "class": cls,
        "old_delta_barrier_match_density": old_hits / clip_q,
        "new_delta_barrier_match_density": new_hits / clip_q,
        "cross_serialization_survival_distinct": clip_found + csmc_found,
        "net_relative_size_change_bytes": int(b.get("net_relative_size_change_bytes", 0)),
    }


def analyze(report: dict) -> dict:
    boundaries = report.get("boundaries", {})
    classified = {name: classify_boundary(data) for name, data in sorted(boundaries.items())}
    counts: dict[str, int] = {}
    for item in classified.values():
        counts[item["class"]] = counts.get(item["class"], 0) + 1
    return {
        "schema_version": "csmc_analysis_c_boundary_motif_classifier_v1",
        "boundary_count": len(classified),
        "class_counts": counts,
        "boundaries": classified,
        "universal_complete_extinction_supported": bool(classified) and all(
            item["class"] == "LOCAL_EXTINCTION_CANDIDATE" for item in classified.values()
        ),
        "guardrails": [
            "Aggregate structural classification only.",
            "No geometry/material/rig semantics are assigned.",
            "MIXED_REUSE_REPACK_CANDIDATE does not prove a specific reorder algorithm.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path)
    ns = ap.parse_args()
    result = analyze(json.loads(ns.input.read_text(encoding="utf-8")))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if ns.out:
        ns.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
