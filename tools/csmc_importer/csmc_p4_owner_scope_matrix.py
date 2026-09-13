#!/usr/bin/env python3
"""Public-safe owner-scope evidence matrix for CSMC P4 transitions.

This tool does not decode payloads and does not name semantic owners. It combines
already-verified aggregate structural facts into a fail-closed scope decision.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "csmc_p4_owner_scope_matrix_v1"

REQUIRED_FALSE = (
    "semantic_owner_confirmed",
    "consumer_function_confirmed",
    "geometry_confirmed",
    "index_confirmed",
    "codec_confirmed",
    "runtime_executed",
    "blender_import_confirmed",
)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    if doc.get("schema_version") != SCHEMA:
        errors.append("invalid_schema_version")
    if doc.get("container_route") != "character":
        errors.append("unexpected_container_route")
    b = doc.get("boundary")
    if not isinstance(b, dict) or b.get("boundary_id") != "BND_197_TO_195":
        errors.append("unexpected_boundary")
    else:
        required = (
            "clip_gap_qwords", "csmc_gap_qwords", "net_relative_size_change_bytes",
            "symmetric_gap_asymmetry", "bounded_by_reused_anchors",
            "complete_cross_serialization_extinction", "clean_phase_switch",
            "post_regime_recurs_later",
        )
        for key in required:
            if key not in b:
                errors.append(f"missing_boundary_{key}")
    contrast = doc.get("contrast")
    if not isinstance(contrast, dict):
        errors.append("missing_contrast")
    else:
        if contrast.get("sparse_roundtrip") != "+195->+194->+195":
            errors.append("unexpected_sparse_roundtrip")
        if contrast.get("round_trip_net_relative_size_change_bytes") != 0:
            errors.append("roundtrip_not_zero")
        if contrast.get("delta_change_alone_owner_change") is not False:
            errors.append("delta_change_rule_not_closed")
    grammar = doc.get("known_grammar_exclusion")
    if not isinstance(grammar, dict) or grammar.get("classification") != "KNOWN_PLUS965_WHOLE_RECORD_CONCATENATION_REJECTED":
        errors.append("known_grammar_exclusion_missing")
    guardrails = doc.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append("missing_guardrails")
    else:
        for key in REQUIRED_FALSE:
            if guardrails.get(key) is not False:
                errors.append(f"guardrail_{key}_must_be_false")
    return sorted(set(errors))


def analyze(doc: dict) -> dict:
    errors = validate(doc)
    if errors:
        return {"schema_version": "csmc_p4_owner_scope_matrix_result_v1", "valid": False, "errors": errors}

    b = doc["boundary"]
    support_same_owner: list[str] = []
    support_owner_switch: list[str] = []
    unresolved: list[str] = []

    if b["bounded_by_reused_anchors"]:
        support_same_owner.append("REUSED_ENDPOINTS_BOUND_LOCAL_REWRITE")
    if float(b["symmetric_gap_asymmetry"]) <= 0.01:
        support_same_owner.append("TIGHT_CROSS_SURFACE_GAP_CONSERVATION")
    if b["complete_cross_serialization_extinction"]:
        support_same_owner.append("LOCAL_CHILD_GRAMMAR_DIVERGENCE_COMPATIBLE")
    if b["clean_phase_switch"] and b["post_regime_recurs_later"]:
        support_same_owner.append("ORDERED_PHASE_CONTINUITY_AROUND_LOCAL_GAP")
    if doc["contrast"]["delta_change_alone_owner_change"] is False:
        support_same_owner.append("DELTA_CHANGE_NOT_OWNER_SWITCH_BY_ITSELF")
    if doc["known_grammar_exclusion"].get("same_owner_still_possible") is True:
        support_same_owner.append("KNOWN_PLUS965_PARSER_REUSE_REJECTED_WITHOUT_REJECTING_SHARED_PARENT")

    # No existing static aggregate directly names a new owner at this boundary.
    if doc.get("explicit_new_owner_marker") is True:
        support_owner_switch.append("EXPLICIT_NEW_OWNER_MARKER")
    if doc.get("explicit_parent_record_boundary") is True:
        support_owner_switch.append("EXPLICIT_PARENT_RECORD_BOUNDARY")

    if not doc.get("explicit_parent_record_boundary"):
        unresolved.append("EXPLICIT_PARENT_RECORD_BOUNDARY")
    if not doc.get("explicit_consumer_crossref"):
        unresolved.append("EXPLICIT_CONSUMER_CROSSREF")
    if not doc.get("explicit_parent_length_field"):
        unresolved.append("EXPLICIT_PARENT_LENGTH_FIELD")

    owner_scope = "SAME_HIGHER_LEVEL_OWNER_FAVORED_NOT_PROVEN"
    if support_owner_switch:
        owner_scope = "OWNER_SCOPE_CONFLICTING_EVIDENCE"

    next_static = "SEARCH_EXISTING_PUBLIC_SAFE_METADATA_FOR_PARENT_BOUNDARY_OR_CONSUMER_CROSSREF"
    runtime_gate = "STATIC_NOT_EXHAUSTED"
    if not unresolved:
        runtime_gate = "STATIC_SCOPE_EDGE_RESOLVED"
    elif unresolved == ["EXPLICIT_CONSUMER_CROSSREF"]:
        runtime_gate = "NARROW_RUNTIME_CONSUMER_TRACE_ELIGIBLE"

    return {
        "schema_version": "csmc_p4_owner_scope_matrix_result_v1",
        "valid": True,
        "boundary_id": b["boundary_id"],
        "container_route": doc["container_route"],
        "owner_scope": owner_scope,
        "consumer_scope": "DISTINCT_LOCAL_CHILD_GRAMMAR_CANDIDATE_INSIDE_CHARACTER_ROUTE",
        "same_owner_support": support_same_owner,
        "owner_switch_support": support_owner_switch,
        "missing_decisive_edges": unresolved,
        "next_static_action": next_static,
        "runtime_gate": runtime_gate,
        "semantic_owner": "UNRESOLVED",
        "consumer_function": "UNRESOLVED",
        "semantic_promotions": 0,
        "runtime_executed": False,
    }


def fixture() -> dict:
    return {
        "schema_version": SCHEMA,
        "container_route": "character",
        "boundary": {
            "boundary_id": "BND_197_TO_195",
            "clip_gap_qwords": 380,
            "csmc_gap_qwords": 378,
            "net_relative_size_change_bytes": -16,
            "symmetric_gap_asymmetry": 0.005277044854881266,
            "bounded_by_reused_anchors": True,
            "complete_cross_serialization_extinction": True,
            "clean_phase_switch": True,
            "post_regime_recurs_later": True,
        },
        "contrast": {
            "sparse_roundtrip": "+195->+194->+195",
            "round_trip_net_relative_size_change_bytes": 0,
            "delta_change_alone_owner_change": False,
        },
        "known_grammar_exclusion": {
            "classification": "KNOWN_PLUS965_WHOLE_RECORD_CONCATENATION_REJECTED",
            "same_owner_still_possible": True,
        },
        "explicit_new_owner_marker": False,
        "explicit_parent_record_boundary": False,
        "explicit_consumer_crossref": False,
        "explicit_parent_length_field": False,
        "guardrails": {
            "semantic_owner_confirmed": False,
            "consumer_function_confirmed": False,
            "geometry_confirmed": False,
            "index_confirmed": False,
            "codec_confirmed": False,
            "runtime_executed": False,
            "blender_import_confirmed": False,
        },
    }


def self_test() -> None:
    out = analyze(fixture())
    assert out["valid"] is True
    assert out["owner_scope"] == "SAME_HIGHER_LEVEL_OWNER_FAVORED_NOT_PROVEN"
    assert len(out["same_owner_support"]) == 6
    assert out["owner_switch_support"] == []
    assert out["runtime_gate"] == "STATIC_NOT_EXHAUSTED"
    assert "EXPLICIT_CONSUMER_CROSSREF" in out["missing_decisive_edges"]

    bad = fixture()
    bad["guardrails"]["geometry_confirmed"] = True
    out2 = analyze(bad)
    assert out2["valid"] is False

    conflict = fixture()
    conflict["explicit_new_owner_marker"] = True
    out3 = analyze(conflict)
    assert out3["owner_scope"] == "OWNER_SCOPE_CONFLICTING_EVIDENCE"
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
    print(json.dumps(analyze(json.loads(ns.input.read_text(encoding="utf-8"))), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
