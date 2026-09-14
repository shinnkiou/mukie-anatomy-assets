#!/usr/bin/env python3
"""Synthetic-only tests for the public-safe numeric candidate probe."""
import numpy as np

from csmc_numeric_candidate_probe import analyze_region


def _find(out, dtype, shift=0):
    for row in out["candidates"]:
        if row["dtype"] == dtype and row["byte_shift"] == shift:
            return row
    raise AssertionError((dtype, shift))


def test_weight_like_groups_are_reported_without_semantic_promotion():
    raw = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.5, 0.5, 0.0, 0.0],
            [0.25, 0.25, 0.25, 0.25],
        ],
        dtype="<f4",
    ).tobytes()
    out = analyze_region(raw, absolute_offset=0, max_shift=0)
    assert out["semantic_promotion"] is False
    row = _find(out, "f32_le", 0)
    assert row["metrics"]["finite_ratio"] == 1.0
    assert row["metrics"]["group4_sum_near_1_fraction"] == 1.0


def test_quaternion_like_norm_is_only_a_candidate_signal():
    raw = np.array(
        [[0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 1.0, 0.0]], dtype="<f4"
    ).tobytes()
    out = analyze_region(raw, max_shift=0)
    row = _find(out, "f32_le", 0)
    assert row["metrics"]["quaternion_norm_near_1_fraction"] == 1.0
    assert out["semantic_promotion"] is False


def test_known_index_range_can_be_scored():
    raw = np.array([0, 1, 2, 2, 3, 0], dtype="<u2").tobytes()
    out = analyze_region(raw, known_vertex_count=4, known_bone_count=4, max_shift=0)
    row = _find(out, "u16_le", 0)
    assert row["metrics"]["index_within_vertex_count_fraction"] == 1.0
    assert row["metrics"]["index_within_bone_count_fraction"] == 1.0
    assert out["semantic_promotion"] is False


def test_matrix_affine_candidate_signal():
    raw = np.eye(4, dtype="<f4").tobytes()
    out = analyze_region(raw, max_shift=0)
    row = _find(out, "f32_le", 0)
    assert row["metrics"]["matrix4_affine_row_candidate_fraction"] == 1.0
    assert row["metrics"]["matrix4_affine_col_candidate_fraction"] == 1.0
    assert out["semantic_promotion"] is False
