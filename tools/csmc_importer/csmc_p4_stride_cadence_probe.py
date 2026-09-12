#!/usr/bin/env python3
"""Public-safe metadata-only probe for 48/49-qword P4 record cadence.

Consumes an analysis JSON containing ``record_lengths_blocks``. It never reads
CSMC/CLIP payload bytes. The exact-enumeration result is exploratory: the
regularity statistic was chosen after observing the sequence, so it should be
used to prioritize a runtime iterator/packing hypothesis, not as proof of a
semantic record type.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Iterable, Sequence


def one_positions(lengths: Sequence[int], short: int = 48, long: int = 49) -> list[int]:
    allowed = {short, long}
    if not lengths or any(x not in allowed for x in lengths):
        raise ValueError(f"record lengths must contain only {short}/{long}")
    return [i for i, value in enumerate(lengths) if value == long]


def internal_gaps(positions: Sequence[int]) -> list[int]:
    return [b - a for a, b in zip(positions, positions[1:])]


def gap23_regular(lengths: Sequence[int]) -> bool:
    gaps = internal_gaps(one_positions(lengths))
    return bool(gaps) and all(gap in (2, 3) for gap in gaps)


def exact_fixed_class_probability(n: int, k: int) -> tuple[int, int, float]:
    """Enumerate all C(n,k) binary class placements and count gap-{2,3} cases."""
    if not (1 < k < n):
        raise ValueError("require 1 < k < n")
    total = math.comb(n, k)
    regular = 0
    for positions in itertools.combinations(range(n), k):
        gaps = internal_gaps(positions)
        if all(gap in (2, 3) for gap in gaps):
            regular += 1
    return regular, total, regular / total


def analyze(lengths: Sequence[int]) -> dict:
    positions = one_positions(lengths)
    gaps = internal_gaps(positions)
    regular, total, fraction = exact_fixed_class_probability(len(lengths), len(positions))
    five_windows = [sum(lengths[i : i + 5]) for i in range(max(0, len(lengths) - 4))]
    return {
        "analysis": "csmc_p4_stride_cadence_probe_v0.1",
        "scope": "metadata_only_record_lengths",
        "record_count": len(lengths),
        "count_48": sum(v == 48 for v in lengths),
        "count_49": len(positions),
        "record_lengths_blocks": list(lengths),
        "long_record_positions_zero_based": positions,
        "long_record_internal_gaps": gaps,
        "all_internal_gaps_in_2_or_3": all(g in (2, 3) for g in gaps),
        "five_record_sliding_sum_counts": {
            str(value): five_windows.count(value) for value in sorted(set(five_windows))
        },
        "fixed_class_exact_enumeration": {
            "assignments": total,
            "assignments_with_all_internal_gaps_2_or_3": regular,
            "fraction": fraction,
        },
        "interpretation": {
            "safe_claim": (
                "The observed 48/49 length sequence is unusually evenly spaced under a "
                "uniform fixed-class-placement reference model. This supports testing a "
                "serializer iterator/packing cadence that advances by 0x180/0x188 bytes."
            ),
            "guardrail": (
                "Exploratory statistic selected after observing the sequence; it does not "
                "prove a semantic subtype, geometry meaning, encryption/compression, or a "
                "Blender import path. Validate on an independent region or runtime branch."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis_json", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    source = json.loads(args.analysis_json.read_text(encoding="utf-8"))
    lengths = source.get("record_lengths_blocks")
    if not isinstance(lengths, list):
        raise SystemExit("analysis JSON has no record_lengths_blocks list")
    result = analyze([int(v) for v in lengths])
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
