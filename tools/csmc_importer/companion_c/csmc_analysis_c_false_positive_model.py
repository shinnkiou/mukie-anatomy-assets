#!/usr/bin/env python3
"""Conservative null model for counted-BE exact-fit recurrence.

No target bytes are consumed. The model assumes a bounded region where either
BE-f32 or BE-f64 exact-length grammar could apply. Under a uniform 32-bit prefix
null, at most two count values can satisfy the bounded length, so p <= 2 / 2^32.
"""
from __future__ import annotations
import argparse
import json
import math


def binomial_tail(n: int, p: float, k_min: int) -> float:
    return sum(math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k)) for k in range(k_min, n + 1))


def analyze(trials: int = 22, possible_widths: int = 2) -> dict:
    p_single = possible_widths / (2 ** 32)
    return {
        "schema_version": "csmc_analysis_c_counted_be_false_positive_v1",
        "trials": trials,
        "possible_widths": possible_widths,
        "per_trial_upper_bound": p_single,
        "at_least_one": binomial_tail(trials, p_single, 1),
        "at_least_two": binomial_tail(trials, p_single, 2),
        "at_least_three": binomial_tail(trials, p_single, 3),
        "assumptions": [
            "32-bit count prefix is modeled as uniform under the null.",
            "At most two count values satisfy a fixed bounded size: one f32 and one f64.",
            "Trials are modeled as independent only for an order-of-magnitude guardrail; real serializer data may be correlated.",
            "Float payload plausibility is not used, making this conservative relative to stricter finite/range checks.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=22)
    ap.add_argument("--possible-widths", type=int, default=2)
    ns = ap.parse_args()
    print(json.dumps(analyze(ns.trials, ns.possible_widths), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
