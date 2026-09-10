"""UKIE AI BRIDGE P0 read-only Blender scene analyzer.

Run with:
  blender.exe -b input.blend --python analyze_scene.py -- --output <scene_before.json>

This script does not save the .blend file and does not mutate scene data.
"""

import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone

import bpy


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="surrogatepass")).hexdigest()


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
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


def main():
    args = parse_args()
    scene = bpy.context.scene
    filepath = bpy.data.filepath

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
            {
                "name": i.name,
                "filepath": i.filepath,
                "packed": bool(i.packed_file),
            }
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

    print(f"UKIE_ANALYZE_OK output={output} objects={len(report['objects'])}")


if __name__ == "__main__":
    main()
