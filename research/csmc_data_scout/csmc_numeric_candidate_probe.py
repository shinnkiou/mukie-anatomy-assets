#!/usr/bin/env python3
"""
Public-safe numeric candidate probe for opaque binary regions.

This tool does NOT identify proprietary semantics. It only reports numerical
plausibility signals for caller-selected byte ranges. No CSMC/MODELER constants,
offsets, signatures, or proprietary bytes are embedded.

Requires: NumPy
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


DTYPES = {
    "f32_le": np.dtype("<f4"),
    "f32_be": np.dtype(">f4"),
    "f64_le": np.dtype("<f8"),
    "f64_be": np.dtype(">f8"),
    "u16_le": np.dtype("<u2"),
    "u16_be": np.dtype(">u2"),
    "u32_le": np.dtype("<u4"),
    "u32_be": np.dtype(">u4"),
}


def _fraction(mask: np.ndarray) -> float:
    if mask.size == 0:
        return 0.0
    return float(np.count_nonzero(mask) / mask.size)


def _safe_float(v: Any) -> float | None:
    x = float(v)
    return x if math.isfinite(x) else None


def _top_values(arr: np.ndarray, limit: int = 8) -> list[dict[str, Any]]:
    if arr.size == 0:
        return []
    if arr.size > 20000:
        arr = arr[:20000]
    vals = arr.tolist()
    counts = Counter(vals)
    return [
        {"value": (float(k) if isinstance(k, float) else int(k)), "count": int(c)}
        for k, c in counts.most_common(limit)
    ]


def _repeat_period_scores(arr: np.ndarray, max_period: int = 16) -> list[dict[str, Any]]:
    n = min(arr.size, 4096)
    if n < 4:
        return []
    x = arr[:n]
    out: list[dict[str, Any]] = []
    for p in range(1, min(max_period, n // 2) + 1):
        eq = x[p:] == x[:-p]
        out.append({"period_elements": p, "exact_repeat_fraction": _fraction(eq)})
    return sorted(out, key=lambda r: r["exact_repeat_fraction"], reverse=True)[:5]


def _float_metrics(arr: np.ndarray) -> dict[str, Any]:
    x = arr.astype(np.float64, copy=False)
    finite = np.isfinite(x)
    finite_ratio = _fraction(finite)
    fx = x[finite]
    metrics: dict[str, Any] = {
        "finite_ratio": finite_ratio,
        "nan_ratio": _fraction(np.isnan(x)),
        "inf_ratio": _fraction(np.isinf(x)),
    }
    if fx.size == 0:
        return metrics

    absx = np.abs(fx)
    metrics.update(
        {
            "min": _safe_float(np.min(fx)),
            "max": _safe_float(np.max(fx)),
            "mean": _safe_float(np.mean(fx)),
            "std": _safe_float(np.std(fx)),
            "zero_fraction": _fraction(np.isclose(fx, 0.0, atol=1e-7)),
            "unit_interval_fraction": _fraction((fx >= -1e-6) & (fx <= 1.000001)),
            "reasonable_magnitude_fraction": _fraction(absx <= 1e6),
            "tiny_denormal_like_fraction": _fraction((absx > 0) & (absx < 1e-30)),
        }
    )

    for width in (2, 3, 4):
        usable = (fx.size // width) * width
        if usable == 0:
            continue
        g = fx[:usable].reshape(-1, width)
        norms = np.linalg.norm(g, axis=1)
        metrics[f"vec{width}_finite_group_fraction"] = _fraction(np.all(np.isfinite(g), axis=1))
        metrics[f"vec{width}_norm_near_1_fraction"] = _fraction(np.abs(norms - 1.0) <= 1e-3)

    usable4 = (fx.size // 4) * 4
    if usable4:
        g4 = fx[:usable4].reshape(-1, 4)
        sums4 = np.sum(g4, axis=1)
        metrics["group4_sum_near_1_fraction"] = _fraction(np.abs(sums4 - 1.0) <= 1e-4)
        metrics["group4_nonnegative_fraction"] = _fraction(np.all(g4 >= -1e-7, axis=1))
        metrics["quaternion_norm_near_1_fraction"] = _fraction(
            np.abs(np.linalg.norm(g4, axis=1) - 1.0) <= 1e-3
        )

    usable16 = (fx.size // 16) * 16
    if usable16:
        mats = fx[:usable16].reshape(-1, 4, 4)
        row_affine = np.max(
            np.abs(mats[:, 3, :] - np.array([0.0, 0.0, 0.0, 1.0])), axis=1
        )
        col_affine = np.max(
            np.abs(mats[:, :, 3] - np.array([0.0, 0.0, 0.0, 1.0])), axis=1
        )
        metrics["matrix4_affine_row_candidate_fraction"] = _fraction(row_affine <= 1e-3)
        metrics["matrix4_affine_col_candidate_fraction"] = _fraction(col_affine <= 1e-3)

        rot = mats[:, :3, :3]
        gram = np.matmul(np.transpose(rot, (0, 2, 1)), rot)
        eye = np.eye(3)
        err = np.max(np.abs(gram - eye), axis=(1, 2))
        metrics["matrix4_orthonormal_3x3_candidate_fraction"] = _fraction(err <= 1e-2)

    return metrics


def _uint_metrics(
    arr: np.ndarray,
    known_vertex_count: int | None,
    known_bone_count: int | None,
) -> dict[str, Any]:
    x = arr.astype(np.uint64, copy=False)
    metrics: dict[str, Any] = {
        "min": int(np.min(x)) if x.size else None,
        "max": int(np.max(x)) if x.size else None,
        "zero_fraction": _fraction(x == 0),
        "adjacent_nondecreasing_fraction": _fraction(x[1:] >= x[:-1]) if x.size > 1 else 0.0,
        "adjacent_step_le_1_fraction": _fraction(np.diff(x.astype(np.int64)) <= 1)
        if x.size > 1
        else 0.0,
    }
    if known_vertex_count is not None and known_vertex_count > 0:
        metrics["index_within_vertex_count_fraction"] = _fraction(x < known_vertex_count)
    if known_bone_count is not None and known_bone_count > 0:
        metrics["index_within_bone_count_fraction"] = _fraction(x < known_bone_count)
    return metrics


def evaluate_candidate(
    data: bytes,
    dtype_name: str,
    shift: int,
    absolute_offset: int,
    known_vertex_count: int | None,
    known_bone_count: int | None,
    max_samples: int,
) -> dict[str, Any] | None:
    dtype = DTYPES[dtype_name]
    itemsize = dtype.itemsize
    if shift >= len(data):
        return None
    usable_bytes = len(data) - shift
    count = min(usable_bytes // itemsize, max_samples)
    if count <= 0:
        return None
    arr = np.frombuffer(data, dtype=dtype, count=count, offset=shift)

    result: dict[str, Any] = {
        "dtype": dtype_name,
        "byte_shift": shift,
        "absolute_start": absolute_offset + shift,
        "alignment_mod_16": (absolute_offset + shift) % 16,
        "itemsize": itemsize,
        "sample_count": int(arr.size),
        "top_values": _top_values(arr),
        "repeat_period_candidates": _repeat_period_scores(arr),
    }
    if dtype.kind == "f":
        result["metrics"] = _float_metrics(arr)
    else:
        result["metrics"] = _uint_metrics(arr, known_vertex_count, known_bone_count)
    return result


def score_candidate(row: dict[str, Any]) -> float:
    m = row["metrics"]
    if row["dtype"].startswith("f"):
        finite = float(m.get("finite_ratio", 0.0))
        reasonable = float(m.get("reasonable_magnitude_fraction", 0.0))
        denorm_penalty = float(m.get("tiny_denormal_like_fraction", 0.0))
        return max(0.0, min(1.0, 0.55 * finite + 0.45 * reasonable - 0.25 * denorm_penalty))
    score = 0.35
    if "index_within_vertex_count_fraction" in m:
        score += 0.45 * float(m["index_within_vertex_count_fraction"])
    if "index_within_bone_count_fraction" in m:
        score += 0.20 * float(m["index_within_bone_count_fraction"])
    return max(0.0, min(1.0, score))


def analyze_region(
    data: bytes,
    absolute_offset: int = 0,
    known_vertex_count: int | None = None,
    known_bone_count: int | None = None,
    max_samples: int = 20000,
    max_shift: int = 15,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for dtype_name in DTYPES:
        for shift in range(0, min(max_shift, len(data) - 1) + 1):
            row = evaluate_candidate(
                data,
                dtype_name,
                shift,
                absolute_offset,
                known_vertex_count,
                known_bone_count,
                max_samples,
            )
            if row is not None:
                row["generic_numeric_plausibility_score"] = score_candidate(row)
                candidates.append(row)

    candidates.sort(
        key=lambda r: (
            r["generic_numeric_plausibility_score"],
            -r["alignment_mod_16"],
            r["sample_count"],
        ),
        reverse=True,
    )
    return {
        "schema_version": "csmc_public_safe_numeric_candidate_probe_v1",
        "semantic_promotion": False,
        "warning": (
            "Candidate metrics are structural/numeric plausibility signals only. "
            "They do not identify proprietary field meaning, ownership, or consumer."
        ),
        "input_bytes": len(data),
        "absolute_offset": absolute_offset,
        "known_vertex_count": known_vertex_count,
        "known_bone_count": known_bone_count,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--length", type=int)
    ap.add_argument("--known-vertex-count", type=int)
    ap.add_argument("--known-bone-count", type=int)
    ap.add_argument("--max-samples", type=int, default=20000)
    ap.add_argument("--max-shift", type=int, default=15)
    ap.add_argument("--top", type=int, default=24)
    ap.add_argument("--json-out", type=Path)
    ns = ap.parse_args()

    raw = ns.input.read_bytes()
    if ns.offset < 0 or ns.offset > len(raw):
        raise SystemExit("--offset is outside file")
    end = len(raw) if ns.length is None else min(len(raw), ns.offset + max(0, ns.length))
    region = raw[ns.offset:end]

    out = analyze_region(
        region,
        absolute_offset=ns.offset,
        known_vertex_count=ns.known_vertex_count,
        known_bone_count=ns.known_bone_count,
        max_samples=max(1, ns.max_samples),
        max_shift=max(0, min(63, ns.max_shift)),
    )
    out["candidates"] = out["candidates"][: max(1, ns.top)]

    text = json.dumps(out, indent=2, ensure_ascii=False)
    if ns.json_out:
        ns.json_out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
