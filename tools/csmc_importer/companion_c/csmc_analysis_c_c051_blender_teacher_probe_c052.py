# C-052 Blender teacher probe for C-051 source fixtures.
# Run inside Blender. Reads .blend source fixtures only and writes public-safe JSON metadata.
# It never reads or writes .csmc and never invokes MODELER/runtime/Worker/Canary/Control Gate.

import bpy
import json
from collections import Counter
from pathlib import Path

ROOT = Path.home() / "Desktop" / "CSMC_C051_NEXT_CONTROLS"
OUT = ROOT / "CSMC_C051_BLENDER_TEACHER_MANIFEST.json"

FILES = {
    "MAT3_ALLUSED": "CSMC_C051_MAT3_ALLUSED.blend",
    "MAT3_ONEUSED": "CSMC_C051_MAT3_ONEUSED.blend",
    "THREE_CUBES": "CSMC_C051_THREE_CUBES.blend",
    "UV_OFF": "CSMC_C051_UV_OFF.blend",
    "UV_ON": "CSMC_C051_UV_ON.blend",
    "W50_50": "CSMC_C051_W50_50.blend",
    "W25_75": "CSMC_C051_W25_75.blend",
}


def tri_count(mesh):
    # Deterministic topology count without applying modifiers.
    return sum(max(0, len(poly.vertices) - 2) for poly in mesh.polygons)


def inspect_current(fixture_id, source_name):
    mesh_objects = sorted((o for o in bpy.context.scene.objects if o.type == "MESH"), key=lambda o: o.name)
    arm_objects = sorted((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), key=lambda o: o.name)

    vertices_total = sum(len(o.data.vertices) for o in mesh_objects)
    triangles_total = sum(tri_count(o.data) for o in mesh_objects)
    material_slot_names = []
    used_material_indices = set()
    uv_layers_total = 0
    vertex_group_names = []
    assignment_count = 0
    weights = []

    for obj in mesh_objects:
        material_slot_names.extend(slot.material.name if slot.material else "" for slot in obj.material_slots)
        used_material_indices.update(poly.material_index for poly in obj.data.polygons if obj.material_slots)
        uv_layers_total += len(obj.data.uv_layers)
        vertex_group_names.extend(g.name for g in obj.vertex_groups)
        for vertex in obj.data.vertices:
            for membership in vertex.groups:
                assignment_count += 1
                weights.append(round(float(membership.weight), 6))

    bone_names = []
    for arm in arm_objects:
        bone_names.extend(b.name for b in arm.data.bones)

    hist = Counter(weights)
    return {
        "fixture_id": fixture_id,
        "source_blend_filename": source_name,
        "mesh_object_names": [o.name for o in mesh_objects],
        "mesh_data_names": [o.data.name for o in mesh_objects],
        "mesh_object_count": len(mesh_objects),
        "vertices_total": vertices_total,
        "triangles_total": triangles_total,
        "material_slot_names": material_slot_names,
        "material_slots_total": sum(len(o.material_slots) for o in mesh_objects),
        "used_material_indices_total": len(used_material_indices),
        "uv_layers_total": uv_layers_total,
        "armature_object_names": [o.name for o in arm_objects],
        "bone_names": bone_names,
        "bones_total": len(bone_names),
        "vertex_group_names": vertex_group_names,
        "weight_assignments_total": assignment_count,
        "weight_histogram": {str(k): v for k, v in sorted(hist.items())},
    }


rows = []
for fixture_id, filename in FILES.items():
    path = ROOT / filename
    if not path.exists():
        raise FileNotFoundError(path)
    bpy.ops.wm.open_mainfile(filepath=str(path))
    rows.append(inspect_current(fixture_id, filename))

manifest = {
    "schema_version": "csmc_c051_blender_teacher_manifest_v1",
    "source_type": "BLENDER_SOURCE_FIXTURE_METADATA_ONLY",
    "csmc_bytes_present": False,
    "runtime_dispatch": False,
    "semantic_promotion": False,
    "fixtures": rows,
}
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print("C-052 teacher manifest written:", OUT)
