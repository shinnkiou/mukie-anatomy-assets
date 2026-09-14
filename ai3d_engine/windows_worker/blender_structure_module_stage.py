# SPDX-License-Identifier: MIT
"""NEVER TEAR AI3D Structure Module staged Blender executor.

This is a pre-promotion implementation for the future Windows Worker production
route. It accepts ONLY the already-QA'd Central Corridor module plan and only
CREATE_PRIMITIVE / TRANSFORM_SET / BOOLEAN / QA_RUN. It does not execute cloud
code, shell, filesystem paths, URLs, imports, exports, materials, or arbitrary
Production Protocol operations.

Evidence from this script is VIRTUAL/STAGED until the separate AI3D companion
passes its physical CANARY and the AI3D-004 physical QA gate promotes the
production route.
"""
from __future__ import annotations

import argparse
from array import array
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

import bpy
from mathutils import Vector

RESULT_SCHEMA = "never-tear-ai3d-structure-module-stage-result-v1"
ACTION = "ai3d_structure_module_v1"
EVIDENCE_CLASS = "VIRTUAL_GITHUB_ACTIONS_BLENDER_NOT_PHYSICAL"
COORDINATE_CONTRACT = "PLAN_XY_EAST_NORTH_TO_THREE_XZ_YUP_V1"
MAPPING_CONTRACT = "THREE_Y_UP_TO_BLENDER_Z_UP_V1"
EXPECTED_PLAN_ID = "module-plan-7d0ef550473d76e6"
EXPECTED_PLAN_SHA256 = "7d0ef550473d76e6cbacf5e285f81cb0152787e29034d524bd8b946f2ad9707a"
EXPECTED_GEOMETRY_SHA256 = "0efa7547c1e065304d93eb5fb0cc858e668c41c3bc6516d0b7ab84302f6f52fb"
EXPECTED_SOURCE_PLAN_ID = "structure-plan-83389de2d8016fb6"
EXPECTED_SOURCE_PLAN_SHA256 = "83389de2d8016fb6dc1ec043befd071d8c937b162c6dbf479a9d19582b3e5313"
EXPECTED_COMMAND_COUNT = 66
EXPECTED_WALL_COUNT = 13
EXPECTED_OPENING_COUNT = 13
ALLOWED_OPS = frozenset({"CREATE_PRIMITIVE", "TRANSFORM_SET", "BOOLEAN", "QA_RUN"})
SAFE_QA_CHECKS = frozenset({
    "source_wall_opening_ids_exact",
    "walkmyplan_coordinate_alignment",
    "door_openings_unobstructed",
    "floor_contact_and_wall_continuity",
    "existing_corridor_assets_preserved",
    "no_inferred_dimensions",
})
NAME_RE = re.compile(r"^(?:wall|opening_cutter)_\d+$")
WALL_RE = re.compile(r"^wall_\d+$")
CUTTER_RE = re.compile(r"^opening_cutter_\d+$")


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="NEVER TEAR staged Structure Module Blender executor")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(raw)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bounded_number(value: object, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError("numeric value required")
    number = float(value)
    if not math.isfinite(number) or number < low or number > high:
        raise ContractError("numeric value outside bounded contract")
    return number


def vec3(value: object, low: float, high: float) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ContractError("vec3 required")
    return tuple(bounded_number(v, low, high) for v in value)  # type: ignore[return-value]


def three_point_to_blender(v: tuple[float, float, float]) -> tuple[float, float, float]:
    return (v[0], -v[2], v[1])


def three_size_to_blender(v: tuple[float, float, float]) -> tuple[float, float, float]:
    return (v[0], v[2], v[1])


def three_rotation_to_blender(v: tuple[float, float, float]) -> tuple[float, float, float]:
    if abs(v[0]) > 1e-9 or abs(v[2]) > 1e-9:
        raise ContractError("staged Structure route permits Three Y-axis rotation only")
    return (0.0, 0.0, v[1])


def load_plan(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ContractError("plan must be an object")
    allowed_top = {
        "schema", "project_key", "task_id", "run_id", "module_id",
        "coordinate_contract", "source_geometry_sha256",
        "source_production_plan_id", "source_production_plan_sha256",
        "commands", "policy", "plan_id", "plan_sha256",
    }
    if set(raw) - allowed_top:
        raise ContractError("plan contains non-contract top-level keys")
    if raw.get("schema") != "never-tear-ai3d-module-production-plan-v1":
        raise ContractError("plan schema rejected")
    if raw.get("project_key") != "never_tear_ai3d_engine" or raw.get("task_id") != "AI3D-010":
        raise ContractError("project/task lineage rejected")
    if raw.get("module_id") != "central_corridor_structure_base":
        raise ContractError("module identity rejected")
    if raw.get("coordinate_contract") != COORDINATE_CONTRACT:
        raise ContractError("coordinate contract rejected")
    if raw.get("source_geometry_sha256") != EXPECTED_GEOMETRY_SHA256:
        raise ContractError("geometry authority SHA rejected")
    if raw.get("source_production_plan_id") != EXPECTED_SOURCE_PLAN_ID:
        raise ContractError("source production plan id rejected")
    if raw.get("source_production_plan_sha256") != EXPECTED_SOURCE_PLAN_SHA256:
        raise ContractError("source production plan SHA rejected")
    if raw.get("plan_id") != EXPECTED_PLAN_ID or raw.get("plan_sha256") != EXPECTED_PLAN_SHA256:
        raise ContractError("module plan identity/SHA rejected")
    policy = raw.get("policy")
    if not isinstance(policy, dict):
        raise ContractError("policy missing")
    if policy.get("geometry_mutated") is not False or policy.get("inferred_dimensions") is not False:
        raise ContractError("geometry inference/mutation policy rejected")
    if policy.get("physical_execution_claimed") is not False or policy.get("legacy_worker_eligible") is not False:
        raise ContractError("physical/legacy policy rejected")
    commands = raw.get("commands")
    if not isinstance(commands, list) or len(commands) != EXPECTED_COMMAND_COUNT:
        raise ContractError("command count rejected")
    return raw


def validate_command(command: object) -> dict[str, Any]:
    if not isinstance(command, dict):
        raise ContractError("command must be object")
    allowed_command = {"command_id", "op", "params", "lineage", "routes"}
    if set(command) - allowed_command:
        raise ContractError("command contains non-contract keys")
    command_id = str(command.get("command_id") or "")
    op = str(command.get("op") or "")
    params = command.get("params")
    if len(command_id) < 4 or op not in ALLOWED_OPS or not isinstance(params, dict):
        raise ContractError("command identity/op/params rejected")
    routes = command.get("routes")
    if routes != ["WEBGL", "WINDOWS_WORKER"]:
        raise ContractError("command routes rejected")
    lineage = command.get("lineage")
    if not isinstance(lineage, dict) or not isinstance(lineage.get("module_id"), str):
        raise ContractError("command lineage rejected")

    if op == "CREATE_PRIMITIVE":
        if set(params) != {"name", "kind", "position", "size"}:
            raise ContractError("CREATE_PRIMITIVE params rejected")
        name = str(params.get("name") or "")
        if not NAME_RE.fullmatch(name) or params.get("kind") != "box":
            raise ContractError("primitive identity/kind rejected")
        vec3(params.get("position"), -200.0, 200.0)
        size = vec3(params.get("size"), 0.01, 100.0)
        if min(size) <= 0:
            raise ContractError("primitive size rejected")
    elif op == "TRANSFORM_SET":
        if set(params) != {"name", "rotation"}:
            raise ContractError("TRANSFORM_SET params rejected")
        name = str(params.get("name") or "")
        if not NAME_RE.fullmatch(name):
            raise ContractError("transform name rejected")
        three_rotation_to_blender(vec3(params.get("rotation"), -2 * math.pi, 2 * math.pi))
    elif op == "BOOLEAN":
        if set(params) != {"target", "tool", "mode", "keep_tool"}:
            raise ContractError("BOOLEAN params rejected")
        target = str(params.get("target") or "")
        tool = str(params.get("tool") or "")
        if not WALL_RE.fullmatch(target) or not CUTTER_RE.fullmatch(tool):
            raise ContractError("boolean object identity rejected")
        if params.get("mode") != "subtract" or params.get("keep_tool") is not False:
            raise ContractError("boolean mode rejected")
    elif op == "QA_RUN":
        if command_id != "central-corridor-module-qa" or set(params) != {"checks"}:
            raise ContractError("QA_RUN identity rejected")
        checks = params.get("checks")
        if not isinstance(checks, list) or set(map(str, checks)) != SAFE_QA_CHECKS:
            raise ContractError("QA_RUN checks rejected")
    return command


def validate_plan_commands(plan: dict[str, Any]) -> list[dict[str, Any]]:
    commands = [validate_command(command) for command in plan["commands"]]
    command_ids = [str(command["command_id"]) for command in commands]
    if len(set(command_ids)) != len(command_ids):
        raise ContractError("duplicate command id")
    counts = {op: sum(1 for command in commands if command["op"] == op) for op in ALLOWED_OPS}
    expected = {"CREATE_PRIMITIVE": 26, "TRANSFORM_SET": 26, "BOOLEAN": 13, "QA_RUN": 1}
    if counts != expected:
        raise ContractError(f"operation counts rejected: {counts}")
    return commands


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def add_box(name: str, position: tuple[float, float, float], size: tuple[float, float, float]) -> bpy.types.Object:
    mapped_position = three_point_to_blender(position)
    mapped_size = three_size_to_blender(size)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=mapped_position)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = mapped_size
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def apply_rotation(obj: bpy.types.Object, rotation: tuple[float, float, float]) -> None:
    obj.rotation_euler = three_rotation_to_blender(rotation)


def subtract_boolean(target: bpy.types.Object, tool: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    tool.select_set(False)
    modifier = target.modifiers.new(name=f"NT_BOOL_{tool.name}", type="BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = tool
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(tool, do_unlink=True)


def make_material(name: str, base: tuple[float, float, float, float], roughness: float, metallic: float = 0.0) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return material


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area_light(name: str, location: tuple[float, float, float], target: tuple[float, float, float], energy: float, size: float) -> None:
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "RECTANGLE"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)


def decorate_and_camera(walls: list[bpy.types.Object]) -> bpy.types.Object:
    wall_material = make_material("NT_Structure_Concrete", (0.18, 0.21, 0.24, 1.0), 0.72, 0.05)
    for wall in walls:
        if len(wall.data.materials) == 0:
            wall.data.materials.append(wall_material)

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(50.0, -20.0, 0.0))
    floor = bpy.context.object
    floor.name = "NT_CentralCorridor_Floor"
    floor.dimensions = (48.0, 8.0, 0.0)
    bpy.context.view_layer.objects.active = floor
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    floor.data.materials.append(make_material("NT_Floor", (0.055, 0.065, 0.075, 1.0), 0.88, 0.08))

    camera_data = bpy.data.cameras.new("NT_Structure_Camera")
    camera = bpy.data.objects.new("NT_Structure_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (50.0, -51.0, 19.0)
    camera.data.lens = 42.0
    look_at(camera, (50.0, -20.0, 1.6))
    bpy.context.scene.camera = camera

    add_area_light("NT_Key", (50.0, -20.0, 16.0), (50.0, -20.0, 1.0), 4800.0, 20.0)
    add_area_light("NT_Fill_West", (27.0, -20.0, 7.0), (42.0, -20.0, 1.2), 2600.0, 10.0)
    add_area_light("NT_Fill_East", (73.0, -20.0, 7.0), (58.0, -20.0, 1.2), 2600.0, 10.0)

    world = bpy.context.scene.world or bpy.data.worlds.new("NT_Structure_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.012, 0.016, 0.022, 1.0)
    background.inputs["Strength"].default_value = 0.18
    return camera


def decoded_png_pixel_sha(png: Path, width: int, height: int) -> str:
    image = bpy.data.images.load(str(png), check_existing=False)
    try:
        if tuple(image.size) != (width, height):
            raise RuntimeError(f"decoded PNG size mismatch: {tuple(image.size)}")
        pixels = array("f", image.pixels[:])
        if len(pixels) != width * height * 4:
            raise RuntimeError("decoded pixel count mismatch")
        return sha256_bytes(pixels.tobytes())
    finally:
        bpy.data.images.remove(image)


def main() -> None:
    args = parse_args()
    plan_path = Path(args.plan).resolve()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    plan = load_plan(plan_path)
    commands = validate_plan_commands(plan)
    reset_scene()
    objects: dict[str, bpy.types.Object] = {}
    boolean_count = 0

    for command in commands:
        op = command["op"]
        params = command["params"]
        if op == "CREATE_PRIMITIVE":
            name = str(params["name"])
            if name in objects or bpy.data.objects.get(name) is not None:
                raise ContractError(f"duplicate Blender object name: {name}")
            objects[name] = add_box(name, vec3(params["position"], -200, 200), vec3(params["size"], 0.01, 100))
        elif op == "TRANSFORM_SET":
            name = str(params["name"])
            obj = objects.get(name)
            if obj is None:
                raise ContractError(f"transform target missing: {name}")
            apply_rotation(obj, vec3(params["rotation"], -2 * math.pi, 2 * math.pi))
        elif op == "BOOLEAN":
            target_name = str(params["target"])
            tool_name = str(params["tool"])
            target = objects.get(target_name)
            tool = objects.get(tool_name)
            if target is None or tool is None:
                raise ContractError(f"boolean target/tool missing: {target_name}/{tool_name}")
            subtract_boolean(target, tool)
            objects.pop(tool_name, None)
            boolean_count += 1
        elif op == "QA_RUN":
            pass

    walls = [obj for name, obj in objects.items() if WALL_RE.fullmatch(name)]
    cutters = [name for name in objects if CUTTER_RE.fullmatch(name)]
    camera = decorate_and_camera(walls)

    width, height = 1280, 720
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.filepath = str(output_dir / "central_corridor_structure_stage.png")
    scene.view_settings.look = "AgX - Medium High Contrast"

    blend_path = output_dir / "central_corridor_structure_stage.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    bpy.ops.render.render(write_still=True)

    png_path = Path(scene.render.filepath)
    if not png_path.is_file() or png_path.stat().st_size <= 0:
        raise RuntimeError("render PNG missing")
    png_sha = sha256_file(png_path)
    raw_pixel_sha = decoded_png_pixel_sha(png_path, width, height)

    floor_contacts = []
    for wall in walls:
        floor_contacts.append(abs(float(wall.location.z - wall.dimensions.z / 2.0)) <= 1e-4)

    checks = {
        "plan_identity_exact": plan["plan_id"] == EXPECTED_PLAN_ID and plan["plan_sha256"] == EXPECTED_PLAN_SHA256,
        "source_geometry_sha_exact": plan["source_geometry_sha256"] == EXPECTED_GEOMETRY_SHA256,
        "command_count_exact": len(commands) == EXPECTED_COMMAND_COUNT,
        "allowed_ops_only": all(command["op"] in ALLOWED_OPS for command in commands),
        "wall_count_exact": len(walls) == EXPECTED_WALL_COUNT,
        "cutter_count_zero_after_booleans": len(cutters) == 0,
        "boolean_count_exact": boolean_count == EXPECTED_OPENING_COUNT,
        "wall_floor_contact": bool(floor_contacts) and all(floor_contacts),
        "all_wall_dimensions_positive": all(min(map(float, wall.dimensions)) > 0 for wall in walls),
        "camera_exists": bpy.data.objects.get(camera.name) is not None,
        "png_exists": png_path.is_file() and png_path.stat().st_size > 0,
        "decoded_pixel_hash_distinct": len(raw_pixel_sha) == 64 and raw_pixel_sha != png_sha,
        "blend_saved": blend_path.is_file() and blend_path.stat().st_size > 0,
        "background_mode": bool(bpy.app.background),
        "physical_execution_not_claimed": True,
        "canary_not_promoted": True,
    }
    status = "PASS" if all(checks.values()) else "FAIL"

    checkpoint_state = {
        "schema": RESULT_SCHEMA,
        "action": ACTION,
        "evidence_class": EVIDENCE_CLASS,
        "module_plan_id": plan["plan_id"],
        "module_plan_sha256": plan["plan_sha256"],
        "source_geometry_sha256": plan["source_geometry_sha256"],
        "coordinate_contract": COORDINATE_CONTRACT,
        "mapping_contract": MAPPING_CONTRACT,
        "wall_count": len(walls),
        "opening_boolean_count": boolean_count,
        "checks": checks,
        "physical_execution_claimed": False,
        "canary_promoted": False,
    }
    checkpoint_sha = sha256_bytes(json.dumps(checkpoint_state, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    checkpoint_id = f"cp-stage-{checkpoint_sha[:16]}"

    result = {
        "schema_version": RESULT_SCHEMA,
        "project_key": "never_tear_ai3d_engine",
        "task_id": "AI3D-011",
        "source_task_id": "AI3D-010",
        "action": ACTION,
        "status": status,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "module_plan_id": plan["plan_id"],
        "module_plan_sha256": plan["plan_sha256"],
        "source_geometry_sha256": plan["source_geometry_sha256"],
        "coordinate_contract": COORDINATE_CONTRACT,
        "mapping_contract": MAPPING_CONTRACT,
        "command_count": len(commands),
        "wall_count": len(walls),
        "opening_boolean_count": boolean_count,
        "render": {
            "png_file": png_path.name,
            "png_sha256": png_sha,
            "raw_pixel_sha256": raw_pixel_sha,
            "raw_pixel_format": "RGBA_FLOAT32_DECODED_PNG",
            "width": width,
            "height": height,
            "renderer": f"Blender {bpy.app.version_string} / EEVEE Next",
        },
        "blend_file": blend_path.name,
        "blend_sha256": sha256_file(blend_path),
        "checks": checks,
        "checkpoint_id": checkpoint_id,
        "checkpoint_sha256": checkpoint_sha,
        "physical_execution_claimed": False,
        "visual_qa": "PENDING",
        "canary_promoted": False,
        "promotion_allowed": False,
        "next_action": "Use this staged executor only after AI3D-002 physical CANARY and AI3D-004 real Physical QA PASS; then promote via a separately reviewed allowlist change.",
    }
    result_path = output_dir / "structure_module_stage_result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "schema": "never-tear-ai3d-structure-module-stage-manifest-v1",
        "evidence_class": EVIDENCE_CLASS,
        "physical_execution_claimed": False,
        "files": {
            png_path.name: {"sha256": png_sha, "size_bytes": png_path.stat().st_size},
            blend_path.name: {"sha256": result["blend_sha256"], "size_bytes": blend_path.stat().st_size},
            result_path.name: {"sha256": sha256_file(result_path), "size_bytes": result_path.stat().st_size},
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if status != "PASS":
        raise SystemExit(23)


if __name__ == "__main__":
    main()
