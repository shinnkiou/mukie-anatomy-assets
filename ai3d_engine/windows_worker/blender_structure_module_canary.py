# SPDX-License-Identifier: MIT
"""Bounded physical Structure capability CANARY for NEVER TEAR AI3D-013.

This executor accepts only the fixed six-command synthetic CANARY contract. It
never accepts arbitrary scripts, commands, URLs, paths, materials, imports, or
production module plans. Passing this CANARY proves the Structure handler path;
it does not promote or execute the Central Corridor production plan.
"""
from __future__ import annotations

import argparse
from array import array
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import bpy
from mathutils import Vector

SCHEMA = "never-tear-ai3d-structure-capability-canary-result-v1"
PLAN_SCHEMA = "never-tear-ai3d-structure-capability-canary-plan-v1"
ACTION = "ai3d_structure_module_v1"
TASK_ID = "AI3D-013"
RUN_ID = "AI3D-013-PHYSICAL-STRUCTURE-CANARY-001"
MODULE_ID = "ai3d_structure_capability_canary_v1"
EVIDENCE_CLASS = "PHYSICAL_WINDOWS_BLENDER_STRUCTURE_CAPABILITY_CANARY"
COORDINATE_CONTRACT = "PLAN_XY_EAST_NORTH_TO_THREE_XZ_YUP_V1"
ALLOWED_OPS = frozenset({"CREATE_PRIMITIVE", "TRANSFORM_SET", "BOOLEAN", "QA_RUN"})
EXPECTED_COUNTS = {"CREATE_PRIMITIVE": 2, "TRANSFORM_SET": 2, "BOOLEAN": 1, "QA_RUN": 1}
SAFE_QA = frozenset({"wall_count_exact", "opening_boolean_exact", "cutter_removed", "mesh_nonempty", "floor_contact", "render_evidence"})


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True)
    p.add_argument("--output", required=True)
    return p.parse_args(raw)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def number(value: object, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError("numeric value required")
    n = float(value)
    if not math.isfinite(n) or n < low or n > high:
        raise ContractError("numeric value out of range")
    return n


def vec3(value: object, low: float, high: float) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ContractError("vec3 required")
    return tuple(number(v, low, high) for v in value)  # type: ignore[return-value]


def point_to_blender(v: tuple[float, float, float]) -> tuple[float, float, float]:
    return (v[0], -v[2], v[1])


def size_to_blender(v: tuple[float, float, float]) -> tuple[float, float, float]:
    return (v[0], v[2], v[1])


def rotation_to_blender(v: tuple[float, float, float]) -> tuple[float, float, float]:
    if abs(v[0]) > 1e-9 or abs(v[2]) > 1e-9:
        raise ContractError("only Three Y-axis rotation is allowed")
    return (0.0, 0.0, v[1])


def load_plan(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ContractError("plan must be object")
    allowed = {"schema", "project_key", "task_id", "run_id", "module_id", "coordinate_contract", "commands", "policy"}
    if set(raw) != allowed:
        raise ContractError("top-level contract mismatch")
    if raw.get("schema") != PLAN_SCHEMA or raw.get("project_key") != "never_tear_ai3d_engine":
        raise ContractError("plan identity rejected")
    if raw.get("task_id") != TASK_ID or raw.get("run_id") != RUN_ID or raw.get("module_id") != MODULE_ID:
        raise ContractError("task/run/module rejected")
    if raw.get("coordinate_contract") != COORDINATE_CONTRACT:
        raise ContractError("coordinate contract rejected")
    policy = raw.get("policy")
    if not isinstance(policy, dict):
        raise ContractError("policy missing")
    expected_policy = {
        "synthetic_canary": True,
        "geometry_authority_mutated": False,
        "production_plan_mutated": False,
        "allow_arbitrary_script": False,
        "allow_network": False,
        "max_commands": 6,
        "max_attempts": 1,
        "physical_concurrency": 1,
        "semantic_promotion": False,
    }
    if policy != expected_policy:
        raise ContractError("policy rejected")
    commands = raw.get("commands")
    if not isinstance(commands, list) or len(commands) != 6:
        raise ContractError("command count rejected")
    counts = {op: 0 for op in ALLOWED_OPS}
    names = set()
    for command in commands:
        if not isinstance(command, dict) or set(command) != {"command_id", "op", "params", "lineage", "routes"}:
            raise ContractError("command contract rejected")
        op = str(command.get("op") or "")
        if op not in ALLOWED_OPS:
            raise ContractError("op rejected")
        counts[op] += 1
        if command.get("routes") != ["WINDOWS_WORKER"]:
            raise ContractError("route rejected")
        lineage = command.get("lineage")
        if not isinstance(lineage, dict) or lineage.get("module_id") != MODULE_ID or lineage.get("source") != "AI3D-013_SYNTHETIC_CANARY":
            raise ContractError("lineage rejected")
        params = command.get("params")
        if not isinstance(params, dict):
            raise ContractError("params missing")
        if op == "CREATE_PRIMITIVE":
            if set(params) != {"name", "kind", "position", "size"} or params.get("kind") != "box":
                raise ContractError("primitive params rejected")
            name = str(params.get("name") or "")
            if name not in {"wall_001", "opening_cutter_001"} or name in names:
                raise ContractError("primitive name rejected")
            names.add(name)
            vec3(params.get("position"), -10, 10); vec3(params.get("size"), 0.01, 10)
        elif op == "TRANSFORM_SET":
            if set(params) != {"name", "rotation"} or str(params.get("name") or "") not in {"wall_001", "opening_cutter_001"}:
                raise ContractError("transform params rejected")
            rotation_to_blender(vec3(params.get("rotation"), -2 * math.pi, 2 * math.pi))
        elif op == "BOOLEAN":
            if params != {"target": "wall_001", "tool": "opening_cutter_001", "mode": "subtract", "keep_tool": False}:
                raise ContractError("boolean params rejected")
        elif op == "QA_RUN":
            if set(params) != {"checks"} or not isinstance(params.get("checks"), list) or set(map(str, params["checks"])) != SAFE_QA:
                raise ContractError("QA params rejected")
    if counts != EXPECTED_COUNTS:
        raise ContractError("operation counts rejected")
    return raw


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def add_box(name: str, position: tuple[float, float, float], size: tuple[float, float, float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=point_to_blender(position))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size_to_blender(size)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def subtract_boolean(target: bpy.types.Object, tool: bpy.types.Object) -> str:
    bpy.context.view_layer.objects.active = target
    target.select_set(True); tool.select_set(False)
    modifier = target.modifiers.new(name="NT_CANARY_BOOL", type="BOOLEAN")
    modifier.operation = "DIFFERENCE"
    solver = "DEFAULT"
    try:
        modifier.solver = "EXACT"
        solver = "EXACT"
    except Exception:
        pass
    modifier.object = tool
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(tool, do_unlink=True)
    return solver


def material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.72
    return mat


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def pick_engine() -> str:
    items = {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    return "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in items else "BLENDER_EEVEE"


def decoded_pixel_sha(path: Path, width: int, height: int) -> str:
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        if tuple(image.size) != (width, height):
            raise RuntimeError("decoded PNG size mismatch")
        pixels = array("f", image.pixels[:])
        return sha256_bytes(pixels.tobytes())
    finally:
        bpy.data.images.remove(image)


def main() -> None:
    args = parse_args()
    plan = load_plan(Path(args.plan).resolve())
    output = Path(args.output).resolve(); output.mkdir(parents=True, exist_ok=True)
    reset_scene()
    objects: dict[str, bpy.types.Object] = {}
    boolean_count = 0; solver = "NONE"
    for command in plan["commands"]:
        op = command["op"]; params = command["params"]
        if op == "CREATE_PRIMITIVE":
            objects[params["name"]] = add_box(params["name"], vec3(params["position"], -10, 10), vec3(params["size"], 0.01, 10))
        elif op == "TRANSFORM_SET":
            objects[params["name"]].rotation_euler = rotation_to_blender(vec3(params["rotation"], -2 * math.pi, 2 * math.pi))
        elif op == "BOOLEAN":
            solver = subtract_boolean(objects[params["target"]], objects[params["tool"]])
            objects.pop(params["tool"], None); boolean_count += 1

    wall = objects.get("wall_001")
    if wall is None:
        raise RuntimeError("wall missing after execution")
    wall.data.materials.append(material("NT_CANARY_WALL", (0.18, 0.23, 0.30, 1.0)))
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 0.0))
    floor = bpy.context.object; floor.name = "NT_CANARY_FLOOR"; floor.dimensions = (7.0, 5.0, 0.0)
    bpy.context.view_layer.objects.active = floor; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    floor.data.materials.append(material("NT_CANARY_FLOOR_MAT", (0.055, 0.065, 0.075, 1.0)))

    camera_data = bpy.data.cameras.new("NT_CANARY_CAMERA"); camera = bpy.data.objects.new("NT_CANARY_CAMERA", camera_data)
    bpy.context.scene.collection.objects.link(camera); camera.location = (5.6, -7.4, 4.2); camera.data.lens = 48.0
    look_at(camera, (0.0, 0.0, 1.5)); bpy.context.scene.camera = camera
    light_data = bpy.data.lights.new("NT_CANARY_KEY", type="AREA"); light_data.energy = 1000.0; light_data.size = 5.0
    light = bpy.data.objects.new("NT_CANARY_KEY", light_data); bpy.context.scene.collection.objects.link(light); light.location = (2.5, -3.5, 6.0); look_at(light, (0, 0, 1.5))
    world = bpy.context.scene.world or bpy.data.worlds.new("NT_CANARY_WORLD"); bpy.context.scene.world = world; world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg: bg.inputs["Strength"].default_value = 0.35

    scene = bpy.context.scene; engine = pick_engine(); scene.render.engine = engine
    width, height = 960, 540; scene.render.resolution_x = width; scene.render.resolution_y = height; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGBA"; scene.render.film_transparent = False
    png = output / "ai3d_structure_capability_canary.png"; blend = output / "ai3d_structure_capability_canary.blend"
    scene.render.filepath = str(png); bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False); bpy.ops.render.render(write_still=True)
    if not png.is_file() or png.stat().st_size <= 0 or not blend.is_file() or blend.stat().st_size <= 0:
        raise RuntimeError("durable local evidence missing")

    png_sha = sha256_file(png); pixel_sha = decoded_pixel_sha(png, width, height)
    floor_contact = abs(float(wall.location.z - wall.dimensions.z / 2.0)) <= 1e-4
    mesh_nonempty = len(wall.data.vertices) > 0 and len(wall.data.polygons) > 0
    checks = {
        "wall_count_exact": len([n for n in objects if n.startswith("wall_")]) == 1,
        "opening_boolean_exact": boolean_count == 1,
        "cutter_removed": bpy.data.objects.get("opening_cutter_001") is None,
        "mesh_nonempty": mesh_nonempty,
        "floor_contact": floor_contact,
        "render_evidence": png.stat().st_size > 0 and len(pixel_sha) == 64 and pixel_sha != png_sha,
        "background_mode": bool(bpy.app.background),
        "production_plan_not_executed": True,
        "canary_promoted": False,
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    checkpoint_state = {"task_id": TASK_ID, "run_id": RUN_ID, "module_id": MODULE_ID, "action": ACTION, "checks": checks, "png_sha256": png_sha, "blender_version": bpy.app.version_string, "engine": engine, "boolean_solver": solver, "canary_promoted": False}
    checkpoint_sha = sha256_bytes(json.dumps(checkpoint_state, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    result = {
        "schema_version": SCHEMA, "project_key": "never_tear_ai3d_engine", "task_id": TASK_ID, "run_id": RUN_ID, "action": ACTION,
        "status": status, "evidence_class": EVIDENCE_CLASS, "generated_at": datetime.now(timezone.utc).isoformat(),
        "module_id": MODULE_ID, "command_count": 6, "wall_count": 1, "opening_boolean_count": boolean_count,
        "raw_pixel_sha256": pixel_sha, "png_sha256": png_sha, "blend_sha256": sha256_file(blend),
        "checkpoint_id": f"cp-ai3d-013-{checkpoint_sha[:16]}", "checkpoint_sha256": checkpoint_sha,
        "renderer": f"Blender {bpy.app.version_string} / {engine}", "blender_version": bpy.app.version_string, "render_engine": engine,
        "boolean_solver": solver, "width": width, "height": height, "automated_qa": status, "visual_qa": "PENDING",
        "canary_promoted": False, "promotion_allowed": False, "checks": checks,
        "next_action": "Require Supabase storage SHA readback and human/visual QA before promotion."
    }
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if status != "PASS": raise SystemExit(23)


if __name__ == "__main__":
    main()
