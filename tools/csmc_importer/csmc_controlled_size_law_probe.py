#!/usr/bin/env python3
"""Public-safe bounded fixed-stride relationship screen for controlled CSMC aggregates.

Consumes only public-safe fixture/phase aggregates. It deliberately tests a
small preregistered hypothesis family and reports exact fits only. It does not
mine arbitrary formulas and cannot promote semantics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SINGLE_STRIDES = (4, 8, 12, 16)
VERTEX_STRIDES = (12, 16)
INDEX_WIDTHS = (2, 4)
TRIANGLE_STRIDES = (4, 8, 12, 16)

GEOM_IDS = (
    "CSMC_F01_TRIANGLE",
    "CSMC_F02_QUAD",
    "CSMC_F03_CUBE",
    "CSMC_F04_CUBE_SUBDIV",
)
RIG_IDS = (
    "CSMC_R01_CUBE_B1_W0",
    "CSMC_R02_CUBE_B1_W100",
    "CSMC_R03_CUBE_B2_W100",
    "CSMC_R04_CUBE_B2_SPLIT",
    "CSMC_R05_CUBE_B2_MIX50",
)


def _fixture_map(manifest: dict) -> dict[str, dict]:
    return {row["fixture_id"]: row for row in manifest["fixtures"]}


def _teacher(row: dict, field: str) -> int:
    gt = row["ground_truth"]
    if field == "corners":
        return int(gt["triangles"]) * 3
    return int(gt[field])


def _stored(row: dict) -> int:
    return int(row["frame"]["stored_length"])


def _single_count_exact_models(rows: list[dict], fields: tuple[str, ...]) -> list[dict]:
    out = []
    base = rows[0]
    for field in fields:
        for stride in SINGLE_STRIDES:
            overhead = _stored(base) - _teacher(base, field) * stride
            errors = [
                _stored(r) - (overhead + _teacher(r, field) * stride)
                for r in rows
            ]
            if all(e == 0 for e in errors):
                out.append({"field": field, "stride_bytes": stride, "overhead_bytes": overhead})
    return out


def _two_factor_rig_exact_models(rows: list[dict]) -> list[dict]:
    out = []
    base = rows[0]
    for bone_stride in SINGLE_STRIDES:
        for weight_stride in SINGLE_STRIDES:
            overhead = (
                _stored(base)
                - _teacher(base, "bones") * bone_stride
                - _teacher(base, "weight_assignments") * weight_stride
            )
            errors = [
                _stored(r)
                - (
                    overhead
                    + _teacher(r, "bones") * bone_stride
                    + _teacher(r, "weight_assignments") * weight_stride
                )
                for r in rows
            ]
            if all(e == 0 for e in errors):
                out.append({
                    "bone_stride_bytes": bone_stride,
                    "weight_assignment_stride_bytes": weight_stride,
                    "overhead_bytes": overhead,
                })
    return out


def _phase_pair(phase: dict, a: str, b: str) -> dict:
    for row in phase["pairs"]:
        if row["fixture_a"] == a and row["fixture_b"] == b:
            return row
        if row["fixture_a"] == b and row["fixture_b"] == a:
            return {
                **row,
                "fixture_a": a,
                "fixture_b": b,
                "longest_run_start_a": row["longest_run_start_b"],
                "longest_run_start_b": row["longest_run_start_a"],
                "qword_count_a": row["qword_count_b"],
                "qword_count_b": row["qword_count_a"],
            }
    raise ValueError(f"phase pair not found: {a} / {b}")


def _same_phase_geometry_delta_models(fm: dict[str, dict], phase: dict) -> dict:
    a, b = "CSMC_F02_QUAD", "CSMC_F04_CUBE_SUBDIV"
    p = _phase_pair(phase, a, b)
    if not p["same_logical_mod8"]:
        raise ValueError("F02/F04 must remain same-phase")
    prefix_delta_bytes = (
        int(p["longest_run_start_b"]) - int(p["longest_run_start_a"])
    ) * 8
    ra, rb = fm[a], fm[b]
    deltas = {
        "vertices": _teacher(rb, "vertices") - _teacher(ra, "vertices"),
        "triangles": _teacher(rb, "triangles") - _teacher(ra, "triangles"),
        "corners": _teacher(rb, "corners") - _teacher(ra, "corners"),
    }

    pure = []
    for field, dn in deltas.items():
        for stride in SINGLE_STRIDES:
            if dn * stride == prefix_delta_bytes:
                pure.append({"field": field, "stride_bytes": stride})

    vertex_corner = []
    for v_stride in VERTEX_STRIDES:
        for index_width in INDEX_WIDTHS:
            if deltas["vertices"] * v_stride + deltas["corners"] * index_width == prefix_delta_bytes:
                vertex_corner.append({
                    "vertex_stride_bytes": v_stride,
                    "corner_index_width_bytes": index_width,
                })

    vertex_triangle = []
    for v_stride in VERTEX_STRIDES:
        for t_stride in TRIANGLE_STRIDES:
            if deltas["vertices"] * v_stride + deltas["triangles"] * t_stride == prefix_delta_bytes:
                vertex_triangle.append({
                    "vertex_stride_bytes": v_stride,
                    "triangle_stride_bytes": t_stride,
                })

    return {
        "pair": "F02_F04",
        "prefix_delta_bytes": prefix_delta_bytes,
        "teacher_deltas": deltas,
        "pure_single_count_exact_models": pure,
        "vertex_plus_corner_index_exact_models": vertex_corner,
        "vertex_plus_triangle_exact_models": vertex_triangle,
    }


def analyze(manifest: dict, phase: dict) -> dict:
    fm = _fixture_map(manifest)
    geom_rows = [fm[x] for x in GEOM_IDS]
    rig_rows = [fm[x] for x in RIG_IDS]

    geom_single = _single_count_exact_models(
        geom_rows, ("vertices", "triangles", "corners")
    )
    rig_single = _single_count_exact_models(
        rig_rows, ("bones", "weight_assignments")
    )
    rig_two = _two_factor_rig_exact_models(rig_rows)
    phase_geom = _same_phase_geometry_delta_models(fm, phase)

    no_simple_geom = (
        not geom_single
        and not phase_geom["pure_single_count_exact_models"]
        and not phase_geom["vertex_plus_corner_index_exact_models"]
        and not phase_geom["vertex_plus_triangle_exact_models"]
    )
    no_simple_rig = not rig_single and not rig_two

    return {
        "schema_version": "csmc_controlled_size_law_probe_v1",
        "candidate_family": {
            "single_strides_bytes": list(SINGLE_STRIDES),
            "vertex_strides_bytes": list(VERTEX_STRIDES),
            "index_widths_bytes": list(INDEX_WIDTHS),
            "triangle_strides_bytes": list(TRIANGLE_STRIDES),
        },
        "geometry_fixture_count": len(geom_rows),
        "rig_fixture_count": len(rig_rows),
        "geometry_whole_stored_single_count_exact_models": geom_single,
        "same_phase_geometry": phase_geom,
        "rig_whole_stored_single_count_exact_models": rig_single,
        "rig_whole_stored_bone_plus_weight_exact_models": rig_two,
        "simple_geometry_size_law_rejected": no_simple_geom,
        "simple_rig_size_law_rejected": no_simple_rig,
        "interpretation": "WHOLE_STORED_AND_PHASE_PREFIX_SIZE_NOT_SINGLE_SIMPLE_FIXED_STRIDE_ARRAY",
        "semantic_promotion": False,
        "blender_emit_ready": False,
        "raw_values_embedded": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("phase_aggregate", type=Path)
    ap.add_argument("--json-out", type=Path)
    ns = ap.parse_args()
    out = analyze(
        json.loads(ns.manifest.read_text(encoding="utf-8")),
        json.loads(ns.phase_aggregate.read_text(encoding="utf-8")),
    )
    text = json.dumps(out, indent=2, sort_keys=True)
    if ns.json_out:
        ns.json_out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
