"""Generate the UKIE AI BRIDGE Blender canary fixture.

This script is ONLY for a new disposable fixture created by the Bridge. It never
opens or modifies user project files. It intentionally saves one generated .blend
so the subsequent ANALYZE_ONLY path can prove source-copy/hash invariants.
"""

import argparse
import os
import sys

import bpy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    output = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output), exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
    cube = bpy.context.active_object
    cube.name = "UKIE_CANARY_CUBE"
    cube["ukie_canary"] = True
    cube["expected_vertices"] = 8
    cube["expected_polygons"] = 6

    mat = bpy.data.materials.new(name="UKIE_CANARY_MATERIAL")
    mat.diffuse_color = (0.18, 0.52, 0.82, 1.0)
    cube.data.materials.append(mat)

    scene = bpy.context.scene
    scene["ukie_canary_schema"] = "ukie_blender_canary_v1"
    scene["expected_object_name"] = cube.name

    bpy.ops.wm.save_as_mainfile(filepath=output, check_existing=False)
    if not os.path.isfile(output) or os.path.getsize(output) < 1024:
        raise RuntimeError("canary .blend was not created")
    print(f"UKIE_CANARY_CREATED path={output} size={os.path.getsize(output)}")


if __name__ == "__main__":
    main()
