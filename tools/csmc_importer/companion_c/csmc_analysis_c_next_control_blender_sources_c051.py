# C-051 public-safe Blender fixture source generator.
# This script creates .blend/.fbx source fixtures only. It does NOT create .csmc,
# invoke MODELER, dispatch runtime jobs, or touch any mainline state.

import bpy
from pathlib import Path

OUT = Path.home() / "Desktop" / "CSMC_C051_NEXT_CONTROLS"
OUT.mkdir(parents=True, exist_ok=True)

def clear_scene():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)

def save_model(file_stem):
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"{file_stem}.blend"))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(
        filepath=str(OUT / f"{file_stem}.fbx"),
        use_selection=True,
        add_leaf_bones=False,
        apply_unit_scale=True,
    )

def add_cube():
    bpy.ops.mesh.primitive_cube_add(size=2)
    obj = bpy.context.object
    obj.name = "CONTROL_CUBE"
    obj.data.name = "CONTROL_CUBE_MESH"
    return obj

def add_two_bone_armature(mesh_obj):
    arm_data = bpy.data.armatures.new("CONTROL_ARM_DATA")
    arm = bpy.data.objects.new("CONTROL_ARM", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    b1 = arm_data.edit_bones.new("BONE_001")
    b1.head = (0, 0, -1)
    b1.tail = (0, 0, 0)
    b2 = arm_data.edit_bones.new("BONE_002")
    b2.head = (0, 0, 0)
    b2.tail = (0, 0, 1)
    b2.parent = b1
    b2.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")
    mod = mesh_obj.modifiers.new("ARMATURE", "ARMATURE")
    mod.object = arm
    return arm

def add_three_materials(obj):
    mats = []
    for name, rgba in (
        ("CONTROL_MAT_A", (1.0, 0.2, 0.2, 1.0)),
        ("CONTROL_MAT_B", (0.2, 1.0, 0.2, 1.0)),
        ("CONTROL_MAT_C", (0.2, 0.2, 1.0, 1.0)),
    ):
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = rgba
        obj.data.materials.append(mat)
        mats.append(mat)
    return mats

clear_scene()
obj = add_cube()
add_three_materials(obj)
for i, poly in enumerate(obj.data.polygons):
    poly.material_index = i % 3
save_model("CSMC_C051_MAT3_ALLUSED")

clear_scene()
obj = add_cube()
add_three_materials(obj)
for poly in obj.data.polygons:
    poly.material_index = 0
save_model("CSMC_C051_MAT3_ONEUSED")

clear_scene()
for idx, x in enumerate((-3.0, 0.0, 3.0), start=1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x, 0, 0))
    o = bpy.context.object
    o.name = f"CONTROL_CUBE_{idx:03d}"
    o.data.name = f"CONTROL_CUBE_MESH_{idx:03d}"
save_model("CSMC_C051_THREE_CUBES")

clear_scene()
obj = add_cube()
while obj.data.uv_layers:
    obj.data.uv_layers.remove(obj.data.uv_layers[0])
save_model("CSMC_C051_UV_OFF")

clear_scene()
obj = add_cube()
while obj.data.uv_layers:
    obj.data.uv_layers.remove(obj.data.uv_layers[0])
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project()
bpy.ops.object.mode_set(mode="OBJECT")
if obj.data.uv_layers:
    obj.data.uv_layers.active.name = "CONTROL_UV"
save_model("CSMC_C051_UV_ON")

def make_weight_pair(file_stem, w1, w2):
    clear_scene()
    obj = add_cube()
    add_two_bone_armature(obj)
    g1 = obj.vertex_groups.new(name="BONE_001")
    g2 = obj.vertex_groups.new(name="BONE_002")
    verts = [v.index for v in obj.data.vertices]
    g1.add(verts, w1, "REPLACE")
    g2.add(verts, w2, "REPLACE")
    save_model(file_stem)

make_weight_pair("CSMC_C051_W50_50", 0.5, 0.5)
make_weight_pair("CSMC_C051_W25_75", 0.25, 0.75)

print("C-051 next-control Blender source fixtures created in:", OUT)
