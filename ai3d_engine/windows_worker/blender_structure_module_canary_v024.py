# SPDX-License-Identifier: MIT
"""CANARY-005 visual/geometry false-positive repair for NEVER TEAR AI3D-013.

This wrapper keeps the fixed six-command synthetic Structure CANARY contract.
It repairs two narrowly-scoped problems observed on the physical Blender 2.83
CANARY-004 path:

1. a temporary Boolean cutter whose lower face is exactly coplanar with the
   wall lower face is extended downward by a fixed 0.01 m execution-only
   overlap epsilon before the trusted Boolean operation; and
2. automated QA now verifies resulting geometry, not merely that one BOOLEAN
   command was invoked. A ray through the expected opening must miss the wall,
   while a control ray through known-solid wall area must still hit it.

No cloud/user supplied path, script, URL, executable, plan mutation, or
production command surface is added. Semantic promotion remains false until a
new physical PNG passes visual QA.
"""
from __future__ import annotations

import builtins
import importlib.util
import json
from pathlib import Path
from typing import Any

import bpy
from mathutils import Vector

RUN_ID = "AI3D-013-PHYSICAL-STRUCTURE-CANARY-005"
EVIDENCE_CLASS = "PHYSICAL_WINDOWS_BLENDER_STRUCTURE_CAPABILITY_CANARY_V5"
BASE_NAME = "blender_structure_module_canary.py"
BOOLEAN_OVERLAP_EPSILON_M = 0.01
COPLANAR_TOLERANCE_M = 1.0e-5

_BOOLEAN_DIAGNOSTICS: dict[str, Any] = {
    "execution_overlap_epsilon_m": 0.0,
    "coplanar_lower_boundary_detected": False,
    "solver": "NONE",
}


def _load_bundled_base():
    base_path = Path(__file__).resolve().with_name(BASE_NAME)
    if not base_path.is_file():
        raise RuntimeError("bundled Structure CANARY base executor missing")
    spec = importlib.util.spec_from_file_location("_never_tear_ai3d_structure_canary_base_v024", str(base_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot create bundled Structure CANARY module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _qa_gate_all(values):
    vals = list(values)
    # Historical base exposes eight positive predicates followed by the safety
    # invariant canary_promoted=False. Preserve the invariant while excluding
    # it from the positive predicate conjunction.
    if len(vals) == 9 and vals[-1] is False:
        return builtins.all(vals[:-1])
    return builtins.all(vals)


def _apply_execution_overlap_if_needed(target: bpy.types.Object, tool: bpy.types.Object) -> None:
    target_bottom = float(target.location.z - target.dimensions.z / 2.0)
    tool_bottom = float(tool.location.z - tool.dimensions.z / 2.0)
    _BOOLEAN_DIAGNOSTICS["target_bottom_before_m"] = target_bottom
    _BOOLEAN_DIAGNOSTICS["tool_bottom_before_m"] = tool_bottom
    if abs(tool_bottom - target_bottom) > COPLANAR_TOLERANCE_M:
        return

    _BOOLEAN_DIAGNOSTICS["coplanar_lower_boundary_detected"] = True
    _BOOLEAN_DIAGNOSTICS["execution_overlap_epsilon_m"] = BOOLEAN_OVERLAP_EPSILON_M
    # Extend only the temporary cutter downward. Its top edge remains fixed,
    # so the intended opening height is unchanged while the coplanar lower
    # boundary becomes a proper overlap for legacy/default Boolean solvers.
    top_before = float(tool.location.z + tool.dimensions.z / 2.0)
    tool.dimensions.z = float(tool.dimensions.z) + BOOLEAN_OVERLAP_EPSILON_M
    tool.location.z = float(tool.location.z) - BOOLEAN_OVERLAP_EPSILON_M / 2.0
    bpy.context.view_layer.objects.active = tool
    tool.select_set(True)
    target.select_set(False)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _BOOLEAN_DIAGNOSTICS["tool_bottom_after_m"] = float(tool.location.z - tool.dimensions.z / 2.0)
    _BOOLEAN_DIAGNOSTICS["tool_top_preserved_m"] = float(tool.location.z + tool.dimensions.z / 2.0)
    _BOOLEAN_DIAGNOSTICS["tool_top_before_m"] = top_before


def _ray_hit_world(obj: bpy.types.Object, world_origin: tuple[float, float, float], world_direction: tuple[float, float, float], distance: float) -> dict[str, Any]:
    inverse = obj.matrix_world.inverted()
    origin_local = inverse @ Vector(world_origin)
    direction_local = (inverse.to_3x3() @ Vector(world_direction)).normalized()
    hit, location, normal, face_index = obj.ray_cast(origin_local, direction_local, distance=distance)
    return {
        "hit": bool(hit),
        "face_index": int(face_index) if hit else -1,
        "location_local": [float(v) for v in location] if hit else None,
        "normal_local": [float(v) for v in normal] if hit else None,
    }


def _rewrite_result_with_geometry_qa(base, output: Path) -> dict[str, Any]:
    result_path = output / "result.json"
    if not result_path.is_file():
        raise RuntimeError("base Structure CANARY result.json missing")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    wall = bpy.data.objects.get("wall_001")
    if wall is None or wall.type != "MESH":
        raise RuntimeError("wall_001 missing for post-Boolean geometry probe")

    # Fixed synthetic CANARY coordinates after PLAN_XY... -> Blender mapping.
    # Opening center: x=0, z=1.1. Known-solid control: x=1.5, z=1.1.
    opening_probe = _ray_hit_world(wall, (0.0, -1.0, 1.1), (0.0, 1.0, 0.0), 2.0)
    solid_probe = _ray_hit_world(wall, (1.5, -1.0, 1.1), (0.0, 1.0, 0.0), 2.0)
    opening_void = not opening_probe["hit"]
    solid_control = bool(solid_probe["hit"])
    command_count_exact = int(result.get("opening_boolean_count") or 0) == 1
    geometry_boolean_exact = command_count_exact and opening_void and solid_control

    checks = dict(result.get("checks") or {})
    checks["opening_boolean_command_count_exact"] = command_count_exact
    checks["opening_void_probe"] = opening_void
    checks["solid_control_probe"] = solid_control
    checks["opening_boolean_exact"] = geometry_boolean_exact
    checks["canary_promoted"] = False

    positive_checks = [bool(value) for key, value in checks.items() if key != "canary_promoted"]
    status = "PASS" if builtins.all(positive_checks) else "FAIL"
    result["run_id"] = RUN_ID
    result["evidence_class"] = EVIDENCE_CLASS
    result["status"] = status
    result["automated_qa"] = status
    result["visual_qa"] = "PENDING"
    result["canary_promoted"] = False
    result["promotion_allowed"] = False
    result["checks"] = checks
    result["geometry_probe_version"] = "CANARY005_OPENING_RAY_V1"
    result["opening_probe"] = opening_probe
    result["solid_control_probe"] = solid_probe
    result["boolean_diagnostics"] = dict(_BOOLEAN_DIAGNOSTICS)
    result["next_action"] = (
        "Require Supabase storage SHA readback and human/visual QA before promotion; "
        "geometry probes must remain PASS."
    )

    checkpoint_state = {
        "task_id": result.get("task_id"),
        "run_id": RUN_ID,
        "module_id": result.get("module_id"),
        "action": result.get("action"),
        "checks": checks,
        "png_sha256": result.get("png_sha256"),
        "blender_version": result.get("blender_version"),
        "engine": result.get("render_engine"),
        "boolean_solver": result.get("boolean_solver"),
        "boolean_diagnostics": result.get("boolean_diagnostics"),
        "geometry_probe_version": result.get("geometry_probe_version"),
        "canary_promoted": False,
    }
    checkpoint_sha = base.sha256_bytes(
        json.dumps(checkpoint_state, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    result["checkpoint_id"] = f"cp-ai3d-013-{checkpoint_sha[:16]}"
    result["checkpoint_sha256"] = checkpoint_sha
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return result


def main() -> None:
    base = _load_bundled_base()
    base.RUN_ID = RUN_ID
    base.EVIDENCE_CLASS = EVIDENCE_CLASS
    base.all = _qa_gate_all

    original_subtract_boolean = base.subtract_boolean

    def _bounded_subtract_boolean(target: bpy.types.Object, tool: bpy.types.Object) -> str:
        _BOOLEAN_DIAGNOSTICS["target_vertices_before"] = len(target.data.vertices)
        _BOOLEAN_DIAGNOSTICS["target_polygons_before"] = len(target.data.polygons)
        _apply_execution_overlap_if_needed(target, tool)
        solver = original_subtract_boolean(target, tool)
        _BOOLEAN_DIAGNOSTICS["solver"] = solver
        _BOOLEAN_DIAGNOSTICS["target_vertices_after"] = len(target.data.vertices)
        _BOOLEAN_DIAGNOSTICS["target_polygons_after"] = len(target.data.polygons)
        return solver

    base.subtract_boolean = _bounded_subtract_boolean
    args = base.parse_args()
    output = Path(args.output).resolve()
    base.main()
    result = _rewrite_result_with_geometry_qa(base, output)
    if result.get("status") != "PASS":
        raise SystemExit(23)


if __name__ == "__main__":
    main()
