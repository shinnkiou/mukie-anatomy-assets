#!/usr/bin/env python3
"""Reconstruct the maximum public-safe I2 positional aggregate from the durable +965 lattice.

This module consumes aggregate metadata only. It never reads private payload bytes.
It combines:
- ordered record lengths and per-record same-position match counts from the durable lattice;
- the already-verified q21..27 control-signature family catalog;
- the already-verified 21-qword stable prefix and no q28+ within-record equality.

The result is deliberately partial when more than one signature remains compatible.
No semantic field names are promoted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

STABLE_PREFIX_BLOCKS = 21
KNOWN_FAMILY_COUNTS: dict[int, dict[str, int]] = {
    48: {"0000110": 7, "0000111": 3, "0001110": 3},
    49: {"0000111": 3, "1000111": 6},
}


def _family_candidates(length_blocks: int, same_position_matches: int) -> list[str]:
    control_ones = same_position_matches - STABLE_PREFIX_BLOCKS
    return sorted(
        sig
        for sig in KNOWN_FAMILY_COUNTS.get(length_blocks, {})
        if sig.count("1") == control_ones
    )


def analyze(lattice: dict, provenance_hash: str) -> dict:
    errors: list[str] = []
    record_count = int(lattice.get("record_count_complete", -1))
    lengths = list(lattice.get("record_lengths_blocks") or [])
    summaries = list(lattice.get("per_record_match_summary") or [])
    five_sums = list(lattice.get("five_record_group_sums_blocks") or [])
    sources = dict(lattice.get("sources") or {})

    if record_count != 22 or len(lengths) != 22 or len(summaries) != 22:
        errors.append("unexpected_record_count")
    if five_sums != [242, 242, 242, 242]:
        errors.append("unexpected_five_record_group_sums")
    if len(lengths) >= 20:
        recomputed = [sum(lengths[g * 5 : g * 5 + 5]) for g in range(4)]
        if recomputed != [242, 242, 242, 242]:
            errors.append("ordered_lengths_do_not_support_four_complete_groups")

    records: list[dict] = []
    for idx, summary in enumerate(summaries):
        try:
            sidx = int(summary["record_index"])
            length = int(summary["length_blocks"])
            matches = int(summary["same_position_matches"])
        except Exception:
            errors.append("malformed_per_record_summary")
            continue
        if sidx != idx:
            errors.append("noncontiguous_record_index")
        if idx >= len(lengths) or int(lengths[idx]) != length:
            errors.append("length_sequence_mismatch")
        candidates = _family_candidates(length, matches)
        if not candidates:
            errors.append(f"no_signature_candidate_at_{idx}")
        in_complete_group = idx < 20 and five_sums == [242, 242, 242, 242]
        records.append({
            "record_index": idx,
            "supergroup_index": idx // 5 if in_complete_group else None,
            "slot_index": idx % 5 if in_complete_group else None,
            "length_blocks": length,
            "same_position_matches": matches,
            "preserve_signature": candidates[0] if len(candidates) == 1 else None,
            "preserve_signature_candidates": candidates,
        })

    ambiguous_indices = [r["record_index"] for r in records if r["preserve_signature"] is None]
    expected_ambiguous = [2, 3, 8, 14, 15, 21]
    if not errors and ambiguous_indices != expected_ambiguous:
        errors.append("unexpected_ambiguity_pattern")

    full_assignment_count = math.comb(len(ambiguous_indices), 3) if len(ambiguous_indices) == 6 else None
    information_lower_bound_bits = math.log2(full_assignment_count) if full_assignment_count else None

    return {
        "schema_version": "csmc_analysis_c_i2_minimal_gap_v1",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "corpus": {
            "corpus_id": "plus965_character_lattice_22r",
            "provenance_hash": provenance_hash,
            "container_route": "character",
            "regime_id": "plus965",
            "source_kinds": [sources.get("a_kind"), sources.get("b_kind")],
            "source_blob_sha256": [sources.get("a_blob_sha256"), sources.get("b_blob_sha256")],
        },
        "records": records,
        "reconstruction": {
            "record_count": len(records),
            "group_slot_rows_deterministic": 20,
            "unassigned_tail_rows": 2,
            "signature_rows_resolved": len(records) - len(ambiguous_indices),
            "signature_rows_ambiguous": len(ambiguous_indices),
            "ambiguous_record_indices": ambiguous_indices,
            "ambiguous_signature_pair": ["0000111", "0001110"],
            "full_signature_assignment_count_after_marginals": full_assignment_count,
            "information_lower_bound_bits": information_lower_bound_bits,
            "sufficient_public_safe_discriminator": {
                "relative_block": 24,
                "alternative_relative_block": 27,
                "records": ambiguous_indices,
                "bits_if_all_six_reported": len(ambiguous_indices),
                "bits_if_family_quota_is_trusted": max(0, len(ambiguous_indices) - 1),
                "recommended": "report all six q24 equality bits plus provenance hash",
            },
        },
        "guardrails": [
            "This reconstruction is structural metadata only.",
            "Do not promote Mesh/Index/UV/Material/Bone/Weight/Transform semantics.",
            "Do not infer either ambiguous signature without a corpus-bound discriminator artifact.",
            "No raw payload bytes are emitted or required.",
        ],
    }


def self_test() -> None:
    lengths = [48,49,48,48,49,48,49,48,48,49,48,49,48,49,48,48,49,48,49,48,49,48]
    matches = [23,24,24,24,25,23,25,23,24,25,23,25,23,24,24,24,25,23,25,23,24,24]
    lattice = {
        "record_count_complete": 22,
        "record_lengths_blocks": lengths,
        "five_record_group_sums_blocks": [242,242,242,242],
        "per_record_match_summary": [
            {"record_index": i, "length_blocks": length, "same_position_matches": matches[i], "off_diagonal_matches": 0}
            for i, length in enumerate(lengths)
        ],
        "sources": {"a_kind":"catalog_character","b_kind":"character","a_blob_sha256":"a"*64,"b_blob_sha256":"b"*64},
    }
    out = analyze(lattice, "sha256:test")
    assert out["valid"] is True, out
    r = out["reconstruction"]
    assert r["signature_rows_resolved"] == 16
    assert r["signature_rows_ambiguous"] == 6
    assert r["ambiguous_record_indices"] == [2,3,8,14,15,21]
    assert r["full_signature_assignment_count_after_marginals"] == 20
    assert r["group_slot_rows_deterministic"] == 20
    assert out["records"][0]["preserve_signature"] == "0000110"
    assert out["records"][1]["preserve_signature"] == "0000111"
    assert out["records"][4]["preserve_signature"] == "1000111"
    assert out["records"][2]["preserve_signature"] is None

    broken = json.loads(json.dumps(lattice))
    broken["per_record_match_summary"][0]["same_position_matches"] = 26
    assert analyze(broken, "sha256:test")["valid"] is False
    print("SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ns = ap.parse_args()
    if ns.self_test:
        self_test()
        return 0
    if ns.input is None:
        ap.error("input required unless --self-test")
    raw = ns.input.read_bytes()
    lattice = json.loads(raw)
    out = analyze(lattice, "sha256:" + hashlib.sha256(raw).hexdigest())
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
