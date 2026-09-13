#!/usr/bin/env python3
"""C-046: public-safe family-wide counted-BE f32 compatibility filter.

This module consumes only aggregate family sizes and aggregate per-role exact-fit
ceilings. It never reads proprietary payload bytes and never promotes semantics.

Important: this is an interpretation filter for CROSS_SURFACE_FAMILY_WIDE scope.
It MUST NOT shrink the fixed C-018 preregistered scan surface because C-021 keeps
cross-family same-role recurrence admissible.
"""

from __future__ import annotations

import json
from typing import Dict, Mapping


FAMILIES: Dict[str, int] = {
    "F48_0000110": 7,
    "F48_0000111": 3,
    "F48_0001110": 3,
    "F49_0000111": 3,
    "F49_1000111": 6,
}

ROLE_CEILINGS: Dict[str, Dict[str, int]] = {
    "WHOLE_RECORD_Q0": {"A": 7, "B": 7},
    "STABLE_PREFIX_Q0": {"A": 7, "B": 7},
    "CONTROL_ZONE_Q21": {"A": 6, "B": 5},
    "PRESERVED_ISLAND_Q25": {"A": 6, "B": 6},
}


def _validate_int_map(
    values: Mapping[str, int], label: str, *, allow_zero: bool = False
) -> None:
    if not isinstance(values, Mapping) or not values:
        raise ValueError(f"{label} must be a non-empty mapping")
    minimum = 0 if allow_zero else 1
    for key, value in values.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"{label} keys must be non-empty strings")
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{label} values must be integers >= {minimum}")


def evaluate_family_wide_role(
    role: str,
    ceilings: Mapping[str, int],
    families: Mapping[str, int] = FAMILIES,
) -> dict:
    """Classify family-wide compatibility without claiming a codec binding.

    A family-wide cross-surface binding would require every member of that family
    to exact-fit the candidate codec on both surfaces. Therefore family_size must
    be <= min(surface_A_ceiling, surface_B_ceiling).

    This necessary-condition test is intentionally one-way:
    compatible != bound, and eliminated applies only to the family-wide scope.
    """

    if not isinstance(role, str) or not role:
        raise ValueError("role must be a non-empty string")
    if not isinstance(ceilings, Mapping) or set(ceilings) != {"A", "B"}:
        raise ValueError("ceilings must contain exactly A and B")

    _validate_int_map(ceilings, "ceilings", allow_zero=True)
    _validate_int_map(families, "families")

    effective_ceiling = min(ceilings["A"], ceilings["B"])
    compatible = sorted(
        family_id for family_id, size in families.items() if size <= effective_ceiling
    )
    eliminated = sorted(
        family_id for family_id, size in families.items() if size > effective_ceiling
    )

    return {
        "role": role,
        "codec_candidate": "COUNTED_BE_F32_FIXED_ROLE_START",
        "scope": "CROSS_SURFACE_FAMILY_WIDE",
        "surface_ceilings": dict(ceilings),
        "effective_cross_surface_ceiling": effective_ceiling,
        "compatible_family_ids": compatible,
        "eliminated_family_ids": eliminated,
        "compatible_record_count_if_family_wide": sum(
            families[family_id] for family_id in compatible
        ),
        "binding_confirmed": False,
        "semantic_promotion": False,
        "primary_preregistered_scan_surface_reduced": False,
        "reason_primary_scan_unchanged": (
            "C-018 scan surface is preregistered and C-021 permits cross-family "
            "same-role recurrence; this ceiling only constrains family-wide scope "
            "interpretation."
        ),
    }


def evaluate_default_matrix() -> dict:
    return {
        role: evaluate_family_wide_role(role, ceilings)
        for role, ceilings in ROLE_CEILINGS.items()
    }


def build_result() -> dict:
    return {
        "schema_version": "csmc_analysis_c_family_codec_compatibility_v1",
        "research_run": "C-046",
        "source_type": "PUBLIC_SAFE_CROSS_LANE_AGGREGATE",
        "families": FAMILIES,
        "roles": evaluate_default_matrix(),
        "global_invariants": {
            "pipeline_stage": "STRUCTURAL_ONLY",
            "semantic_promotion_count": 0,
            "blender_emit_ready": False,
            "raw_or_private_payload_bytes_used": False,
            "runtime_dispatch_requested": False,
            "mainline_mutation_requested": False,
            "c018_preregistered_scan_surface_changed": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_result(), indent=2, sort_keys=True))
