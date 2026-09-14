#!/usr/bin/env python3
"""Blind-safe post-ranker for generic static-analysis function candidate TSVs.

This helper consumes an analysis_ranking.tsv-like file and re-ranks functions so
that direct target evidence dominates generic call-graph popularity. It contains
no product-specific names, addresses, bytes, or semantic labels.

Candidate ranking is triage only. It never promotes a semantic interpretation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List

COMMON_HELPER_PATTERNS = (
    r"^_?free$",
    r"^_?malloc$",
    r"^_?calloc$",
    r"^_?realloc$",
    r"^memcpy$",
    r"^memmove$",
    r"^memset$",
    r"^atexit$",
    r"^_?alloca_probe$",
    r"^_?cxxthrowexception$",
    r"^__security_check_cookie$",
    r"^_guard_check_icall$",
    r"^__std_type_info_",
    r"^__rtdynamiccast$",
    r"^_init_thread_",
    r"^thunk_",
)
COMMON_HELPER_RE = re.compile("|".join(f"(?:{p})" for p in COMMON_HELPER_PATTERNS), re.I)

TARGET_REASON_PREFIXES = (
    "target_string:",
    "raw_target:",
    "target_symbol:",
    "direct_target:",
)


def _int(value: str | None) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _targets(value: str | None) -> List[str]:
    if not value:
        return []
    return sorted({part.strip() for part in value.split(",") if part.strip()})


def _target_reason_count(reasons: str | None) -> int:
    if not reasons:
        return 0
    total = 0
    for token in reasons.split(","):
        token = token.strip()
        if token.lower().startswith(TARGET_REASON_PREFIXES):
            total += 1
    return total


def score_row(row: Dict[str, str]) -> Dict[str, object]:
    """Return a blind-safe focused score plus transparent score components."""
    name = (row.get("name") or "").strip()
    caller_count = _int(row.get("caller_count"))
    callee_count = _int(row.get("callee_count"))
    original_score = max(0, _int(row.get("score")))
    target_list = _targets(row.get("targets"))
    target_reason_count = _target_reason_count(row.get("reasons"))

    direct_target_count = len(target_list)
    helper_penalty = 1 if COMMON_HELPER_RE.search(name) else 0

    # Direct evidence is intentionally dominant. Generic popularity is a penalty:
    # the more callers a function has, the more likely it is to be a shared helper.
    focused_score = (
        direct_target_count * 10_000.0
        + target_reason_count * 600.0
        + min(callee_count, 64) * 4.0
        + math.log1p(original_score) * 20.0
        - math.log1p(caller_count) * 1_200.0
        - helper_penalty * 20_000.0
    )

    result: Dict[str, object] = dict(row)
    result.update(
        {
            "focused_score": round(focused_score, 3),
            "direct_target_count": direct_target_count,
            "target_reason_count": target_reason_count,
            "common_helper_penalty": helper_penalty,
            "blind_safe": True,
            "semantic_promotion": False,
        }
    )
    return result


def rerank(rows: Iterable[Dict[str, str]]) -> List[Dict[str, object]]:
    scored = [score_row(row) for row in rows]
    scored.sort(
        key=lambda row: (
            -float(row["focused_score"]),
            -int(row["direct_target_count"]),
            str(row.get("address") or ""),
        )
    )
    for rank, row in enumerate(scored, start=1):
        row["focused_rank"] = rank
    return scored


def read_tsv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        raise ValueError("no rows to write")
    preferred = [
        "focused_rank",
        "focused_score",
        "address",
        "name",
        "caller_count",
        "callee_count",
        "targets",
        "direct_target_count",
        "target_reason_count",
        "common_helper_penalty",
        "blind_safe",
        "semantic_promotion",
        "rank",
        "score",
        "reasons",
    ]
    all_keys = set().union(*(row.keys() for row in rows))
    fieldnames = [k for k in preferred if k in all_keys]
    fieldnames.extend(sorted(all_keys - set(fieldnames)))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_metadata(path: Path, input_path: Path, rows: List[Dict[str, object]]) -> None:
    metadata = {
        "schema_version": "blind_safe_static_relevance_ranker_v1",
        "input": input_path.name,
        "row_count": len(rows),
        "blind_safe": True,
        "semantic_promotion": False,
        "product_specific_constants": False,
        "purpose": "candidate triage only; direct evidence over generic call-graph popularity",
    }
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_tsv", type=Path)
    parser.add_argument("--output-tsv", type=Path, default=Path("focused_ranking.tsv"))
    parser.add_argument("--metadata-json", type=Path, default=Path("focused_ranking.meta.json"))
    args = parser.parse_args()

    ranked = rerank(read_tsv(args.input_tsv))
    write_tsv(args.output_tsv, ranked)
    write_metadata(args.metadata_json, args.input_tsv, ranked)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
