#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path

CODEC_REQS = (
    "current_payload_mapping",
    "bounded_region",
    "confirmed_codec",
    "recurrent_exact_fit",
    "same_structural_role_recurrence",
)
SEMANTIC_REQS = CODEC_REQS + (
    "controlled_differential",
    "known_input_correlation",
    "localized_effect",
    "semantic_slot",
)


def gaps(candidate: dict, semantic: bool = False) -> dict:
    reqs = SEMANTIC_REQS if semantic else CODEC_REQS
    missing = [r for r in reqs if not candidate.get(r, False)]
    return {
        "missing": missing,
        "missing_count": len(missing),
        "satisfied_count": len(reqs) - len(missing),
        "total": len(reqs),
    }


def analyze(candidates: list[dict]) -> dict:
    rows = []
    for c in candidates:
        row = dict(c)
        row["codec_gap"] = gaps(c, False)
        row["semantic_gap"] = gaps(c, True)
        rows.append(row)
    rows.sort(key=lambda r: (r["codec_gap"]["missing_count"], r["semantic_gap"]["missing_count"], r["candidate_id"]))
    return {
        "schema_version": "csmc_analysis_c_binding_gap_vector_v1",
        "candidates": rows,
        "nearest_codec_candidate": rows[0]["candidate_id"] if rows else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path)
    ns = ap.parse_args()
    data = json.loads(ns.input.read_text(encoding="utf-8"))
    out = analyze(data["candidates"])
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if ns.out:
        ns.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
