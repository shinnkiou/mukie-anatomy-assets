#!/usr/bin/env python3
"""Validate and analyze public-safe positional aggregates for Companion C.

This module never needs payload bytes or absolute offsets. It measures association
between structural record family and preregistered five-record supergroup slot.
"""
from __future__ import annotations
import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def family_key(row: dict) -> str:
    return f"{int(row['length_blocks'])}:{row['preserve_signature']}"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    records = list(doc.get("records") or [])
    if not doc.get("corpus_id"):
        errors.append("missing_corpus_id")
    if not doc.get("provenance_hash"):
        errors.append("missing_provenance_hash")
    if doc.get("container_route") not in {"character", "scene", "unresolved"}:
        errors.append("invalid_container_route")
    if not doc.get("regime_id"):
        errors.append("missing_regime_id")

    seen_indices: set[int] = set()
    seen_group_slots: set[tuple[int, int]] = set()
    for row in records:
        try:
            idx = int(row["record_index"])
            length = int(row["length_blocks"])
            sig = str(row["preserve_signature"])
        except Exception:
            errors.append("malformed_record")
            continue
        if idx in seen_indices:
            errors.append("duplicate_record_index")
        seen_indices.add(idx)
        if length not in (48, 49):
            errors.append("unexpected_record_length")
        if len(sig) != 7 or any(c not in "01" for c in sig):
            errors.append("invalid_preserve_signature")

        group = row.get("supergroup_index")
        slot = row.get("slot_index")
        if (group is None) != (slot is None):
            errors.append("partial_group_slot_assignment")
        if group is not None:
            group_i, slot_i = int(group), int(slot)
            if group_i < 0 or slot_i not in range(5):
                errors.append("invalid_group_or_slot")
            key = (group_i, slot_i)
            if key in seen_group_slots:
                errors.append("duplicate_group_slot")
            seen_group_slots.add(key)
    return sorted(set(errors))


def entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((n / total) * math.log2(n / total) for n in counter.values() if n)


def analyze(doc: dict) -> dict:
    errors = validate(doc)
    if errors:
        return {"schema_version":"csmc_analysis_c_positional_aggregate_result_v1","valid":False,"errors":errors}

    assigned = [r for r in doc["records"] if r.get("supergroup_index") is not None]
    slot_counts = Counter(int(r["slot_index"]) for r in assigned)
    family_counts = Counter(family_key(r) for r in assigned)
    joint = Counter((int(r["slot_index"]), family_key(r)) for r in assigned)

    h_slot = entropy(slot_counts)
    h_family = entropy(family_counts)
    h_joint = entropy(joint)
    mi = h_slot + h_family - h_joint

    families_by_slot: dict[int, set[str]] = defaultdict(set)
    slots_by_family: dict[str, set[int]] = defaultdict(set)
    for r in assigned:
        s = int(r["slot_index"])
        f = family_key(r)
        families_by_slot[s].add(f)
        slots_by_family[f].add(s)

    return {
        "schema_version": "csmc_analysis_c_positional_aggregate_result_v1",
        "valid": True,
        "assigned_record_count": len(assigned),
        "unassigned_tail_count": len(doc["records"]) - len(assigned),
        "slot_counts": {str(k): v for k, v in sorted(slot_counts.items())},
        "family_counts": dict(sorted(family_counts.items())),
        "joint_counts": {f"slot{s}|family{f}": n for (s, f), n in sorted(joint.items())},
        "mutual_information_bits": mi,
        "slot_determines_family": all(len(v) == 1 for v in families_by_slot.values()) if assigned else False,
        "family_determines_slot": all(len(v) == 1 for v in slots_by_family.values()) if assigned else False,
        "guardrails": [
            "Association is structural only.",
            "No slot/family may be named Mesh/Index/UV/Material/Bone/Weight without independent evidence.",
            "No raw bytes or absolute offsets are required by this schema.",
        ],
    }


def self_test() -> None:
    rows = []
    sigs = ["0000110","0000111","0001110","0000111","1000111"]
    lens = [48,48,48,49,49]
    for g in range(4):
        for s in range(5):
            rows.append({"record_index":g*5+s,"supergroup_index":g,"slot_index":s,"length_blocks":lens[s],"preserve_signature":sigs[s]})
    rows.extend([
        {"record_index":20,"supergroup_index":None,"slot_index":None,"length_blocks":48,"preserve_signature":"0000110"},
        {"record_index":21,"supergroup_index":None,"slot_index":None,"length_blocks":49,"preserve_signature":"1000111"},
    ])
    doc={"corpus_id":"synthetic","provenance_hash":"sha256:test","container_route":"character","regime_id":"plus965","records":rows}
    out=analyze(doc)
    assert out["valid"] is True
    assert out["assigned_record_count"] == 20
    assert out["unassigned_tail_count"] == 2
    assert out["slot_determines_family"] is True
    assert out["family_determines_slot"] is False  # shared 0000111 across 48/49 remains distinct via length, but slots 1/3 keys differ; this assertion is conservative fixture check
    print("SELF_TEST_PASS")


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ns=ap.parse_args()
    if ns.self_test:
        self_test(); return 0
    if ns.input is None:
        ap.error("input required unless --self-test")
    print(json.dumps(analyze(json.loads(ns.input.read_text(encoding="utf-8"))), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
