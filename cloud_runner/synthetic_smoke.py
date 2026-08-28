# SPDX-License-Identifier: MIT
"""BP3D Cloud Runner synthetic smoke test.

This script intentionally uses no user assets. It creates procedural geometry in a
factory-startup Blender process, records deterministic mesh facts, and exits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone

import bpy


def parse_args() -> argparse.Namespace:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    return parser.parse_args(raw)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    args = parse_args()
    out_dir = os.path.abspath(args.output)
    os.makedirs(out_dir, exist_ok=True)

    # Factory-startup should already be empty, but make the test independent of
    # startup-file contents and deterministic.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
    cube = bpy.context.object
    cube.name = "BP3D_SYNTHETIC_CUBE"

    # Add one deterministic modifier so the smoke test exercises dependency-graph
    # evaluation rather than only reading the source mesh datablock.
    bevel = cube.modifiers.new(name="BP3D_TEST_BEVEL", type="BEVEL")
    bevel.width = 0.125
    bevel.segments = 2

    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = cube.evaluated_get(depsgraph)
    evaluated_mesh = evaluated.to_mesh()
    try:
        evaluated_counts = {
            "vertices": len(evaluated_mesh.vertices),
            "edges": len(evaluated_mesh.edges),
            "polygons": len(evaluated_mesh.polygons),
        }
    finally:
        evaluated.to_mesh_clear()

    source_counts = {
        "vertices": len(cube.data.vertices),
        "edges": len(cube.data.edges),
        "polygons": len(cube.data.polygons),
    }

    # The expected source cube topology is stable and provides a strict pass/fail
    # assertion without depending on any external file.
    source_ok = source_counts == {"vertices": 8, "edges": 12, "polygons": 6}
    evaluated_ok = (
        evaluated_counts["vertices"] > source_counts["vertices"]
        and evaluated_counts["polygons"] > source_counts["polygons"]
    )

    fingerprint_payload = json.dumps(
        {
            "source": source_counts,
            "evaluated": evaluated_counts,
            "object": cube.name,
            "modifier": {"type": bevel.type, "width": bevel.width, "segments": bevel.segments},
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    result = {
        "schema_version": "bp3d_cloud_smoke_v1",
        "status": "PASS" if source_ok and evaluated_ok else "FAIL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "blender_version": bpy.app.version_string,
        "blender_background": bpy.app.background,
        "factory_startup_expected": True,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "object_name": cube.name,
        "source_mesh": source_counts,
        "evaluated_mesh": evaluated_counts,
        "checks": {
            "source_cube_topology": source_ok,
            "modifier_evaluation_changed_topology": evaluated_ok,
            "background_mode": bool(bpy.app.background),
        },
        "synthetic_only": True,
        "user_assets_loaded": False,
        "fingerprint_sha256": sha256_text(fingerprint_payload),
    }

    result_path = os.path.join(out_dir, "bp3d_cloud_smoke_result.json")
    with open(result_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print("BP3D_CLOUD_SMOKE_RESULT=" + json.dumps(result, sort_keys=True), flush=True)
    if result["status"] != "PASS" or not result["checks"]["background_mode"]:
        raise SystemExit(21)


if __name__ == "__main__":
    main()
