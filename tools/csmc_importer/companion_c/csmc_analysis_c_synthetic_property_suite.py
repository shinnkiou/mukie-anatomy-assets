#!/usr/bin/env python3
"""C-042: completely synthetic +965-like structural corpus and fail-closed properties.

No proprietary bytes are stored or generated. Values are synthetic integers used
only to exercise the Companion C structural parser contract.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

ALLOWED_FAMILIES = {
    (48, "0000110"),
    (48, "0000111"),
    (48, "0001110"),
    (49, "0000111"),
    (49, "1000111"),
}
FORBIDDEN_EXPORT_KEYS = {"raw_bytes","payload_bytes","hex","absolute_offset","private_payload"}

@dataclass(frozen=True)
class SyntheticRecord:
    record_index: int
    length_blocks: int
    preserve_signature: str
    before: tuple[int, ...]
    after: tuple[int, ...]
    container_route: str = "character"
    owner_state: str = "UNRESOLVED"
    semantic_state: str = "UNRESOLVED"
    scan_protocol: str = "PREDECLARED_FIXED_Q0_QEND"

def make_record(record_index: int, length_blocks: int, signature: str) -> SyntheticRecord:
    if (length_blocks, signature) not in ALLOWED_FAMILIES:
        raise ValueError("unsupported_joint_family")
    before = tuple((record_index + 1) * 100000 + q for q in range(length_blocks))
    after = list(before)
    # q0..20 stable.
    # q21..27 follow the seven-bit preserve signature.
    for bit_index, bit in enumerate(signature):
        q = 21 + bit_index
        if bit == "0":
            after[q] = before[q] + 10_000_000
    # q28+ rewritten.
    for q in range(28, length_blocks):
        after[q] = before[q] + 20_000_000
    return SyntheticRecord(record_index, length_blocks, signature, before, tuple(after))

def validate_record(r: SyntheticRecord) -> list[str]:
    reasons: list[str] = []
    if (r.length_blocks, r.preserve_signature) not in ALLOWED_FAMILIES:
        reasons.append("unknown_joint_family")
    if len(r.before) != r.length_blocks or len(r.after) != r.length_blocks:
        reasons.append("wrong_numeric_width_or_record_length")
        return reasons
    if r.container_route != "character":
        reasons.append("wrong_route")
    if r.owner_state != "UNRESOLVED":
        reasons.append("owner_must_remain_unresolved")
    if r.semantic_state != "UNRESOLVED":
        reasons.append("false_semantic_promotion")
    if r.scan_protocol != "PREDECLARED_FIXED_Q0_QEND":
        reasons.append("post_hoc_window_selection")
    for q in range(21):
        if r.before[q] != r.after[q]:
            reasons.append("stable_prefix_violation")
            break
    actual = "".join("1" if r.before[q] == r.after[q] else "0" for q in range(21, 28))
    if actual != r.preserve_signature:
        reasons.append("preserve_signature_mismatch")
    # Known invariant: q22-23 rewritten; q25-26 preserved.
    if actual[1:3] != "00":
        reasons.append("q22_q23_rewrite_invariant_broken")
    if actual[4:6] != "11":
        reasons.append("q25_q26_preserve_invariant_broken")
    if any(r.before[q] == r.after[q] for q in range(28, r.length_blocks)):
        reasons.append("rewrite_tail_violation")
    return reasons

def public_safe_export(r: SyntheticRecord) -> dict[str, Any]:
    out = {
        "record_index": r.record_index,
        "length_blocks": r.length_blocks,
        "preserve_signature": r.preserve_signature,
        "container_route": r.container_route,
        "owner_state": r.owner_state,
        "semantic_state": r.semantic_state,
        "scan_protocol": r.scan_protocol,
    }
    if set(out) & FORBIDDEN_EXPORT_KEYS:
        raise AssertionError("raw_byte_leakage")
    return out

def validate_corpus(records: list[SyntheticRecord]) -> dict:
    reasons: list[str] = []
    families = set()
    for r in records:
        rr = validate_record(r)
        if rr:
            reasons.extend(f"record_{r.record_index}:{x}" for x in rr)
        families.add((r.length_blocks, r.preserve_signature))
    if len(families) < 5:
        reasons.append("family_collapse")
    return {
        "accepted": not reasons,
        "reasons": reasons,
        "family_count": len(families),
        "semantic_promotions": 0,
        "blender_emit_ready": False,
    }

def self_test() -> None:
    fams = sorted(ALLOWED_FAMILIES)
    good = [make_record(i, *fam) for i, fam in enumerate(fams)]
    checks = []
    checks.append(validate_corpus(good)["accepted"] is True)
    checks.append(validate_corpus(good)["family_count"] == 5)
    try:
        make_record(9, 47, "0000110")
        checks.append(False)
    except ValueError:
        checks.append(True)
    bad_route = SyntheticRecord(**{**asdict(good[0]), "container_route":"scene"})
    checks.append("wrong_route" in validate_record(bad_route))
    bad_owner = SyntheticRecord(**{**asdict(good[0]), "owner_state":"MeshOwner"})
    checks.append("owner_must_remain_unresolved" in validate_record(bad_owner))
    bad_sem = SyntheticRecord(**{**asdict(good[0]), "semantic_state":"GEOMETRY_CONFIRMED"})
    checks.append("false_semantic_promotion" in validate_record(bad_sem))
    bad_scan = SyntheticRecord(**{**asdict(good[0]), "scan_protocol":"POST_HOC_BEST_WINDOW"})
    checks.append("post_hoc_window_selection" in validate_record(bad_scan))
    mutated_after = list(good[0].after); mutated_after[25] += 1
    bad_sig = SyntheticRecord(**{**asdict(good[0]), "after":tuple(mutated_after)})
    checks.append("preserve_signature_mismatch" in validate_record(bad_sig))
    mutated_prefix = list(good[0].after); mutated_prefix[3] += 1
    bad_prefix = SyntheticRecord(**{**asdict(good[0]), "after":tuple(mutated_prefix)})
    checks.append("stable_prefix_violation" in validate_record(bad_prefix))
    export = public_safe_export(good[0])
    checks.append(not (set(export) & FORBIDDEN_EXPORT_KEYS))
    assert all(checks), checks
    print("SELF_TEST_PASS 10/10")

if __name__ == "__main__":
    self_test()
