#!/usr/bin/env python3
"""Classify public-safe CSMC correspondence transitions without semantic promotion."""

from __future__ import annotations
import argparse, json
from pathlib import Path

SCHEMA = "csmc_p4_transition_object_v1"


def _ratio(a: int, b: int) -> float:
    den = (abs(a) + abs(b)) / 2.0
    return 0.0 if den == 0 else abs(a - b) / den


def validate(doc: dict) -> list[str]:
    errors = []
    if doc.get("schema_version") != SCHEMA:
        errors.append("invalid_schema_version")
    for key in ("boundary_id", "container_route", "regime_before", "regime_after"):
        if not doc.get(key):
            errors.append(f"missing_{key}")
    if doc.get("container_route") not in {"character", "scene", "unresolved"}:
        errors.append("invalid_container_route")
    for key in ("clip_gap_qwords", "csmc_gap_qwords", "delta_before_qwords", "delta_after_qwords"):
        try:
            val = int(doc[key])
            if key.endswith("gap_qwords") and val < 0:
                errors.append(f"negative_{key}")
        except Exception:
            errors.append(f"malformed_{key}")
    for key in (
        "left_anchor_reused",
        "right_anchor_reused",
        "complete_cross_serialization_extinction",
        "post_regime_recurs_later",
    ):
        if not isinstance(doc.get(key), bool):
            errors.append(f"malformed_{key}")
    pl = doc.get("phase_lock")
    if not isinstance(pl, dict):
        errors.append("missing_phase_lock")
    else:
        for key in ("pre_before", "pre_after", "barrier_before", "barrier_after", "post_before", "post_after"):
            try:
                val = int(pl[key])
                if val < 0:
                    errors.append(f"negative_phase_{key}")
            except Exception:
                errors.append(f"malformed_phase_{key}")
    guardrails = doc.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append("missing_guardrails")
    else:
        required_false = (
            "semantic_owner_confirmed",
            "codec_confirmed",
            "geometry_confirmed",
            "blender_import_confirmed",
            "runtime_trace_executed",
        )
        for key in required_false:
            if guardrails.get(key) is not False:
                errors.append(f"guardrail_{key}_must_be_false")
    return sorted(set(errors))


def analyze(doc: dict) -> dict:
    errors = validate(doc)
    if errors:
        return {"schema_version": "csmc_p4_transition_object_result_v1", "valid": False, "errors": errors}

    cg = int(doc["clip_gap_qwords"])
    sg = int(doc["csmc_gap_qwords"])
    db = int(doc["delta_before_qwords"])
    da = int(doc["delta_after_qwords"])
    pl = doc["phase_lock"]

    identity_holds = (sg - cg) == (da - db)
    asym = _ratio(cg, sg)
    clean_phase_switch = (
        pl["pre_before"] > 0
        and pl["pre_after"] == 0
        and pl["barrier_before"] == 0
        and pl["barrier_after"] == 0
        and pl["post_before"] == 0
        and pl["post_after"] > 0
    )
    bounded_by_reuse = doc["left_anchor_reused"] and doc["right_anchor_reused"]
    local_scale_preserved = asym <= 0.05
    section_repack_signal = asym >= 0.50

    evidence = {
        "offset_gap_identity_holds": identity_holds,
        "symmetric_gap_asymmetry": asym,
        "bounded_by_reused_anchors": bounded_by_reuse,
        "complete_cross_serialization_extinction": doc["complete_cross_serialization_extinction"],
        "clean_phase_switch": clean_phase_switch,
        "post_regime_recurs_later": doc["post_regime_recurs_later"],
        "local_scale_preserved": local_scale_preserved,
        "section_repack_signal": section_repack_signal,
    }

    if (
        identity_holds
        and local_scale_preserved
        and bounded_by_reuse
        and doc["complete_cross_serialization_extinction"]
        and clean_phase_switch
        and doc["post_regime_recurs_later"]
    ):
        structural_class = "LOCAL_LENGTH_CHANGING_CHILD_CANDIDATE"
        owner_scope = "SAME_HIGHER_LEVEL_OWNER_FAVORED_NOT_PROVEN"
        trace_target = "BOUNDARY_TRANSITION_EVENT"
    elif section_repack_signal:
        structural_class = "SECTION_REPACK_OR_REORDER_CANDIDATE"
        owner_scope = "OWNER_CONTINUITY_UNRESOLVED"
        trace_target = "SECTION_ROUTING_EVENT"
    else:
        structural_class = "UNRESOLVED_TRANSITION"
        owner_scope = "OWNER_CONTINUITY_UNRESOLVED"
        trace_target = "NONE_PREREGISTERED"

    return {
        "schema_version": "csmc_p4_transition_object_result_v1",
        "valid": True,
        "boundary_id": doc["boundary_id"],
        "container_route": doc["container_route"],
        "regime_before": doc["regime_before"],
        "regime_after": doc["regime_after"],
        "net_relative_size_change_qwords": da - db,
        "net_relative_size_change_bytes": (da - db) * 8,
        "evidence": evidence,
        "structural_class": structural_class,
        "owner_scope": owner_scope,
        "runtime_trace_target_if_needed": trace_target,
        "semantic_owner": "UNRESOLVED",
        "semantic_promotions": 0,
        "guardrails": [
            "Classification is structural only.",
            "Same higher-level owner is favored only when the full local-child gate passes; it is not proven.",
            "Do not infer compression, encryption, geometry, indices, UVs, materials, bones, weights, or Blender import.",
            "Runtime tracing is not executed by this classifier.",
        ],
    }


def self_test() -> None:
    base = {
        "schema_version": SCHEMA,
        "boundary_id": "BND_197_TO_195",
        "container_route": "character",
        "regime_before": "+197",
        "regime_after": "+195",
        "clip_gap_qwords": 380,
        "csmc_gap_qwords": 378,
        "delta_before_qwords": 197,
        "delta_after_qwords": 195,
        "left_anchor_reused": True,
        "right_anchor_reused": True,
        "complete_cross_serialization_extinction": True,
        "post_regime_recurs_later": True,
        "phase_lock": {"pre_before": 68, "pre_after": 0, "barrier_before": 0, "barrier_after": 0, "post_before": 0, "post_after": 65},
        "guardrails": {
            "semantic_owner_confirmed": False,
            "codec_confirmed": False,
            "geometry_confirmed": False,
            "blender_import_confirmed": False,
            "runtime_trace_executed": False,
        },
    }
    out = analyze(base)
    assert out["valid"] and out["structural_class"] == "LOCAL_LENGTH_CHANGING_CHILD_CANDIDATE"
    assert out["owner_scope"] == "SAME_HIGHER_LEVEL_OWNER_FAVORED_NOT_PROVEN"

    repack = dict(
        base,
        boundary_id="BND_BIG",
        clip_gap_qwords=1325,
        csmc_gap_qwords=269,
        delta_before_qwords=4693615,
        delta_after_qwords=4692559,
        complete_cross_serialization_extinction=False,
        post_regime_recurs_later=False,
        phase_lock={"pre_before": 9, "pre_after": 0, "barrier_before": 0, "barrier_after": 0, "post_before": 0, "post_after": 7},
    )
    out2 = analyze(repack)
    assert out2["valid"] and out2["structural_class"] == "SECTION_REPACK_OR_REORDER_CANDIDATE"

    broken = json.loads(json.dumps(base))
    broken["guardrails"]["geometry_confirmed"] = True
    out3 = analyze(broken)
    assert not out3["valid"] and "guardrail_geometry_confirmed_must_be_false" in out3["errors"]

    mismatch = dict(base, csmc_gap_qwords=379)
    out4 = analyze(mismatch)
    assert out4["valid"] and out4["structural_class"] == "UNRESOLVED_TRANSITION"
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
    doc = json.loads(ns.input.read_text(encoding="utf-8"))
    print(json.dumps(analyze(doc), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
