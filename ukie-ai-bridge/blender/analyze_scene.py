"""UKIE AI BRIDGE read-only Blender scene analyzer + ephemeral previews.

Run with:
  blender.exe -b input.blend --python analyze_scene.py -- \
    --output <scene_before.json> \
    --preview-front <preview_front.png> \
    --preview-side <preview_side.png>

The script never saves the .blend file. Preview camera/lights exist only in the
in-memory disposable working copy and are removed before exit. The scene report
is captured before preview helper objects are created.
"""

import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone

import bpy
from mathutils import Vector


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="surrogatepass")).hexdigest()


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--preview-front")
    parser.add_argument("--preview-side")
    return parser.parse_args(argv)


def serialize_vector(v):
    return [float(x) for x in v]


def object_record(obj):
    data = {
        "name": obj.name,
        "type": obj.type,
        "location": serialize_vector(obj.location),
        "rotation_mode": obj.rotation_mode,
        "rotation_euler": serialize_vector(obj.rotation_euler),
        "scale": serialize_vector(obj.scale),
        "hide_render": bool(obj.hide_render),
        "parent": obj.parent.name if obj.parent else None,
        "modifiers": [
            {"name": m.name, "type": m.type, "show_render": bool(m.show_render)}
            for m in obj.modifiers
        ],
        "constraints": [
            {"name": c.name, "type": c.type, "mute": bool(c.mute)}
            for c in obj.constraints
        ],
    }

    if obj.type == "MESH" and obj.data:
        mesh = obj.data
        topo_source = {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
            "loops": len(mesh.loops),
            "uv_layers": [u.name for u in mesh.uv_layers],
            "materials": [m.name if m else None for m in mesh.materials],
        }
        data["mesh"] = topo_source
        data["topology_digest"] = sha256_text(json.dumps(topo_source, ensure_ascii=False, sort_keys=True))
        data["shape_keys"] = (
            [kb.name for kb in mesh.shape_keys.key_blocks]
            if mesh.shape_keys and mesh.shape_keys.key_blocks
            else []
        )

    if obj.type == "ARMATURE" and obj.data:
        data["armature"] = {
            "bones": [b.name for b in obj.data.bones],
            "pose_bones": [
                {
                    "name": pb.name,
                    "constraints": [
                        {"name": c.name, "type": c.type, "mute": bool(c.mute)}
                        for c in pb.constraints
                    ],
                }
                for pb in obj.pose.bones
            ] if obj.pose else [],
        }

    return data


def scene_bounds(scene):
    points = []
    for obj in scene.objects:
        if obj.hide_render or obj.type in {"CAMERA", "LIGHT", "SPEAKER"}:
            continue
        try:
            for corner in obj.bound_box:
                points.append(obj.matrix_world @ Vector(corner))
        except (AttributeError, TypeError, ValueError):
            pass

    if not points:
        return Vector((0.0, 0.0, 0.0)), Vector((2.0, 2.0, 2.0))

    mins = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maxs = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (mins + maxs) * 0.5
    size = maxs - mins
    size.x = max(size.x, 0.1)
    size.y = max(size.y, 0.1)
    size.z = max(size.z, 0.1)
    return center, size


def look_at(obj, target):
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _new_area_light(scene, name, location, energy, size, target):
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)
    return obj, data


def render_preview(scene, path, view, center, size):
    """Render an orthographic QA image without saving scene changes."""
    output = os.path.abspath(path)
    os.makedirs(os.path.dirname(output), exist_ok=True)

    original = {
        "camera": scene.camera,
        "engine": scene.render.engine,
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "resolution_percentage": scene.render.resolution_percentage,
        "filepath": scene.render.filepath,
        "film_transparent": scene.render.film_transparent,
    }

    camera_data = bpy.data.cameras.new(name="UKIE_QA_CAMERA_DATA")
    camera = bpy.data.objects.new("UKIE_QA_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type = "ORTHO"

    span = max(size.x, size.y, size.z, 0.5)
    camera_data.ortho_scale = max(size.z * 1.18, span * 1.18, 0.75)
    distance = max(span * 3.0, 3.0)
    if view == "FRONT":
        camera.location = center + Vector((0.0, -distance, 0.0))
    elif view == "SIDE":
        camera.location = center + Vector((distance, 0.0, 0.0))
    else:
        raise ValueError("unsupported preview view")
    look_at(camera, center)

    lights = []
    light_datas = []
    for name, location, energy in (
        ("UKIE_QA_KEY", center + Vector((-distance * 0.65, -distance * 0.7, distance * 0.8)), 1100.0),
        ("UKIE_QA_FILL", center + Vector((distance * 0.65, -distance * 0.35, distance * 0.25)), 650.0),
        ("UKIE_QA_RIM", center + Vector((0.0, distance * 0.7, distance * 0.55)), 850.0),
    ):
        obj, data = _new_area_light(scene, name, location, energy, max(span, 1.0), center)
        lights.append(obj)
        light_datas.append(data)

    try:
        # Blender 4.2 production pin provides EEVEE Next. Rendering occurs only
        # on the disposable working copy and no save operator is called.
        scene.render.engine = "BLENDER_EEVEE_NEXT"
        scene.camera = camera
        scene.render.resolution_x = 512
        scene.render.resolution_y = 512
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = False
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = output
        bpy.ops.render.render(write_still=True)
    finally:
        scene.camera = original["camera"]
        scene.render.engine = original["engine"]
        scene.render.resolution_x = original["resolution_x"]
        scene.render.resolution_y = original["resolution_y"]
        scene.render.resolution_percentage = original["resolution_percentage"]
        scene.render.filepath = original["filepath"]
        scene.render.film_transparent = original["film_transparent"]

        for obj in lights:
            bpy.data.objects.remove(obj, do_unlink=True)
        for data in light_datas:
            if data.users == 0:
                bpy.data.lights.remove(data)
        bpy.data.objects.remove(camera, do_unlink=True)
        if camera_data.users == 0:
            bpy.data.cameras.remove(camera_data)

    if not os.path.isfile(output) or os.path.getsize(output) < 1024:
        raise RuntimeError("preview render did not produce a valid PNG")
    return {"path": output, "byte_size": os.path.getsize(output), "view": view}


def main():
    args = parse_args()
    scene = bpy.context.scene
    filepath = bpy.data.filepath

    # Capture evidence before adding any temporary QA objects.
    report = {
        "schema_version": "ukie_scene_report_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "ANALYZE_ONLY",
        "blender_version": bpy.app.version_string,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "source_file_basename": os.path.basename(filepath),
        "scene_name": scene.name,
        "frame_current": int(scene.frame_current),
        "render_engine": scene.render.engine,
        "objects": [object_record(o) for o in sorted(scene.objects, key=lambda x: x.name)],
        "collections": [c.name for c in bpy.data.collections],
        "materials": [m.name for m in bpy.data.materials],
        "images": [
            {"name": i.name, "filepath": i.filepath, "packed": bool(i.packed_file)}
            for i in bpy.data.images
        ],
        "libraries": [
            {"name": lib.name, "filepath": lib.filepath}
            for lib in bpy.data.libraries
        ],
        "cameras": [o.name for o in scene.objects if o.type == "CAMERA"],
        "lights": [o.name for o in scene.objects if o.type == "LIGHT"],
    }

    output = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    center, size = scene_bounds(scene)
    previews = []
    if args.preview_front:
        previews.append(render_preview(scene, args.preview_front, "FRONT", center, size))
    if args.preview_side:
        previews.append(render_preview(scene, args.preview_side, "SIDE", center, size))

    print(
        "UKIE_ANALYZE_OK "
        f"output={output} objects={len(report['objects'])} previews={len(previews)}"
    )


if __name__ == "__main__":
    main()
