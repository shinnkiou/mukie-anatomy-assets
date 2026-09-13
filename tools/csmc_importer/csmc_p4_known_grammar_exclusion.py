#!/usr/bin/env python3
"""Aggregate-only exclusion test for reusing the known +965 whole-record grammar.

No target bytes are read. The test asks whether a bounded region length can be an
exact concatenation of complete 48/49-qword +965 records and whether its observed
cross-serialization preservation behavior is compatible with the known grammar.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "csmc_p4_known_grammar_exclusion_v1"


def compositions(total: int, lengths: tuple[int, ...]) -> list[dict[str, int]]:
    if lengths != (48, 49):
        raise ValueError("this public-safe contract is preregistered for 48/49-qword records")
    out: list[dict[str, int]] = []
    for n49 in range(total // 49 + 1):
        rem = total - 49 * n49
        if rem >= 0 and rem % 48 == 0:
            out.append({"n48": rem // 48, "n49": n49, "record_count": rem // 48 + n49})
    return out


def validate(doc: dict) -> list[str]:
    e: list[str] = []
    if doc.get("schema_version") != SCHEMA:
        e.append("invalid_schema_version")
    if doc.get("boundary_id") != "BND_197_TO_195":
        e.append("unexpected_boundary_id")
    if doc.get("known_record_lengths_qwords") != [48, 49]:
        e.append("unexpected_known_record_lengths")
    if doc.get("known_always_preserved_qwords_per_record") != 23:
        e.append("unexpected_known_preservation_floor")
    for key in ("clip_open_barrier_qwords", "csmc_open_barrier_qwords"):
        try:
            if int(doc[key]) < 0:
                e.append(f"negative_{key}")
        except Exception:
            e.append(f"malformed_{key}")
    if doc.get("barrier_complete_global_qword_extinction") is not True:
        e.append("barrier_extinction_must_be_true")
    try:
        ep = int(doc.get("max_endpoint_qwords_to_test"))
        if ep < 0 or ep > 2:
            e.append("invalid_endpoint_test_width")
    except Exception:
        e.append("malformed_endpoint_test_width")
    guardrails = doc.get("guardrails")
    if not isinstance(guardrails, dict):
        e.append("missing_guardrails")
    else:
        for key in (
            "same_owner_rejected",
            "semantic_owner_confirmed",
            "geometry_confirmed",
            "index_confirmed",
            "runtime_executed",
        ):
            if guardrails.get(key) is not False:
                e.append(f"guardrail_{key}_must_be_false")
    return sorted(set(e))


def analyze(doc: dict) -> dict:
    errors = validate(doc)
    if errors:
        return {"schema_version": "csmc_p4_known_grammar_exclusion_result_v1", "valid": False, "errors": errors}

    lengths = (48, 49)
    max_ep = int(doc["max_endpoint_qwords_to_test"])
    surfaces = {
        "clip": int(doc["clip_open_barrier_qwords"]),
        "csmc": int(doc["csmc_open_barrier_qwords"]),
    }
    length_trials: dict[str, list[dict]] = {}
    any_composition = False
    for name, base in surfaces.items():
        trials = []
        for endpoint_qwords in range(max_ep + 1):
            total = base + endpoint_qwords
            sols = compositions(total, lengths)
            any_composition = any_composition or bool(sols)
            trials.append({
                "open_barrier_qwords": base,
                "endpoint_qwords_included": endpoint_qwords,
                "tested_total_qwords": total,
                "whole_record_compositions": sols,
                "compatible": bool(sols),
            })
        length_trials[name] = trials

    min8 = 8 * min(lengths)
    max7 = 7 * max(lengths)
    all_tested_totals = [t["tested_total_qwords"] for v in length_trials.values() for t in v]
    lies_in_7_to_8_record_impossible_gap = all(max7 < x < min8 for x in all_tested_totals)

    preservation_contradiction = bool(doc["barrier_complete_global_qword_extinction"]) and int(doc["known_always_preserved_qwords_per_record"]) > 0
    whole_record_concat_rejected = (not any_composition) and preservation_contradiction

    return {
        "schema_version": "csmc_p4_known_grammar_exclusion_result_v1",
        "valid": True,
        "boundary_id": doc["boundary_id"],
        "length_trials": length_trials,
        "seven_record_max_qwords": max7,
        "eight_record_min_qwords": min8,
        "all_tested_totals_in_impossible_7_to_8_record_gap": lies_in_7_to_8_record_impossible_gap,
        "known_always_preserved_qwords_per_complete_record": int(doc["known_always_preserved_qwords_per_record"]),
        "barrier_complete_global_qword_extinction": True,
        "preservation_behavior_contradiction": preservation_contradiction,
        "classification": "KNOWN_PLUS965_WHOLE_RECORD_CONCATENATION_REJECTED" if whole_record_concat_rejected else "NOT_EXCLUDED",
        "same_owner_still_possible": True,
        "partial_or_wrapped_use_of_known_grammar_still_possible": True,
        "semantic_promotions": 0,
        "runtime_executed": False,
        "guardrails": [
            "This rejects only exact concatenation of complete known +965 records with the known preservation grammar.",
            "It does not reject a shared higher-level owner, partial records, headers/trailers, or a different child grammar.",
            "It does not identify geometry, indices, codec, serializer function, or Blender import readiness.",
        ],
    }


def fixture() -> dict:
    return {
        "schema_version": SCHEMA,
        "boundary_id": "BND_197_TO_195",
        "known_record_lengths_qwords": [48, 49],
        "known_always_preserved_qwords_per_record": 23,
        "clip_open_barrier_qwords": 380,
        "csmc_open_barrier_qwords": 378,
        "barrier_complete_global_qword_extinction": True,
        "max_endpoint_qwords_to_test": 2,
        "guardrails": {
            "same_owner_rejected": False,
            "semantic_owner_confirmed": False,
            "geometry_confirmed": False,
            "index_confirmed": False,
            "runtime_executed": False,
        },
    }


def self_test() -> None:
    out = analyze(fixture())
    assert out["valid"] is True
    assert out["classification"] == "KNOWN_PLUS965_WHOLE_RECORD_CONCATENATION_REJECTED"
    assert out["all_tested_totals_in_impossible_7_to_8_record_gap"] is True
    assert all(not t["compatible"] for rows in out["length_trials"].values() for t in rows)
    assert out["preservation_behavior_contradiction"] is True
    assert out["same_owner_still_possible"] is True

    positive = fixture()
    positive["clip_open_barrier_qwords"] = 384
    positive["csmc_open_barrier_qwords"] = 384
    positive["max_endpoint_qwords_to_test"] = 0
    positive["barrier_complete_global_qword_extinction"] = True
    out2 = analyze(positive)
    assert out2["valid"] is True
    assert out2["length_trials"]["clip"][0]["compatible"] is True
    assert out2["classification"] == "NOT_EXCLUDED"

    bad = fixture()
    bad["guardrails"]["same_owner_rejected"] = True
    out3 = analyze(bad)
    assert out3["valid"] is False
    print("SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ns = ap.parse_args()
    if ns.self_test:
        self_test(); return 0
    if ns.input is None:
        ap.error("input required unless --self-test")
    print(json.dumps(analyze(json.loads(ns.input.read_text(encoding="utf-8"))), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
