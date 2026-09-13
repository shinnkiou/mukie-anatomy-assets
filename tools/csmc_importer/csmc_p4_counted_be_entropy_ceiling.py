from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROLE_SPECS = {
    "record_whole": {"relative_qword": 0, "count_mode": "record_length"},
    "stable_prefix_0_20": {"relative_qword": 0, "count_mode": "fixed", "expected_count": 41},
    "control_zone_21_27": {"relative_qword": 21, "count_mode": "fixed", "expected_count": 13},
    "preserved_island_25_26": {"relative_qword": 25, "count_mode": "fixed", "expected_count": 3},
}


def shannon_entropy_from_counts(counts: list[int]) -> float:
    n = sum(counts)
    if n <= 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in counts if c)


def hmax_fixed_prefix(*, fitting_rows: int, total_rows: int) -> float:
    """Maximum 8-byte-row byte entropy if k rows start 00 00 00 XX.

    A counted-BE f32 exact fit fixes the first four bytes of its role-start
    qword: three zero bytes and one count byte. To produce a conservative
    entropy upper bound, every remaining unconstrained byte is assigned a
    unique byte value distinct from the fixed symbols. With <=176 total bytes,
    the 256-byte alphabet is large enough for this construction.
    """
    k = fitting_rows
    if not 0 <= k <= total_rows:
        raise ValueError("fitting_rows out of range")
    total_bytes = 8 * total_rows
    if k == 0:
        # Every byte can be unique because total_bytes <= 256 for the known 22-row lattice.
        return math.log2(total_bytes)
    free = total_bytes - 4 * k
    return shannon_entropy_from_counts([3 * k, k] + [1] * free)


def hmax_two_count_prefixes(
    *, fitting_rows: int, total_rows: int, class_caps: tuple[int, int]
) -> float:
    """Maximum entropy when the count byte can take either of two values.

    Used for whole 48/49-qword records, where exact counted-f32 shape implies
    count 95 or 97. The three leading zero bytes remain common to every fit.
    We maximize over all feasible splits between the two record-length classes.
    """
    k = fitting_rows
    cap_a, cap_b = class_caps
    if not 0 <= k <= min(total_rows, cap_a + cap_b):
        raise ValueError("fitting_rows out of range")
    if k == 0:
        return math.log2(8 * total_rows)
    free = 8 * total_rows - 4 * k
    best = -1.0
    lo = max(0, k - cap_b)
    hi = min(k, cap_a)
    for a in range(lo, hi + 1):
        b = k - a
        counts = [3 * k]
        if a:
            counts.append(a)
        if b:
            counts.append(b)
        counts.extend([1] * free)
        best = max(best, shannon_entropy_from_counts(counts))
    return best


def max_fits_compatible(
    observed_entropy: float,
    *,
    total_rows: int,
    mode: str,
    class_caps: tuple[int, int] | None = None,
    epsilon: float = 1e-12,
) -> int:
    compatible: list[int] = []
    for k in range(total_rows + 1):
        if mode == "fixed":
            hmax = hmax_fixed_prefix(fitting_rows=k, total_rows=total_rows)
        elif mode == "record_length":
            if class_caps is None:
                raise ValueError("class_caps required for record_length mode")
            hmax = hmax_two_count_prefixes(
                fitting_rows=k,
                total_rows=total_rows,
                class_caps=class_caps,
            )
        else:
            raise ValueError(f"unknown mode: {mode}")
        if hmax + epsilon >= observed_entropy:
            compatible.append(k)
    return max(compatible) if compatible else 0


def analyze_entropy_ceiling(lattice: dict[str, Any]) -> dict[str, Any]:
    lengths = [int(x) for x in lattice["record_lengths_blocks"]]
    total_rows = len(lengths)
    if total_rows <= 0 or 8 * total_rows > 256:
        raise ValueError("this conservative unique-free-byte bound requires 1..32 rows")

    length_counts = Counter(lengths)
    if set(length_counts) != {48, 49}:
        raise ValueError("expected verified 48/49-qword +965 lattice")

    profile = {int(r["relative_block"]): r for r in lattice["relative_equality_profile"]}
    results: list[dict[str, Any]] = []

    for role, spec in ROLE_SPECS.items():
        rel = int(spec["relative_qword"])
        row = profile[rel]
        for surface in ("a", "b"):
            observed = float(row[f"{surface}_byte_entropy"])
            if spec["count_mode"] == "record_length":
                max_hits = max_fits_compatible(
                    observed,
                    total_rows=total_rows,
                    mode="record_length",
                    class_caps=(length_counts[48], length_counts[49]),
                )
                expected_counts = [95, 97]
            else:
                max_hits = max_fits_compatible(
                    observed,
                    total_rows=total_rows,
                    mode="fixed",
                )
                expected_counts = [int(spec["expected_count"])]

            results.append({
                "role": role,
                "surface": surface,
                "relative_qword": rel,
                "observed_byte_entropy": observed,
                "expected_be_f32_counts": expected_counts,
                "max_exact_fit_rows_compatible_with_entropy": max_hits,
                "total_rows": total_rows,
                "regime_global_exact_fit_excluded": max_hits < total_rows,
                "two_or_more_exact_fits_still_possible": max_hits >= 2,
            })

    return {
        "analysis": "csmc_p4_counted_be_entropy_ceiling_v1",
        "scope": "aggregate_metadata_only_no_payload_bytes",
        "record_count": total_rows,
        "record_length_counts": {str(k): v for k, v in sorted(length_counts.items())},
        "assumption": (
            "For an exact counted-BE f32 fit, the role-start qword begins with a 4-byte big-endian count. "
            "Given counts below 256, those four bytes are 00 00 00 XX. The entropy ceiling maximizes all "
            "other bytes adversarially, so exceeding it makes k-or-more exact fits impossible."
        ),
        "results": results,
        "decision": {
            "regime_global_counted_be_f32_binding_excluded_for_all_fixed_roles": all(
                r["regime_global_exact_fit_excluded"] for r in results
            ),
            "minority_same_role_recurrence_still_unresolved": any(
                r["two_or_more_exact_fits_still_possible"] for r in results
            ),
            "semantic_binding_claimed": False,
            "geometry_binding_claimed": False,
        },
        "guardrail": (
            "This is an upper bound from already durable aggregate byte entropy, not a decode result. "
            "It excludes universal/regime-global counted-f32 binding at these role starts but does not "
            "exclude a recurrent minority subfamily."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Bound possible counted-BE f32 exact-fit multiplicity from +965 aggregate byte entropy"
    )
    ap.add_argument("lattice_json")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    lattice = json.loads(Path(args.lattice_json).read_text(encoding="utf-8"))
    out = analyze_entropy_ceiling(lattice)
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
