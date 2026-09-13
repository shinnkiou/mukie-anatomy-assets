# SPDX-License-Identifier: MIT
"""Bounded Blender action for NEVER TEAR AI3D Windows Worker canary.

This script is invoked only by the local AI3D worker with a locally-written,
strictly structured plan JSON. It never executes cloud-supplied code or paths.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

SCHEMA = "never-tear-ai3d-worker-render-v1"
ACTION = "ai3d_blender_physical_mvp_v1"
HEX = set("0123456789abcdefABCDEF")


def parse_args() -> argparse.Namespace:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
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


def stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def bounded_number(value: object, low: float, high: float) -> float:
    n = float(value)
    if not math.isfinite(n) or n < low or n > high:
        raise ValueError("number out of range")
    return n


def vec3(value: object, low: float, high: float) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError("vec3 required")
    return tuple(bounded_number(v, low, high) for v in value)  # type: ignore[return-value]


def load_plan(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("plan must be an object")
    obj = raw.get("object")
    camera = raw.get("camera")
    render = raw.get("render")
    if not isinstance(obj, dict) or not isinstance(camera, dict) or not isinstance(render, dict):
        raise ValueError("plan sections missing")
    if obj.get("name") != "MVP_Physical_Box" or obj.get("kind") != "box":
        raise ValueError("object contract rejected")
    material = obj.get("material")
    if not isinstance(material, dict):
        raise ValueError("material missing")
    color = str(material.get("color_srgb", ""))
    if len(color) != 7 or color[0] != "#" or any(ch not in HEX for ch in color[1:]):
        raise ValueError("invalid color")
    if render.get("engine") != "BLENDER_EEVEE_NEXT" or render.get("output_format") != "PNG":
        raise ValueError("render engine/format rejected")
    width = int(bounded_number(render.get("width"), 64, 2048))
    height = int(bounded_number(render.get("height"), 64, 2048))
    return {
        "object": {
            "name": "MVP_Physical_Box",
            "kind": "box",
            "size": vec3(obj.get("size"), 0.05, 20),
            "position": vec3(obj.get("position"), -100, 100),
            "rotation": vec3(obj.get("rotation"), -2 * math.pi, 2 * math.pi),
            "material": {
                "color_srgb": color.lower(),
                "roughness": bounded_number(material.get("roughness"), 0, 1),
                "metallic": bounded_number(material.get("metallic"), 0, 1),
            },
        },
        "camera": {
            "position": vec3(camera.get("position"), -100, 100),
            "target": vec3(camera.get("target"), -100, 100),
            "lens_mm": bounded_number(camera.get("lens_mm"), 12, 200),
        },
        "render": {
            "width": width,
            "height": height,
            "engine": "BLENDER_EEVEE_NEXT",
            "output_format": "PNG",
            "color_mode": "RGBA",
        },
    }


def hex_to_linear_rgba(hex_color: str) -> tuple[float, float, float, float]:
    srgb = [int(hex_color[i : i + 2], 16) / 255.0 for i in (1, 3, 5)]
    def linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (linear(srgb[0]), linear(srgb[1]), linear(srgb[2]), 1.0)


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def add_area_light(name: str, location: tuple[float, float, float], target: tuple[float, float, float], energy: float, size: float) -> None:
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)


def build_scene(plan: dict) -> tuple[bpy.types.Object, bpy.types.Object]:
    reset_scene()
    o = plan["object"]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=o["position"], rotation=o["rotation"])
    box = bpy.context.object
    box.name = o["name"]
    box.dimensions = o["size"]
    bpy.context.view_layer.objects.active = box
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    mat = bpy.data.materials.new("AI3D_MVP_Material")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_to_linear_rgba(o["material"]["color_srgb"])
    bsdf.inputs["Roughness"].default_value = o["material"]["roughness"]
    bsdf.inputs["Metallic"].default_value = o["material"]["metallic"]
    box.data.materials.append(mat)

    # Ground plane is local implementation detail, never cloud-addressable.
    bpy.ops.mesh.primitive_plane_add(size=20.0, location=(o["position"][0], 0.0, o["position"][2]))
    ground = bpy.context.object
    ground.name = "AI3D_MVP_Ground"
    gmat = bpy.data.materials.new("AI3D_Ground_Material")
    gmat.use_nodes = True
    gbsdf = gmat.node_tree.nodes.get("Principled BSDF")
    gbsdf.inputs["Base Color"].default_value = (0.055, 0.062, 0.075, 1.0)
    gbsdf.inputs["Roughness"].default_value = 0.9
    ground.data.materials.append(gmat)

    c = plan["camera"]
    camera_data = bpy.data.cameras.new("AI3D_MVP_Camera")
    camera = bpy.data.objects.new("AI3D_MVP_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = c["position"]
    camera.data.lens = c["lens_mm"]
    look_at(camera, c["target"])
    bpy.context.scene.camera = camera

    add_area_light("AI3D_Key", (4.5, 7.0, 4.5), c["target"], 900.0, 4.0)
    add_area_light("AI3D_Fill", (-4.0, 3.0, 1.0), c["target"], 500.0, 3.0)
    add_area_light("AI3D_Rim", (3.0, 4.0, -7.0), c["target"], 650.0, 2.5)

    world = bpy.context.scene.world or bpy.data.worlds.new("AI3D_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.018, 0.022, 0.03, 1.0)
    background.inputs["Strength"].default_value = 0.22
    return box, camera


def tuples_close(actual, expected, tolerance: float = 1e-5) -> bool:
    return all(abs(float(a) - float(b)) <= tolerance for a, b in zip(actual, expected))


def main() -> None:
    args = parse_args()
    plan_path = Path(args.plan).resolve()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if plan_path.parent != output_dir:
        raise RuntimeError("plan must be inside the worker-owned job directory")
    plan = load_plan(plan_path)
    box, camera = build_scene(plan)

    scene = bpy.context.scene
    r = plan["render"]
    scene.render.engine = r["engine"]
    scene.render.resolution_x = r["width"]
    scene.render.resolution_y = r["height"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(output_dir / "ai3d_physical_mvp.png")
    scene.view_settings.look = "AgX - Medium High Contrast"
    bpy.ops.render.render(write_still=True)

    png = Path(scene.render.filepath)
    if not png.is_file() or png.stat().st_size <= 0:
        raise RuntimeError("render PNG missing")
    render_result = bpy.data.images.get("Render Result")
    if render_result is None:
        raise RuntimeError("Render Result missing")
    pixels = array("f", [0.0]) * (r["width"] * r["height"] * 4)
    render_result.pixels.foreach_get(pixels)
    raw_pixel_sha = sha256_bytes(pixels.tobytes())
    png_sha = sha256_file(png)

    mat = box.data.materials[0]
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    checks = {
        "object_exists": bpy.data.objects.get("MVP_Physical_Box") is not None,
        "position_equals": tuples_close(box.location, plan["object"]["position"]),
        "rotation_equals": tuples_close(box.rotation_euler, plan["object"]["rotation"]),
        "dimensions_equals": tuples_close(box.dimensions, plan["object"]["size"]),
        "material_roughness_equals": abs(float(bsdf.inputs["Roughness"].default_value) - plan["object"]["material"]["roughness"]) <= 1e-6,
        "material_metallic_equals": abs(float(bsdf.inputs["Metallic"].default_value) - plan["object"]["material"]["metallic"]) <= 1e-6,
        "camera_position_equals": tuples_close(camera.location, plan["camera"]["position"]),
        "png_exists": png.is_file() and png.stat().st_size > 0,
        "background_mode": bool(bpy.app.background),
    }
    automated_qa = "PASS" if all(checks.values()) else "FAIL"
    checkpoint_state = {
        "action": ACTION,
        "plan": plan,
        "render": {
            "png_sha256": png_sha,
            "raw_pixel_sha256": raw_pixel_sha,
            "renderer": f"Blender {bpy.app.version_string} / EEVEE Next",
            "width": r["width"],
            "height": r["height"],
        },
        "automated_qa": automated_qa,
        "visual_qa": "PENDING",
        "canary_promoted": False,
    }
    checkpoint_sha = sha256_bytes(stable_json(checkpoint_state).encode("utf-8"))
    result = {
        "schema_version": SCHEMA,
        "action": ACTION,
        "status": automated_qa,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "png_file": png.name,
        "png_sha256": png_sha,
        "raw_pixel_sha256": raw_pixel_sha,
        "renderer": f"Blender {bpy.app.version_string} / EEVEE Next",
        "blender_version": bpy.app.version_string,
        "width": r["width"],
        "height": r["height"],
        "automated_qa": automated_qa,
        "visual_qa": "PENDING",
        "checkpoint_id": f"cp-worker-{checkpoint_sha[:16]}",
        "checkpoint_sha256": checkpoint_sha,
        "checks": checks,
        "physical_render": True,
        "canary_promoted": False,
    }
    (output_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("AI3D_WORKER_RESULT=" + json.dumps(result, sort_keys=True), flush=True)
    if automated_qa != "PASS":
        raise SystemExit(31)


if __name__ == "__main__":
    main()
