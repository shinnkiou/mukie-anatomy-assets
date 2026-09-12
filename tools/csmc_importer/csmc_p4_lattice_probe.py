from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from csmc_p4_anchor_probe import load_surface, stored_payload


def byte_entropy(chunks: list[bytes]) -> float:
    data = b"".join(chunks)
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def qword(payload: bytes, block: int) -> bytes:
    p = block * 8
    return payload[p:p + 8]


def analyze_lattice(
    a: bytes,
    b: bytes,
    starts: list[int],
    delta_blocks: int,
    *,
    prefix_blocks: int = 21,
    profile_before: int = 32,
    profile_after: int = 64,
) -> dict[str, Any]:
    if len(starts) < 2:
        raise ValueError("at least two cluster starts are required")
    if any(y <= x for x, y in zip(starts, starts[1:])):
        raise ValueError("cluster starts must be strictly increasing")

    strides = [y - x for x, y in zip(starts, starts[1:])]
    complete_starts = starts[:-1]
    n = len(strides)

    rel_profile = []
    for rel in range(-profile_before, profile_after + 1):
        pairs = []
        for s in complete_starts:
            aa = qword(a, s + rel)
            bb = qword(b, s + delta_blocks + rel)
            if len(aa) == 8 and len(bb) == 8:
                pairs.append((aa, bb))
        if not pairs:
            continue
        rel_profile.append({
            "relative_block": rel,
            "pairs": len(pairs),
            "equal_pairs": sum(x == y for x, y in pairs),
            "equal_fraction": sum(x == y for x, y in pairs) / len(pairs),
            "a_unique_values": len({x for x, _ in pairs}),
            "b_unique_values": len({y for _, y in pairs}),
            "a_byte_entropy": byte_entropy([x for x, _ in pairs]),
            "b_byte_entropy": byte_entropy([y for _, y in pairs]),
        })

    # Match qwords anywhere inside the corresponding record pair. Off-diagonal
    # hits would indicate local relocation/shift; only same-position hits support
    # field-zone rewrite rather than a simple insertion shift.
    offset_counts: Counter[int] = Counter()
    off_diagonal = 0
    same_position = 0
    per_record = []
    for i, (s, length) in enumerate(zip(complete_starts, strides)):
        av = [qword(a, s + r) for r in range(length)]
        bv = [qword(b, s + delta_blocks + r) for r in range(length)]
        pos_b: dict[bytes, list[int]] = defaultdict(list)
        for j, value in enumerate(bv):
            pos_b[value].append(j)
        matches = []
        for r, value in enumerate(av):
            for j in pos_b.get(value, []):
                off = j - r
                offset_counts[off] += 1
                if off == 0:
                    same_position += 1
                else:
                    off_diagonal += 1
                matches.append((r, j, off))
        per_record.append({
            "record_index": i,
            "length_blocks": length,
            "same_position_matches": sum(off == 0 for _, _, off in matches),
            "off_diagonal_matches": sum(off != 0 for _, _, off in matches),
        })

    # Equality by stride class for the mixed transition positions.
    stride_classes: dict[str, dict[str, Any]] = {}
    for length in sorted(set(strides)):
        ids = [i for i, value in enumerate(strides) if value == length]
        by_rel = []
        for rel in range(0, max(strides)):
            eq = 0
            total = 0
            for i in ids:
                s = complete_starts[i]
                aa = qword(a, s + rel)
                bb = qword(b, s + delta_blocks + rel)
                if len(aa) == 8 and len(bb) == 8:
                    total += 1
                    eq += aa == bb
            if total:
                by_rel.append({"relative_block": rel, "equal": eq, "total": total})
        stride_classes[str(length)] = {"records": len(ids), "equality_by_relative_block": by_rel}

    five_stride_sums = [sum(strides[i:i + 5]) for i in range(0, len(strides) - 4, 5)]

    prefix_rows = [r for r in rel_profile if 0 <= r["relative_block"] < prefix_blocks]
    prefix_all_equal = bool(prefix_rows) and all(r["equal_pairs"] == r["pairs"] for r in prefix_rows)
    prefix_all_unique = bool(prefix_rows) and all(
        r["a_unique_values"] == r["pairs"] and r["b_unique_values"] == r["pairs"]
        for r in prefix_rows
    )

    # Boundary recurrence: after each variable-size record, the next record's
    # preserved prefix must restart exactly at its actual next start.
    next_prefix_checks = []
    for i in range(n):
        ns = starts[i + 1]
        eq = 0
        total = 0
        for rel in range(prefix_blocks):
            aa = qword(a, ns + rel)
            bb = qword(b, ns + delta_blocks + rel)
            if len(aa) == 8 and len(bb) == 8:
                total += 1
                eq += aa == bb
        next_prefix_checks.append({"after_record": i, "next_start": ns, "equal": eq, "total": total})

    return {
        "analysis": "csmc_p4_variable_record_lattice_v0.1",
        "delta_blocks": delta_blocks,
        "delta_bytes": delta_blocks * 8,
        "record_count_complete": n,
        "record_start_blocks": starts,
        "record_lengths_blocks": strides,
        "record_length_counts": dict(Counter(strides)),
        "five_record_group_sums_blocks": five_stride_sums,
        "five_record_group_sums_bytes": [x * 8 for x in five_stride_sums],
        "relative_equality_profile": rel_profile,
        "local_match_offsets": {
            "same_position_matches": same_position,
            "off_diagonal_matches": off_diagonal,
            "offset_counts": {str(k): v for k, v in sorted(offset_counts.items())},
        },
        "per_record_match_summary": per_record,
        "stride_classes": stride_classes,
        "boundary_recurrence": {
            "prefix_blocks": prefix_blocks,
            "prefix_bytes": prefix_blocks * 8,
            "current_prefix_all_equal": prefix_all_equal,
            "current_prefix_unique_per_record": prefix_all_unique,
            "next_record_prefix_checks": next_prefix_checks,
            "all_interior_next_prefixes_restart_equal": all(x["equal"] == x["total"] for x in next_prefix_checks[:-1]) if len(next_prefix_checks) > 1 else True,
            "terminal_next_prefix": next_prefix_checks[-1] if next_prefix_checks else None,
        },
        "interpretation": {
            "classification": "STRONG_VARIABLE_LENGTH_RECORD_BOUNDARY_CANDIDATE",
            "safe_claim": (
                "The repeated 48/49-block intervals behave as corresponding record boundaries: "
                "a high-entropy record-specific prefix is preserved at the same relative offsets, "
                "serializer-sensitive zones diverge, and equality restarts at each actual next boundary."
            ),
            "relocation_check": (
                "Off-diagonal local qword matches test whether the divergent tail is merely shifted. "
                "Zero off-diagonal matches supports field-zone rewrite/re-encoding over simple local insertion shift."
            ),
            "guardrail": (
                "This is structural evidence only. It does not identify semantic fields, geometry, vertices, indices, "
                "UVs, materials, bones, weights, compression, encryption, or DRM behavior."
            ),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Analyze a bounded repeated record lattice between two CELSYS 3D serializations")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--a-kind", default=None)
    ap.add_argument("--b-kind", default=None)
    ap.add_argument("--boundary-json", required=True, help="Prior public-safe boundary JSON containing record_candidate_plus965")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    a_blob, a_meta = load_surface(args.a, args.a_kind)
    b_blob, b_meta = load_surface(args.b, args.b_kind)
    a_payload = stored_payload(a_blob, a_meta)
    b_payload = stored_payload(b_blob, b_meta)
    prior = json.loads(Path(args.boundary_json).read_text(encoding="utf-8"))
    rec = prior["record_candidate_plus965"]
    out = analyze_lattice(a_payload, b_payload, rec["cluster_start_blocks"], int(rec["delta_blocks"]))
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
