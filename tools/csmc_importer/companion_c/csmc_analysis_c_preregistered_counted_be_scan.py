#!/usr/bin/env python3
"""Companion C preregistered counted-BE scan for the +965 record lattice.

Public-safe tool: it reads caller-supplied authorized payloads but emits only aggregate
metadata. No payload bytes are written to output.

C-018 protocol invariants:
- exactly 22 preregistered record starts/lengths;
- exactly three non-overlapping structural roles per record:
  stable_prefix qwords 0..20, control_zone qwords 21..27,
  rewritten_tail qword 28 through record end;
- both serialization sides are tested independently;
- no sliding windows and no post-hoc role creation;
- counted BE f64 whole-role fits are rejected by length congruence for these roles;
- counted BE f32 exact-fit requires the leading BE u32 count to equal
  (role_byte_length - 4) / 4;
- recurrence means >=2 exact fits in distinct records for the same side+role.

This tests codec binding only. It never assigns geometry, index, transform, material,
hierarchy, bone, or weight semantics.
"""
from __future__ import annotations

import argparse
import json
import struct
from collections import defaultdict
from pathlib import Path

BLOCK = 8
DELTA_DEFAULT = 965


def parse_ints(text: str) -> list[int]:
    return [int(x.strip(), 0) for x in text.split(",") if x.strip()]


def role_ranges(length_blocks: int) -> dict[str, tuple[int, int]]:
    if length_blocks not in (48, 49):
        raise ValueError(f"preregistered protocol only accepts 48/49-qword records, got {length_blocks}")
    return {
        "stable_prefix": (0, 21),
        "control_zone": (21, 28),
        "rewritten_tail": (28, length_blocks),
    }


def expected_f32_count(byte_length: int) -> int | None:
    if byte_length < 4 or (byte_length - 4) % 4:
        return None
    return (byte_length - 4) // 4


def f64_exact_fit_possible(byte_length: int) -> bool:
    return byte_length >= 4 and (byte_length - 4) % 8 == 0


def inspect_role(blob: bytes) -> dict:
    size = len(blob)
    expected = expected_f32_count(size)
    count = int.from_bytes(blob[:4], "big") if size >= 4 else None
    exact = expected is not None and count == expected
    out = {
        "byte_length": size,
        "be_f64_whole_role_fit_possible": f64_exact_fit_possible(size),
        "expected_be_f32_count": expected,
        "observed_be_u32_count": count,
        "be_f32_exact_fit": exact,
    }
    if exact and expected:
        values = struct.unpack(">" + "f" * expected, blob[4:])
        finite = sum(1 for v in values if v == v and v not in (float("inf"), float("-inf")))
        out["decoded_value_count"] = expected
        out["finite_value_count"] = finite
        out["all_values_finite"] = finite == expected
    return out


def slice_blocks(payload: bytes, start_block: int, begin_rel: int, end_rel: int) -> bytes:
    a = (start_block + begin_rel) * BLOCK
    b = (start_block + end_rel) * BLOCK
    if a < 0 or b > len(payload) or b < a:
        raise ValueError(f"slice outside payload: blocks {start_block + begin_rel}..{start_block + end_rel}")
    return payload[a:b]


def analyze_side(payload: bytes, side: str, starts: list[int], lengths: list[int]) -> list[dict]:
    records = []
    for i, (start, length) in enumerate(zip(starts, lengths)):
        roles = {}
        for role, (a, b) in role_ranges(length).items():
            roles[role] = inspect_role(slice_blocks(payload, start, a, b))
        records.append({
            "record_index": i,
            "side": side,
            "start_block": start,
            "length_blocks": length,
            "roles": roles,
        })
    return records


def summarize(records: list[dict]) -> dict:
    hits: dict[tuple[str, str], list[int]] = defaultdict(list)
    for rec in records:
        for role, result in rec["roles"].items():
            if result["be_f32_exact_fit"]:
                hits[(rec["side"], role)].append(rec["record_index"])

    families = []
    for side in ("left", "right"):
        for role in ("stable_prefix", "control_zone", "rewritten_tail"):
            idxs = hits.get((side, role), [])
            families.append({
                "side": side,
                "role": role,
                "exact_fit_record_indices": idxs,
                "exact_fit_count": len(idxs),
                "recurrent_same_role_exact_fit": len(set(idxs)) >= 2,
            })

    recurrent = [x for x in families if x["recurrent_same_role_exact_fit"]]
    return {
        "trial_cells": len(records) * 3,
        "families": families,
        "recurrent_family_count": len(recurrent),
        "codec_binding_missing_conditions_closed": bool(recurrent),
        "semantic_promotion_count": 0,
    }


def analyze(left: bytes, right: bytes, starts: list[int], lengths: list[int], delta: int) -> dict:
    if len(starts) != 22 or len(lengths) != 22:
        raise ValueError("C-018 is preregistered for exactly 22 complete records")
    if any(x not in (48, 49) for x in lengths):
        raise ValueError("record lengths must be 48 or 49 qwords")

    left_records = analyze_side(left, "left", starts, lengths)
    right_starts = [s + delta for s in starts]
    right_records = analyze_side(right, "right", right_starts, lengths)
    all_records = left_records + right_records
    summary = summarize(all_records)

    return {
        "schema_version": "csmc_analysis_c_preregistered_counted_be_scan_v1",
        "run_id": "C-018",
        "record_count_per_side": 22,
        "sides": 2,
        "roles_per_record": 3,
        "delta_blocks": delta,
        "delta_bytes": delta * BLOCK,
        "roles": {
            "stable_prefix": "qwords 0..20 inclusive (168 B, expected BE-f32 count 41)",
            "control_zone": "qwords 21..27 inclusive (56 B, expected BE-f32 count 13)",
            "rewritten_tail": "qword 28..end (160 B/count39 for 48-qword records; 168 B/count41 for 49-qword records)",
        },
        "search_policy": {
            "sliding_windows": False,
            "post_hoc_roles": False,
            "f64_whole_role_scan": False,
            "reason_f64_excluded": "all preregistered role lengths are 0 mod 8, while 4 + 8*n is 4 mod 8",
            "promotion_rule": ">=2 exact fits in distinct records for the same serialization side and structural role",
        },
        "summary": summary,
        "records": all_records,
        "guardrails": [
            "Codec binding is structural only.",
            "All-value-finite is reported diagnostically but is not used as a promotion gate.",
            "No geometry/index/transform/material/hierarchy/bone/weight semantics may be inferred.",
            "No runtime/MODELER/Worker interaction is performed by this tool.",
        ],
    }


def self_test() -> None:
    # Arithmetic invariants for all preregistered roles.
    expected = {
        168: 41,
        56: 13,
        160: 39,
    }
    for size, count in expected.items():
        assert expected_f32_count(size) == count
        assert not f64_exact_fit_possible(size)

    # Single exact fit is not recurrence; two exact fits in the same family are.
    fake = []
    for side in ("left", "right"):
        for i in range(22):
            fake.append({
                "record_index": i,
                "side": side,
                "roles": {
                    "stable_prefix": {"be_f32_exact_fit": side == "left" and i in (2, 9)},
                    "control_zone": {"be_f32_exact_fit": side == "right" and i == 4},
                    "rewritten_tail": {"be_f32_exact_fit": False},
                },
            })
    s = summarize(fake)
    assert s["recurrent_family_count"] == 1
    assert s["codec_binding_missing_conditions_closed"] is True
    print("SELF_TEST_PASS")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--left", type=Path)
    ap.add_argument("--right", type=Path)
    ap.add_argument("--starts", help="22 comma-separated left-side record start qword indices")
    ap.add_argument("--lengths", help="22 comma-separated record lengths (48 or 49 qwords)")
    ap.add_argument("--delta", type=int, default=DELTA_DEFAULT)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if not (args.left and args.right and args.starts and args.lengths):
        ap.error("--left --right --starts --lengths are required unless --self-test is used")

    result = analyze(
        args.left.read_bytes(),
        args.right.read_bytes(),
        parse_ints(args.starts),
        parse_ints(args.lengths),
        args.delta,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
