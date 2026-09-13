# SPDX-License-Identifier: MIT
"""NEVER TEAR AI3D physical canary v2: Three.js Y-up → Blender Z-up.

Synthetic/procedural only. The logical MVP values remain identical to the
Base44/WebGL plan. This renderer explicitly maps them into Blender space,
produces a 960x540 PNG, re-opens that durable file, hashes decoded RGBA float
pixels separately from PNG bytes, and emits checkpoint/manifest evidence.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_KEY = "never_tear_ai3d_engine"
TASK_ID = "AI3D-001"
OBJECT_NAME = "MVP_Physical_Box"
THREE_SIZE = (1.8, 1.2, 1.4)
THREE_POSITION = (1.0, 0.6, -2.0)
THREE_ROTATION = (0.0, 0.35, 0.0)
THREE_CAMERA = (6.5, 4.2, 7.5)
THREE_TARGET = (1.0, 0.6, -2.0)
COLOR_SRGB = "#7c8792"
ROUGHNESS = 0.42
METALLIC = 0.12
WIDTH, HEIGHT = 960, 540


def parse_args() -> argparse.Namespace:
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    return p.parse_args(raw)


def three_point_to_blender(v: tuple[float, float, float]) -> tuple[float, float, float]:
    # Right-handed axis conversion: Three X/Y/Z → Blender X/-Z/Y.
    return (v[0], -v[2], v[1])


def three_size_to_blender(v: tuple[float, float, float]) -> tuple[float, float, float]:
    return (v[0], v[2], v[1])


def three_euler_xyz_to_blender_for_mvp(v: tuple[float, float, float]) -> tuple[float, float, float]:
    # MVP only rotates around Three Y. Under X/-Z/Y mapping this is Blender +Z.
    if abs(v[0]) > 1e-12 or abs(v[2]) > 1e-12:
        raise RuntimeError("MVP v2 only permits Three Y-axis rotation")
    return (0.0, 0.0, v[1])


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def linear_rgba(hex_color: str) -> tuple[float, float, float, float]:
    s = hex_color.lstrip("#")
    rgb = [int(s[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(rgb[0]), lin(rgb[1]), lin(rgb[2]), 1.0)


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def close3(actual, expected, tol: float = 1e-5) -> bool:
    return all(abs(float(a) - float(b)) <= tol for a, b in zip(actual, expected))


def build_scene() -> tuple[bpy.types.Object, bpy.types.Object, dict]:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    bp = three_point_to_blender(THREE_POSITION)
    bs = three_size_to_blender(THREE_SIZE)
    br = three_euler_xyz_to_blender_for_mvp(THREE_ROTATION)
    bc = three_point_to_blender(THREE_CAMERA)
    bt = three_point_to_blender(THREE_TARGET)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=bp, rotation=br)
    box = bpy.context.object
    box.name = OBJECT_NAME
    box.dimensions = bs
    bpy.context.view_layer.objects.active = box
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    material = bpy.data.materials.new("AI3D_MVP_Material")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = linear_rgba(COLOR_SRGB)
    bsdf.inputs["Roughness"].default_value = ROUGHNESS
    bsdf.inputs["Metallic"].default_value = METALLIC
    box.data.materials.append(material)

    # Three Y=0 is the logical floor; after conversion Blender Z=0.
    bpy.ops.mesh.primitive_plane_add(size=20.0, location=(bp[0], bp[1], 0.0))
    ground = bpy.context.object
    ground.name = "AI3D_MVP_Ground"
    gmat = bpy.data.materials.new("AI3D_Ground_Material")
    gmat.use_nodes = True
    gbsdf = gmat.node_tree.nodes.get("Principled BSDF")
    gbsdf.inputs["Base Color"].default_value = (0.055, 0.062, 0.075, 1.0)
    gbsdf.inputs["Roughness"].default_value = 0.9
    ground.data.materials.append(gmat)

    cam_data = bpy.data.cameras.new("AI3D_MVP_Camera")
    camera = bpy.data.objects.new("AI3D_MVP_Camera", cam_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = bc
    camera.data.lens = 50.0
    look_at(camera, bt)
    bpy.context.scene.camera = camera

    for name, loc, energy, size in (
        ("AI3D_Key", (4.5, -4.5, 7.0), 900.0, 4.0),
        ("AI3D_Fill", (-4.0, -1.0, 3.0), 500.0, 3.0),
        ("AI3D_Rim", (3.0, 7.0, 4.0), 650.0, 2.5),
    ):
        data = bpy.data.lights.new(name=name, type="AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(light)
        light.location = loc
        look_at(light, bt)

    world = bpy.context.scene.world or bpy.data.worlds.new("AI3D_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.018, 0.022, 0.03, 1.0)
    bg.inputs["Strength"].default_value = 0.22
    mapped = {"position": bp, "size": bs, "rotation": br, "camera": bc, "target": bt}
    return box, camera, mapped


def render(out: Path) -> tuple[Path, str]:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    png = out / "ai3d_physical_mvp.png"
    scene.render.filepath = str(png)
    bpy.ops.render.render(write_still=True)
    if not png.is_file() or png.stat().st_size <= 0:
        raise RuntimeError("physical PNG missing")
    decoded = bpy.data.images.load(str(png), check_existing=False)
    try:
        if tuple(decoded.size) != (WIDTH, HEIGHT):
            raise RuntimeError(f"decoded PNG size mismatch: {tuple(decoded.size)}")
        pixels = array("f", decoded.pixels[:])
        if len(pixels) != WIDTH * HEIGHT * 4:
            raise RuntimeError(f"decoded pixel count mismatch: {len(pixels)}")
        pixel_sha = sha256_bytes(pixels.tobytes())
    finally:
        bpy.data.images.remove(decoded)
    return png, pixel_sha


def main() -> None:
    out = Path(parse_args().output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    box, camera, mapped = build_scene()
    png, pixel_sha = render(out)
    png_sha = sha256_file(png)
    bsdf = box.data.materials[0].node_tree.nodes.get("Principled BSDF")
    ground_clearance = float(box.location.z - box.dimensions.z / 2.0)
    checks = {
        "object_exists": bpy.data.objects.get(OBJECT_NAME) is not None,
        "mapped_position_equals": close3(box.location, mapped["position"]),
        "mapped_rotation_equals": close3(box.rotation_euler, mapped["rotation"]),
        "mapped_dimensions_equals": close3(box.dimensions, mapped["size"]),
        "logical_floor_contact": abs(ground_clearance) <= 1e-5,
        "material_roughness_equals": abs(float(bsdf.inputs["Roughness"].default_value) - ROUGHNESS) <= 1e-6,
        "material_metallic_equals": abs(float(bsdf.inputs["Metallic"].default_value) - METALLIC) <= 1e-6,
        "camera_position_equals": close3(camera.location, mapped["camera"]),
        "render_png_exists": png.is_file() and png.stat().st_size > 0,
        "decoded_pixel_sha_distinct_evidence": len(pixel_sha) == 64 and pixel_sha != png_sha,
        "physical_background_mode": bool(bpy.app.background),
    }
    qa = "PASS" if all(checks.values()) else "FAIL"
    snapshot = {
        "project_key": PROJECT_KEY,
        "task_id": TASK_ID,
        "route": "BLENDER_GITHUB_ACTIONS_CYCLES_CPU",
        "coordinate_contract": "THREE_Y_UP_TO_BLENDER_Z_UP_V1",
        "logical_three": {"size": list(THREE_SIZE), "position": list(THREE_POSITION), "rotation": list(THREE_ROTATION), "camera": list(THREE_CAMERA), "target": list(THREE_TARGET)},
        "mapped_blender": {k: list(v) for k, v in mapped.items()},
        "material": {"color_srgb": COLOR_SRGB, "roughness": ROUGHNESS, "metallic": METALLIC},
        "render": {"width": WIDTH, "height": HEIGHT, "engine": "CYCLES", "device": "CPU", "samples": 16, "raw_pixel_sha256": pixel_sha, "png_sha256": png_sha},
        "automated_qa": qa,
        "visual_qa": "PENDING",
        "canary_promoted": False,
    }
    cp_sha = sha256_bytes(stable_json(snapshot).encode("utf-8"))
    result = {
        "schema_version": "never-tear-ai3d-blender-physical-mvp-v2",
        "project_key": PROJECT_KEY,
        "task_id": TASK_ID,
        "status": qa,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "route": "BLENDER_GITHUB_ACTIONS_CYCLES_CPU",
        "coordinate_contract": "THREE_Y_UP_TO_BLENDER_Z_UP_V1",
        "runner": {"blender_version": bpy.app.version_string, "blender_background": bpy.app.background, "python_version": platform.python_version(), "platform": platform.platform(), "github_run_id": os.environ.get("GITHUB_RUN_ID"), "github_sha": os.environ.get("GITHUB_SHA"), "github_ref": os.environ.get("GITHUB_REF")},
        "artifact": {"artifact_id": f"blender-render-{png_sha[:16]}", "type": "PIXEL_RENDER_EVIDENCE", "file": png.name, "width": WIDTH, "height": HEIGHT, "physical_render": True, "renderer": f"Blender {bpy.app.version_string} / Cycles CPU", "raw_pixel_format": "RGBA_FLOAT32_DECODED_PNG", "raw_pixel_sha256": pixel_sha, "png_sha256": png_sha, "size_bytes": png.stat().st_size, "readback_status": "PASS", "visual_qa": "PENDING"},
        "checks": checks,
        "checkpoint": {"checkpoint_id": f"cp-blender-{cp_sha[:16]}", "sha256": cp_sha, "snapshot": snapshot},
        "synthetic_only": True,
        "user_assets_loaded": False,
        "csmc_private_data_loaded": False,
        "canary_promoted": False,
        "next_action": "Visually inspect the mapped physical PNG. Promote AI3D-001 only after automated QA, provider readback and visual QA all PASS.",
    }
    result_path = out / "ai3d_physical_mvp_result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"schema_version": "never-tear-ai3d-artifact-manifest-v1", "files": {png.name: {"sha256": png_sha, "size_bytes": png.stat().st_size}, result_path.name: {"sha256": sha256_file(result_path), "size_bytes": result_path.stat().st_size}}}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("AI3D_PHYSICAL_MVP_RESULT=" + json.dumps(result, sort_keys=True), flush=True)
    if qa != "PASS":
        raise SystemExit(31)


if __name__ == "__main__":
    main()
