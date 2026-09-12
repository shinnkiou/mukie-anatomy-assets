from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from csmc_p4_anchor_probe import load_surface, stored_payload


def _qword(payload: bytes, block: int) -> bytes:
    p = block * 8
    return payload[p:p + 8]


def analyze_tail_rewrites(
    a: bytes,
    b: bytes,
    starts: list[int],
    lengths: list[int],
    delta_blocks: int,
    *,
    tail_start_block: int = 21,
) -> dict[str, Any]:
    if len(starts) != len(lengths):
        raise ValueError("starts and lengths must have equal length")
    if not starts:
        raise ValueError("at least one record is required")

    rewritten: list[tuple[int, int, int, bytes, bytes, int]] = []
    class_stats: dict[str, dict[str, Any]] = {}

    for i, (start, length) in enumerate(zip(starts, lengths)):
        if length <= tail_start_block:
            continue
        for rel in range(tail_start_block, length):
            aa = _qword(a, start + rel)
            bb = _qword(b, start + delta_blocks + rel)
            if len(aa) != 8 or len(bb) != 8:
                continue
            if aa == bb:
                continue
            xor = int.from_bytes(aa, "little") ^ int.from_bytes(bb, "little")
            rewritten.append((i, length, rel, aa, bb, xor))

    if not rewritten:
        raise ValueError("no rewritten qwords found in selected tail scope")

    hamming = [x[5].bit_count() for x in rewritten]
    n = len(hamming)
    mean_hamming = sum(hamming) / n
    expected_mean = 32.0
    expected_variance = 16.0
    mean_z = (mean_hamming - expected_mean) / math.sqrt(expected_variance / n)

    equal_bytes = sum(
        sum(aa[j] == bb[j] for j in range(8))
        for _, _, _, aa, bb, _ in rewritten
    )
    total_bytes = n * 8
    p_equal_byte = 1 / 256
    expected_equal_bytes = total_bytes * p_equal_byte
    byte_sd = math.sqrt(total_bytes * p_equal_byte * (1 - p_equal_byte))
    byte_z = (equal_bytes - expected_equal_bytes) / byte_sd

    xor_counts = Counter(x[5] for x in rewritten)

    for length in sorted(set(lengths)):
        rows = [x for x in rewritten if x[1] == length]
        if not rows:
            continue
        hs = [x[5].bit_count() for x in rows]
        eqb = sum(sum(aa[j] == bb[j] for j in range(8)) for _, _, _, aa, bb, _ in rows)
        total = 0
        exact = 0
        for start, rec_len in zip(starts, lengths):
            if rec_len != length:
                continue
            for rel in range(tail_start_block, rec_len):
                aa = _qword(a, start + rel)
                bb = _qword(b, start + delta_blocks + rel)
                if len(aa) == 8 and len(bb) == 8:
                    total += 1
                    exact += aa == bb
        class_stats[str(length)] = {
            "nonexact_qwords": len(rows),
            "hamming_mean": sum(hs) / len(hs),
            "hamming_median": statistics.median(hs),
            "hamming_min": min(hs),
            "hamming_max": max(hs),
            "equal_bytes": eqb,
            "expected_equal_bytes_independent": len(rows) * 8 / 256,
            "tail_qwords_total": total,
            "tail_qwords_exact": exact,
            "tail_qwords_rewritten": total - exact,
        }

    return {
        "analysis": "csmc_p4_tail_rewrite_statistical_profile_v1",
        "scope": {
            "tail_start_relative_qword": tail_start_block,
            "records": len(lengths),
            "delta_blocks": delta_blocks,
            "delta_bytes": delta_blocks * 8,
        },
        "nonexact_qwords": n,
        "hamming_bits": {
            "mean": mean_hamming,
            "sample_variance": statistics.variance(hamming) if n > 1 else 0.0,
            "median": statistics.median(hamming),
            "min": min(hamming),
            "max": max(hamming),
            "expected_independent_mean": expected_mean,
            "expected_independent_variance": expected_variance,
            "mean_z_vs_independent": mean_z,
        },
        "byte_equality": {
            "observed_equal_bytes": equal_bytes,
            "total_compared_bytes": total_bytes,
            "expected_independent_equal_bytes": expected_equal_bytes,
            "z_vs_independent": byte_z,
        },
        "xor_masks": {
            "distinct": len(xor_counts),
            "duplicates": sum(v - 1 for v in xor_counts.values() if v > 1),
            "max_frequency": max(xor_counts.values()),
        },
        "classes": class_stats,
        "interpretation": {
            "safe_claim": (
                "Nonexact tail qwords can be compared against the statistical baseline expected from "
                "independent high-entropy 64-bit values. Agreement with that baseline means only that "
                "simple local arithmetic/byte-preservation models are unsupported."
            ),
            "guardrail": (
                "This does not prove encryption, compression, hashing, a codec, geometry semantics, "
                "or a Blender import path."
            ),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Profile rewritten qwords inside a bounded CSMC/CLIP record family")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--a-kind", default=None)
    ap.add_argument("--b-kind", default=None)
    ap.add_argument("--lattice-json", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--tail-start", type=int, default=21)
    args = ap.parse_args()

    a_blob, a_meta = load_surface(Path(args.a), args.a_kind)
    b_blob, b_meta = load_surface(Path(args.b), args.b_kind)
    a_payload = stored_payload(a_blob, a_meta)
    b_payload = stored_payload(b_blob, b_meta)
    lattice = json.loads(Path(args.lattice_json).read_text(encoding="utf-8"))
    starts_all = [int(x) for x in lattice["record_start_blocks"]]
    lengths = [int(x) for x in lattice["record_lengths_blocks"]]
    starts = starts_all[: len(lengths)]
    out = analyze_tail_rewrites(
        a_payload,
        b_payload,
        starts,
        lengths,
        int(lattice["delta_blocks"]),
        tail_start_block=args.tail_start,
    )
    out["sources"] = {
        "a_blob_sha256": a_meta.blob_sha256,
        "a_kind": a_meta.kind,
        "b_blob_sha256": b_meta.blob_sha256,
        "b_kind": b_meta.kind,
    }
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
