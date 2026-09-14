#!/usr/bin/env python3
"""Reference-only Companion C reconciliation for the public-safe bounded size-law probe."""
from __future__ import annotations

EXPECTED_SINGLE = [4, 8, 12, 16]
EXPECTED_VERTEX = [12, 16]
EXPECTED_INDEX = [2, 4]
EXPECTED_TRIANGLE = [4, 8, 12, 16]
EXPECTED_INTERPRETATION = "WHOLE_STORED_AND_PHASE_PREFIX_SIZE_NOT_SINGLE_SIMPLE_FIXED_STRIDE_ARRAY"

def reconcile(source: dict, c062: dict) -> dict:
    fam = source.get("candidate_family", {})
    if fam.get("single_strides_bytes") != EXPECTED_SINGLE:
        raise ValueError("candidate family drift: single strides")
    if fam.get("vertex_strides_bytes") != EXPECTED_VERTEX:
        raise ValueError("candidate family drift: vertex strides")
    if fam.get("index_widths_bytes") != EXPECTED_INDEX:
        raise ValueError("candidate family drift: index widths")
    if fam.get("triangle_strides_bytes") != EXPECTED_TRIANGLE:
        raise ValueError("candidate family drift: triangle strides")
    if source.get("interpretation") != EXPECTED_INTERPRETATION:
        raise ValueError("unexpected source interpretation")
    if source.get("geometry_whole_stored_single_count_exact_models") != []:
        raise ValueError("geometry simple model unexpectedly present")
    same = source.get("same_phase_geometry", {})
    if same.get("pair") != "F02_F04":
        raise ValueError("unexpected same-phase pair")
    if same.get("prefix_delta_bytes") != 864:
        raise ValueError("prefix delta drift")
    if same.get("teacher_deltas") != {"vertices": 22, "triangles": 46, "corners": 138}:
        raise ValueError("teacher deltas drift")
    for key in (
        "pure_single_count_exact_models",
        "vertex_plus_corner_index_exact_models",
        "vertex_plus_triangle_exact_models",
    ):
        if same.get(key) != []:
            raise ValueError(f"same-phase exact model unexpectedly present: {key}")
    if source.get("rig_whole_stored_single_count_exact_models") != []:
        raise ValueError("rig single-count model unexpectedly present")
    if source.get("rig_whole_stored_bone_plus_weight_exact_models") != []:
        raise ValueError("rig two-factor model unexpectedly present")
    if source.get("simple_geometry_size_law_rejected") is not True:
        raise ValueError("geometry rejection flag missing")
    if source.get("simple_rig_size_law_rejected") is not True:
        raise ValueError("rig rejection flag missing")
    if source.get("semantic_promotion") is not False:
        raise ValueError("semantic promotion must remain false")
    if source.get("blender_emit_ready") is not False:
        raise ValueError("Blender emit must remain false")
    if source.get("raw_values_embedded") is not False:
        raise ValueError("raw values must not be embedded")

    ba = c062.get("binary_analysis", c062)
    if ba.get("classification") != "PHASE_CORE_EXCLUSION_MASK_EXTENDED_PHASE3_READY":
        raise ValueError("C-062 mask classification drift")
    if ba.get("remaining_search_qwords") != 537774:
        raise ValueError("C-062 remaining search surface drift")
    if ba.get("semantic_promotion_count") != 0:
        raise ValueError("C-062 semantic promotion drift")

    return {
        "schema_version": "csmc_analysis_c_size_law_reconciliation_c063_v1",
        "classification": "BOUNDED_SIMPLE_FIXED_STRIDE_SIZE_LAW_REJECTED",
        "source_interpretation": EXPECTED_INTERPRETATION,
        "candidate_family_locked": True,
        "geometry_whole_stored_simple_models": 0,
        "f02_f04_prefix_delta_bytes": 864,
        "f02_f04_teacher_deltas": {"vertices": 22, "triangles": 46, "corners": 138},
        "f02_f04_preregistered_exact_models": 0,
        "rig_whole_stored_simple_models": 0,
        "masked_remaining_search_qwords": 537774,
        "mask_changed": False,
        "next_search": "INTERNAL_SUBBLOCK_BOUNDARY_RELATIONSHIPS_ONLY",
        "semantic_binding": "UNRESOLVED",
        "pipeline_stage": "STRUCTURAL_ONLY",
        "semantic_promotion_count": 0,
        "blender_emit_ready": False,
        "runtime_dispatch": False,
        "raw_private_bytes_published": False,
    }
