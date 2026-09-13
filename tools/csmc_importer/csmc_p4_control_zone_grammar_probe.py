#!/usr/bin/env python3
"""Public-safe P4 record control-zone equality grammar probe.

This tool contains no private CELSYS/model bytes. It compares two already-extracted,
8-byte-aligned payloads using caller-supplied record starts, record lengths and a
constant block displacement. The output is aggregate equality metadata only.

It is intentionally semantics-free: equality signatures are structural evidence,
not field/type/geometry identification.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


def parse_ints(text: str) -> list[int]:
    return [int(x.strip(), 0) for x in text.split(",") if x.strip()]


def block(payload: bytes, index: int, width: int = 8) -> bytes:
    a = index * width
    b = a + width
    if a < 0 or b > len(payload):
        raise ValueError(f"block {index} outside payload ({len(payload)} bytes)")
    return payload[a:b]


def equality_signature(
    left: bytes,
    right: bytes,
    start: int,
    delta: int,
    relative_blocks: Iterable[int],
) -> str:
    return "".join(
        "1" if block(left, start + r) == block(right, start + delta + r) else "0"
        for r in relative_blocks
    )


def analyze(
    left: bytes,
    right: bytes,
    starts: list[int],
    lengths: list[int],
    delta: int,
    relative_blocks: list[int],
    stable_prefix_blocks: int = 21,
) -> dict:
    if len(starts) != len(lengths):
        raise ValueError("starts and lengths must have the same item count")
    if not starts:
        raise ValueError("at least one record is required")

    records = []
    by_length: dict[int, Counter[str]] = defaultdict(Counter)
    equality_by_relative = {r: Counter() for r in relative_blocks}

    for idx, (start, length) in enumerate(zip(starts, lengths)):
        sig = equality_signature(left, right, start, delta, relative_blocks)
        records.append({"index": idx, "start_block": start, "length_blocks": length, "signature": sig})
        by_length[length][sig] += 1
        for r, bit in zip(relative_blocks, sig):
            equality_by_relative[r]["equal" if bit == "1" else "different"] += 1

    fixed_equal = [
        r for r in relative_blocks
        if equality_by_relative[r]["equal"] == len(records)
    ]
    fixed_different = [
        r for r in relative_blocks
        if equality_by_relative[r]["different"] == len(records)
    ]
    conditional = [r for r in relative_blocks if r not in fixed_equal and r not in fixed_different]

    # Precision/recall of one-way equality and difference markers for each length class.
    marker_rules = []
    lengths_present = sorted(set(lengths))
    for r_idx, r in enumerate(relative_blocks):
        for wanted in ("1", "0"):
            matching = [rec for rec in records if rec["signature"][r_idx] == wanted]
            if not matching:
                continue
            for length in lengths_present:
                tp = sum(1 for rec in matching if rec["length_blocks"] == length)
                if not tp:
                    continue
                total_class = sum(1 for rec in records if rec["length_blocks"] == length)
                precision = tp / len(matching)
                recall = tp / total_class
                if precision == 1.0:
                    marker_rules.append(
                        {
                            "relative_block": r,
                            "condition": "equal" if wanted == "1" else "different",
                            "implies_length_blocks": length,
                            "support": tp,
                            "precision": precision,
                            "recall": recall,
                        }
                    )

    # Test whether any *single bit* in the fully preserved prefix of the left payload
    # perfectly separates a two-class length label. This is only a negative/simple-flag
    # check; absence does not prove the prefix carries no length information.
    perfect_prefix_bits = []
    if len(lengths_present) == 2:
        positive = lengths_present[1]
        labels = [1 if x == positive else 0 for x in lengths]
        for q in range(stable_prefix_blocks):
            for byte_i in range(8):
                vals = [block(left, start + q)[byte_i] for start in starts]
                for bit_i in range(8):
                    xs = [(v >> bit_i) & 1 for v in vals]
                    if xs == labels or [1 - x for x in xs] == labels:
                        perfect_prefix_bits.append(
                            {
                                "relative_block": q,
                                "byte": byte_i,
                                "bit": bit_i,
                                "positive_when_one": xs == labels,
                            }
                        )

    return {
        "schema_version": "csmc_p4_control_zone_grammar_v1",
        "record_count": len(records),
        "delta_blocks": delta,
        "delta_bytes": delta * 8,
        "relative_blocks": relative_blocks,
        "length_counts": {str(k): lengths.count(k) for k in lengths_present},
        "signature_counts_by_length": {
            str(length): dict(sorted(counter.items())) for length, counter in sorted(by_length.items())
        },
        "fixed_equal_relative_blocks": fixed_equal,
        "fixed_different_relative_blocks": fixed_different,
        "conditional_relative_blocks": conditional,
        "one_way_marker_rules": marker_rules,
        "stable_prefix_blocks_checked_for_single_bit_flag": stable_prefix_blocks,
        "perfect_single_bit_prefix_separators": perfect_prefix_bits,
        "records": records,
        "guardrails": [
            "Equality signatures are structural correspondence only.",
            "Do not infer geometry, compression, encryption, or field semantics from this output.",
            "A missing single-bit separator does not prove the stable prefix contains no class information.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--left", required=True, type=Path)
    ap.add_argument("--right", required=True, type=Path)
    ap.add_argument("--starts", required=True, help="comma-separated aligned block starts")
    ap.add_argument("--lengths", required=True, help="comma-separated record lengths in blocks")
    ap.add_argument("--delta", required=True, type=int, help="right_block - left_block")
    ap.add_argument("--relative", default="21,22,23,24,25,26,27")
    ap.add_argument("--stable-prefix-blocks", type=int, default=21)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    result = analyze(
        args.left.read_bytes(),
        args.right.read_bytes(),
        parse_ints(args.starts),
        parse_ints(args.lengths),
        args.delta,
        parse_ints(args.relative),
        args.stable_prefix_blocks,
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
