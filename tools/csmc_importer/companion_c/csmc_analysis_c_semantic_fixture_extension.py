#!/usr/bin/env python3
"""C-049: expand public-safe semantic fingerprint calibration coverage.

Only exact-hashed public fixture metadata is accepted. Fixture calibration never
promotes a CSMC semantic and never enables Blender emission.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from csmc_analysis_c_semantic_fingerprint_calibration import evaluate


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    sha256: str
    license: str
    ground_truth_semantics: frozenset[str]
    layout_tags: frozenset[str]


FIXTURES = {
    "KHRONOS_BUFFER_INTERLEAVED_00": Fixture(
        "KHRONOS_BUFFER_INTERLEAVED_00",
        "ac6289c77338ee278b3dd8838787329483dc09ac37192951f3ec6ede553a54e4",
        "MIT",
        frozenset({"vertex", "index", "uv"}),
        frozenset({"INTERLEAVED_STRIDE_32"}),
    ),
    "KHRONOS_ACCESSOR_SPARSE_00": Fixture(
        "KHRONOS_ACCESSOR_SPARSE_00",
        "098106a42447ac52f43af11450d45a6482259943310861b3e110db0404ae3da4",
        "MIT",
        frozenset({"vertex"}),
        frozenset({"SPARSE_ACCESSOR"}),
    ),
    "KHRONOS_MESH_PRIMITIVE_ATTRIBUTE_06": Fixture(
        "KHRONOS_MESH_PRIMITIVE_ATTRIBUTE_06",
        "57a0e7949aa7d1ed09dc356fcb2ab9ec016245ab61319f07fa9eb9503dac4f4b",
        "MIT",
        frozenset({"uv", "normal", "tangent"}),
        frozenset({"NORMAL_TEXTURE", "VERTEX_NORMAL", "VERTEX_TANGENT"}),
    ),
    "KHRONOS_MATERIAL_MIXED_02": Fixture(
        "KHRONOS_MATERIAL_MIXED_02",
        "3eb7000eb6b9442a998adebd6416a51314d29bbee1f70949e28002c8b7cb8da9",
        "MIT",
        frozenset({"material_routing"}),
        frozenset({"MULTI_PRIMITIVE", "MULTI_MATERIAL"}),
    ),
}


def evaluate_fixture(
    fixture_id: str,
    semantic: str,
    observed_signals: Iterable[str],
    *,
    fixture_sha256: str,
) -> dict:
    fixture = FIXTURES.get(fixture_id)
    if fixture is None:
        return {"accepted": False, "reason": "unknown_fixture", "csmc_semantic_promotion": False}
    if fixture_sha256 != fixture.sha256:
        return {"accepted": False, "reason": "fixture_hash_mismatch", "csmc_semantic_promotion": False}
    if semantic not in fixture.ground_truth_semantics:
        return {"accepted": False, "reason": "semantic_not_ground_truth_for_fixture", "csmc_semantic_promotion": False}

    scored = evaluate(
        semantic,
        observed_signals,
        source_context="C049_PUBLIC_FIXTURE_EXTENSION",
        known_ground_truth=False,
    )
    if not scored.get("accepted"):
        return scored

    return {
        "accepted": True,
        "fixture_id": fixture_id,
        "fixture_sha256": fixture.sha256,
        "license": fixture.license,
        "layout_tags": sorted(fixture.layout_tags),
        "semantic": semantic,
        "base_detector_confidence": scored["confidence"],
        "matched_signals": scored["matched_signals"],
        "relationship_hits": scored["relationship_hits"],
        "fixture_ground_truth_valid": True,
        "csmc_semantic_promotion": False,
        "note": "Known-fixture calibration only; layout tags are negative-control context, not CSMC layout assertions.",
    }


def coverage_summary() -> dict:
    return {
        "fixture_count": len(FIXTURES),
        "fixture_semantics": sorted({s for f in FIXTURES.values() for s in f.ground_truth_semantics}),
        "newly_calibrated_vs_c041": ["normal", "tangent"],
        "layout_negative_controls": [
            "INTERLEAVED_STRIDE_32",
            "SPARSE_ACCESSOR",
            "MULTI_PRIMITIVE",
            "MULTI_MATERIAL",
        ],
        "csmc_semantic_promotion": False,
    }


def self_test() -> None:
    tests = 0

    def expect(fixture_id: str, semantic: str, signals: set[str], confidence: str) -> None:
        nonlocal tests
        out = evaluate_fixture(
            fixture_id,
            semantic,
            signals,
            fixture_sha256=FIXTURES[fixture_id].sha256,
        )
        assert out["accepted"] is True, out
        assert out["base_detector_confidence"] == confidence, out
        assert out["fixture_ground_truth_valid"] is True
        assert out["csmc_semantic_promotion"] is False
        tests += 1

    expect("KHRONOS_MESH_PRIMITIVE_ATTRIBUTE_06", "normal", {"finite_vec3", "approximately_unit_length", "count_correlates_geometry"}, "HIGH")
    expect("KHRONOS_MESH_PRIMITIVE_ATTRIBUTE_06", "tangent", {"float_vec4", "xyz_approximately_unit", "count_correlates_geometry"}, "HIGH")
    expect("KHRONOS_BUFFER_INTERLEAVED_00", "vertex", {"finite_vec3", "vec3_compatible_spacing", "coherent_bounds", "index_topology_crosscheck"}, "HIGH")
    expect("KHRONOS_BUFFER_INTERLEAVED_00", "index", {"integer_scalar", "below_vertex_count", "triangle_count_divisible_by_3", "position_crosscheck"}, "HIGH")
    expect("KHRONOS_BUFFER_INTERLEAVED_00", "uv", {"float_vec2", "typical_uv_range", "count_correlates_geometry"}, "HIGH")
    expect("KHRONOS_ACCESSOR_SPARSE_00", "vertex", {"finite_vec3", "coherent_bounds", "index_topology_crosscheck"}, "HIGH")
    expect("KHRONOS_MATERIAL_MIXED_02", "material_routing", {"uv_candidate", "image_or_uri_evidence", "material_scalar_vector_cluster", "explicit_texture_binding"}, "HIGH")
    expect("KHRONOS_MESH_PRIMITIVE_ATTRIBUTE_06", "normal", {"finite_vec3", "approximately_unit_length"}, "MEDIUM")
    expect("KHRONOS_MESH_PRIMITIVE_ATTRIBUTE_06", "tangent", {"float_vec4", "xyz_approximately_unit"}, "MEDIUM")

    bad_hash = evaluate_fixture(
        "KHRONOS_MESH_PRIMITIVE_ATTRIBUTE_06",
        "normal",
        {"finite_vec3", "approximately_unit_length", "count_correlates_geometry"},
        fixture_sha256="0" * 64,
    )
    assert bad_hash["accepted"] is False and bad_hash["reason"] == "fixture_hash_mismatch"
    assert bad_hash["csmc_semantic_promotion"] is False
    tests += 1

    wrong_semantic = evaluate_fixture(
        "KHRONOS_ACCESSOR_SPARSE_00",
        "weights",
        {"nonnegative_vectors", "rows_sum_one", "pairs_with_joints"},
        fixture_sha256=FIXTURES["KHRONOS_ACCESSOR_SPARSE_00"].sha256,
    )
    assert wrong_semantic["accepted"] is False and wrong_semantic["reason"] == "semantic_not_ground_truth_for_fixture"
    assert wrong_semantic["csmc_semantic_promotion"] is False
    tests += 1

    summary = coverage_summary()
    assert summary["newly_calibrated_vs_c041"] == ["normal", "tangent"]
    assert summary["csmc_semantic_promotion"] is False
    tests += 1

    print(f"SELF_TEST_PASS {tests}/{tests}")


if __name__ == "__main__":
    self_test()
