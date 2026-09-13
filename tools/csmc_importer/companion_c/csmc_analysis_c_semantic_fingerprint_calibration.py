#!/usr/bin/env python3
"""C-041: calibration-only semantic fingerprint evaluator using known public fixtures.

This module MUST NOT confirm CSMC semantics. It only evaluates detector strength on
known ground-truth fixture observations and emits candidate confidence.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class Rule:
    semantic: str
    signals: frozenset[str]
    relationship_signals: frozenset[str]

RULES = {
    "vertex": Rule("vertex",
        frozenset({"finite_vec3","vec3_compatible_spacing","coherent_bounds","index_topology_crosscheck"}),
        frozenset({"index_topology_crosscheck"})),
    "index": Rule("index",
        frozenset({"integer_scalar","below_vertex_count","triangle_count_divisible_by_3","local_reuse","position_crosscheck"}),
        frozenset({"position_crosscheck"})),
    "uv": Rule("uv",
        frozenset({"float_vec2","typical_uv_range","count_correlates_geometry","material_texture_evidence"}),
        frozenset({"count_correlates_geometry","material_texture_evidence"})),
    "normal": Rule("normal",
        frozenset({"finite_vec3","approximately_unit_length","count_correlates_geometry"}),
        frozenset({"count_correlates_geometry"})),
    "tangent": Rule("tangent",
        frozenset({"float_vec4","xyz_approximately_unit","count_correlates_geometry"}),
        frozenset({"count_correlates_geometry"})),
    "joints": Rule("joints",
        frozenset({"small_integer_vectors","below_joint_count","pairs_with_weights","count_matches_weights"}),
        frozenset({"pairs_with_weights","count_matches_weights"})),
    "weights": Rule("weights",
        frozenset({"nonnegative_vectors","rows_sum_one","pairs_with_joints","count_matches_joints"}),
        frozenset({"pairs_with_joints","count_matches_joints"})),
    "matrix": Rule("matrix",
        frozenset({"sixteen_float_values","finite_values","affine_substructure","repeated_64_byte_records"}),
        frozenset({"repeated_64_byte_records"})),
    "quaternion": Rule("quaternion",
        frozenset({"float_vec4","norm_one","nearby_monotonic_time","smooth_adjacent_angle"}),
        frozenset({"nearby_monotonic_time"})),
    "morph": Rule("morph",
        frozenset({"parallel_vec3_array","same_count_as_base_position","multiple_parallel_targets","morph_weight_animation"}),
        frozenset({"same_count_as_base_position","morph_weight_animation"})),
    "material_routing": Rule("material_routing",
        frozenset({"uv_candidate","image_or_uri_evidence","material_scalar_vector_cluster","explicit_texture_binding"}),
        frozenset({"explicit_texture_binding"})),
}

def evaluate(semantic: str, observed_signals: Iterable[str], *,
             source_context: str, known_ground_truth: bool = False) -> dict:
    if semantic not in RULES:
        return {"accepted":False, "reason":"unknown_semantic", "confidence":"NONE",
                "csmc_semantic_promotion":False}
    rule = RULES[semantic]
    observed = frozenset(observed_signals)
    hits = sorted(rule.signals & observed)
    rel = sorted(rule.relationship_signals & observed)
    n = len(hits)
    confidence = "NONE"
    if n >= 3 and rel:
        confidence = "HIGH"
    elif n >= 2:
        confidence = "MEDIUM"
    elif n >= 1:
        confidence = "LOW"
    calibration_valid = known_ground_truth and source_context in {
        "KHRONOS_SIMPLE_SKIN_CC0",
        "KHRONOS_SIMPLE_MORPH_CC0",
        "KHRONOS_SIMPLE_TEXTURE_CC0",
        "SYNTHETIC_NEGATIVE_CONTROL",
    }
    return {
        "accepted": True,
        "semantic": semantic,
        "matched_signals": hits,
        "relationship_hits": rel,
        "confidence": confidence,
        "calibration_valid": calibration_valid,
        "ground_truth_confirmed_for_fixture": bool(calibration_valid and confidence in {"MEDIUM","HIGH"}),
        "csmc_semantic_promotion": False,
        "note": "Fixture similarity is calibration evidence only; it is not CSMC semantic proof.",
    }

def self_test() -> None:
    cases = [
        ("vertex", {"finite_vec3","vec3_compatible_spacing","coherent_bounds","index_topology_crosscheck"},
         "KHRONOS_SIMPLE_SKIN_CC0", "HIGH"),
        ("index", {"integer_scalar","below_vertex_count","triangle_count_divisible_by_3","position_crosscheck"},
         "KHRONOS_SIMPLE_SKIN_CC0", "HIGH"),
        ("joints", {"small_integer_vectors","below_joint_count","pairs_with_weights","count_matches_weights"},
         "KHRONOS_SIMPLE_SKIN_CC0", "HIGH"),
        ("weights", {"nonnegative_vectors","rows_sum_one","pairs_with_joints","count_matches_joints"},
         "KHRONOS_SIMPLE_SKIN_CC0", "HIGH"),
        ("matrix", {"sixteen_float_values","finite_values","affine_substructure","repeated_64_byte_records"},
         "KHRONOS_SIMPLE_SKIN_CC0", "HIGH"),
        ("quaternion", {"float_vec4","norm_one","nearby_monotonic_time","smooth_adjacent_angle"},
         "KHRONOS_SIMPLE_SKIN_CC0", "HIGH"),
        ("morph", {"parallel_vec3_array","same_count_as_base_position","multiple_parallel_targets","morph_weight_animation"},
         "KHRONOS_SIMPLE_MORPH_CC0", "HIGH"),
        ("uv", {"float_vec2","typical_uv_range","count_correlates_geometry","material_texture_evidence"},
         "KHRONOS_SIMPLE_TEXTURE_CC0", "HIGH"),
        ("material_routing", {"uv_candidate","image_or_uri_evidence","material_scalar_vector_cluster","explicit_texture_binding"},
         "KHRONOS_SIMPLE_TEXTURE_CC0", "HIGH"),
    ]
    for semantic, signals, source, expected in cases:
        out = evaluate(semantic, signals, source_context=source, known_ground_truth=True)
        assert out["confidence"] == expected, (semantic, out)
        assert out["csmc_semantic_promotion"] is False
    neg = evaluate("vertex", {"finite_vec3"}, source_context="CSMC_PLUS965", known_ground_truth=False)
    assert neg["confidence"] == "LOW"
    assert neg["ground_truth_confirmed_for_fixture"] is False
    assert neg["csmc_semantic_promotion"] is False
    unknown = evaluate("not_a_semantic", set(), source_context="CSMC_PLUS965")
    assert unknown["accepted"] is False
    print("SELF_TEST_PASS 11/11")

if __name__ == "__main__":
    self_test()
