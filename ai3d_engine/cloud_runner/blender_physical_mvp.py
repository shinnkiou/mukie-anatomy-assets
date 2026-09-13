# SPDX-License-Identifier: MIT
"""NEVER TEAR AI3D physical-render canary for Blender 4.2.x.

Synthetic/procedural only. No user assets, CSMC data, credentials, or arbitrary
commands are loaded. The script implements the AI3D-001 vertical slice in a
factory-startup Blender process and emits durable render/checkpoint evidence.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
import os
import platform
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

SCHEMA = "never-tear-ai3d-blender-physical-mvp-v1"
PROJECT_KEY = "never_tear_ai3d_engine"
TASK_ID = "AI3D-001"
OBJECT_NAME = "MVP_Physical_Box"
SIZE = (1.8, 1.2, 1.4)
POSITION = (1.0, 0.6, -2.0)
ROTATION = (0.0, 0.35, 0.0)
COLOR_SRGB = "#7c8792"
ROUGHNESS = 0.42
METALLIC = 0.12
CAMERA_POSITION = (6.5, 4.2, 7.5)
CAMERA_TARGET = (1.0, 0.6, -2.0)
WIDTH = 960
HEIGHT = 540


def parse_args() -> argparse.Namespace:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    return parser.parse_args(raw)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hex_to_linear_rgba(hex_color: str) -> tuple[float, float, float, float]:
    value = hex_color.lstrip("#")
    srgb = [int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def to_linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    return (to_linear(srgb[0]), to_linear(srgb[1]), to_linear(srgb[2]), 1.0)


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def add_box() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=POSITION, rotation=ROTATION)
    box = bpy.context.object
    box.name = OBJECT_NAME
    box.dimensions = SIZE
    bpy.context.view_layer.objects.active = box
    box.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    material = bpy.data.materials.new("AI3D_MVP_Material")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_to_linear_rgba(COLOR_SRGB)
    bsdf.inputs["Roughness"].default_value = ROUGHNESS
    bsdf.inputs["Metallic"].default_value = METALLIC
    box.data.materials.append(material)
    return box


def add_ground() -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=20.0, location=(1.0, 0.0, -2.0))
    ground = bpy.context.object
    ground.name = "AI3D_MVP_Ground"
    material = bpy.data.materials.new("AI3D_Ground_Material")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.055, 0.062, 0.075, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.9
    ground.data.materials.append(material)
    return ground


def add_camera() -> bpy.types.Object:
    camera_data = bpy.data.cameras.new("AI3D_MVP_Camera")
    camera = bpy.data.objects.new("AI3D_MVP_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = CAMERA_POSITION
    camera.data.lens = 50.0
    look_at(camera, CAMERA_TARGET)
    bpy.context.scene.camera = camera
    return camera


def add_light(name: str, location: tuple[float, float, float], energy: float, size: float) -> bpy.types.Object:
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    light = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    look_at(light, CAMERA_TARGET)
    return light


def setup_scene() -> tuple[bpy.types.Object, bpy.types.Object]:
    clear_scene()
    box = add_box()
    add_ground()
    camera = add_camera()
    add_light("AI3D_Key", (4.5, 7.0, 4.5), 900.0, 4.0)
    add_light("AI3D_Fill", (-4.0, 3.0, 1.0), 500.0, 3.0)
    add_light("AI3D_Rim", (3.0, 4.0, -7.0), 650.0, 2.5)

    world = bpy.context.scene.world or bpy.data.worlds.new("AI3D_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.018, 0.022, 0.03, 1.0)
    background.inputs["Strength"].default_value = 0.22
    return box, camera


def close_tuple(actual, expected, tolerance: float = 1e-5) -> bool:
    return all(abs(float(a) - float(b)) <= tolerance for a, b in zip(actual, expected))


def render_physical(output_dir: Path) -> tuple[Path, str]:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.filepath = str(output_dir / "ai3d_physical_mvp.png")
    scene.render.use_file_extension = True

    scene.view_settings.look = "AgX - Medium High Contrast"
    bpy.ops.render.render(write_still=True)

    render_result = bpy.data.images.get("Render Result")
    if render_result is None:
        raise RuntimeError("Render Result image is missing")
    pixels = array("f", [0.0]) * (WIDTH * HEIGHT * 4)
    render_result.pixels.foreach_get(pixels)
    raw_pixel_sha256 = sha256_bytes(pixels.tobytes())
    return Path(scene.render.filepath), raw_pixel_sha256


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    box, camera = setup_scene()
    png_path, raw_pixel_sha256 = render_physical(output_dir)
    if not png_path.exists() or png_path.stat().st_size <= 0:
        raise RuntimeError("physical render PNG was not created")
    png_sha256 = sha256_file(png_path)

    material = box.data.materials[0]
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    material_ok = (
        abs(float(bsdf.inputs["Roughness"].default_value) - ROUGHNESS) <= 1e-6
        and abs(float(bsdf.inputs["Metallic"].default_value) - METALLIC) <= 1e-6
    )
    checks = {
        "object_exists": bpy.data.objects.get(OBJECT_NAME) is not None,
        "position_equals": close_tuple(box.location, POSITION),
        "rotation_equals": close_tuple(box.rotation_euler, ROTATION),
        "dimensions_equals": close_tuple(box.dimensions, SIZE),
        "material_parameters_equal": material_ok,
        "camera_position_equals": close_tuple(camera.location, CAMERA_POSITION),
        "render_png_exists": png_path.exists() and png_path.stat().st_size > 0,
        "physical_background_mode": bool(bpy.app.background),
    }
    automated_qa = "PASS" if all(checks.values()) else "FAIL"

    checkpoint_snapshot = {
        "project_key": PROJECT_KEY,
        "task_id": TASK_ID,
        "route": "BLENDER_GITHUB_ACTIONS",
        "object": {
            "name": OBJECT_NAME,
            "kind": "box",
            "size": list(SIZE),
            "position": list(POSITION),
            "rotation": list(ROTATION),
            "material": {"color_srgb": COLOR_SRGB, "roughness": ROUGHNESS, "metallic": METALLIC},
        },
        "camera": {"position": list(CAMERA_POSITION), "target": list(CAMERA_TARGET)},
        "render": {
            "width": WIDTH,
            "height": HEIGHT,
            "engine": bpy.context.scene.render.engine,
            "raw_pixel_sha256": raw_pixel_sha256,
            "png_sha256": png_sha256,
        },
        "automated_qa": automated_qa,
    }
    checkpoint_sha256 = sha256_bytes(stable_json(checkpoint_snapshot).encode("utf-8"))
    checkpoint_id = f"cp-blender-{checkpoint_sha256[:16]}"
    artifact_id = f"blender-render-{png_sha256[:16]}"

    result = {
        "schema_version": SCHEMA,
        "project_key": PROJECT_KEY,
        "task_id": TASK_ID,
        "status": automated_qa,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "route": "BLENDER_GITHUB_ACTIONS",
        "runner": {
            "blender_version": bpy.app.version_string,
            "blender_background": bpy.app.background,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_ref": os.environ.get("GITHUB_REF"),
        },
        "artifact": {
            "artifact_id": artifact_id,
            "type": "PIXEL_RENDER_EVIDENCE",
            "file": png_path.name,
            "width": WIDTH,
            "height": HEIGHT,
            "physical_render": True,
            "renderer": f"Blender {bpy.app.version_string} / EEVEE Next",
            "raw_pixel_format": "RGBA_FLOAT32_LINEAR",
            "raw_pixel_sha256": raw_pixel_sha256,
            "png_sha256": png_sha256,
            "size_bytes": png_path.stat().st_size,
            "visual_qa": "PENDING",
        },
        "checks": checks,
        "checkpoint": {
            "checkpoint_id": checkpoint_id,
            "sha256": checkpoint_sha256,
            "snapshot": checkpoint_snapshot,
        },
        "synthetic_only": True,
        "user_assets_loaded": False,
        "csmc_private_data_loaded": False,
        "canary_promoted": False,
        "next_action": "Visually inspect ai3d_physical_mvp.png. Promote AI3D-001 only if automated QA, artifact readback, and visual QA all PASS.",
    }

    result_path = output_dir / "ai3d_physical_mvp_result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "never-tear-ai3d-artifact-manifest-v1",
        "files": {
            png_path.name: {"sha256": png_sha256, "size_bytes": png_path.stat().st_size},
            result_path.name: {"sha256": sha256_file(result_path), "size_bytes": result_path.stat().st_size},
        },
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("AI3D_PHYSICAL_MVP_RESULT=" + json.dumps(result, sort_keys=True), flush=True)
    if automated_qa != "PASS":
        raise SystemExit(31)


if __name__ == "__main__":
    main()
