#!/usr/bin/env python3
"""Factor aggregate CSMC record classes into independent structural axes.

Input is the public-safe control-zone grammar summary. No model/payload bytes are
read. The probe quantifies whether record length and preservation signature can be
collapsed to one variable or must remain separate in an importer IR.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path


def entropy(counts) -> float:
    vals = list(counts.values()) if hasattr(counts, "values") else list(counts)
    total = sum(vals)
    if not total:
        return 0.0
    return -sum((n / total) * math.log2(n / total) for n in vals if n)


def analyze(report: dict) -> dict:
    table = report["signature_counts_by_length"]
    joint = {}
    by_length = Counter()
    by_sig = Counter()
    signatures_to_lengths: dict[str, set[int]] = {}

    for length_s, sigs in table.items():
        length = int(length_s)
        for sig, count in sigs.items():
            count = int(count)
            joint[(length, sig)] = count
            by_length[length] += count
            by_sig[sig] += count
            signatures_to_lengths.setdefault(sig, set()).add(length)

    total = sum(joint.values())
    h_l = entropy(by_length)
    h_s = entropy(by_sig)
    h_joint = entropy(joint)
    mi = h_l + h_s - h_joint
    shared = {sig: sorted(vals) for sig, vals in signatures_to_lengths.items() if len(vals) > 1}

    families = [
        {"length_blocks": length, "signature": sig, "count": count}
        for (length, sig), count in sorted(joint.items())
    ]
    return {
        "schema_version": "csmc_analysis_c_record_family_factorization_v1",
        "records": total,
        "observed_joint_families": len(families),
        "families": families,
        "length_entropy_bits": h_l,
        "signature_entropy_bits": h_s,
        "joint_entropy_bits": h_joint,
        "mutual_information_bits": mi,
        "conditional_length_given_signature_bits": h_joint - h_s,
        "conditional_signature_given_length_bits": h_joint - h_l,
        "signatures_shared_across_lengths": shared,
        "length_is_function_of_signature": len(shared) == 0,
        "signature_is_function_of_length": all(len(sigs) == 1 for sigs in table.values()),
        "recommended_ir_axes": ["length_blocks", "preserve_signature"],
        "guardrails": [
            "Structural record-family factorization only.",
            "Do not map a family to Mesh/Index/UV/Material/Bone/Weight without independent evidence.",
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
