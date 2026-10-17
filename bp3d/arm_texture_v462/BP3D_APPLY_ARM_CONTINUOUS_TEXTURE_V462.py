import bpy
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent if "__file__" in globals() else Path(bpy.path.abspath("//"))
SRC="大学用女性data　胸小.body"; NAME="BP3D_ARM_TEXTURE_PREVIEW_V462"
s=bpy.data.objects.get(SRC) or bpy.context.object
if not s or s.type!="MESH": raise RuntimeError("body mesh not found")
o=bpy.data.objects.get(NAME)
if o: bpy.data.objects.remove(o,do_unlink=True)
o=s.copy();o.data=s.data.copy();o.name=NAME;(s.users_collection[0] if s.users_collection else bpy.context.scene.collection).objects.link(o)
mat=bpy.data.materials.get("BP3D_ARM_TEXTURE_V462") or bpy.data.materials.new("BP3D_ARM_TEXTURE_V462");mat.use_nodes=True;n=mat.node_tree;n.nodes.clear();out=n.nodes.new("ShaderNodeOutputMaterial");bs=n.nodes.new("ShaderNodeBsdfPrincipled")
tex=n.nodes.new("ShaderNodeTexImage");tex.name="BP3D_COLOR_WITH_BLACK_BOUNDARY";tex.image=bpy.data.images.load(str(BASE/"ARM_MUSCLE_COMPOSITE_BODY_TEXTURE_V462_4K.png"),check_existing=True)
mask=n.nodes.new("ShaderNodeTexImage");mask.name="BP3D_BLACK_BOUNDARY_MASK";mask.image=bpy.data.images.load(str(BASE/"ARM_MUSCLE_BOUNDARY_BLACK_MASK_V462_4K.png"),check_existing=True);mask.image.colorspace_settings.name="Non-Color";mask.hide=True
h=n.nodes.new("ShaderNodeTexImage");h.image=bpy.data.images.load(str(BASE/"ARM_MUSCLE_RELIEF_HEIGHT_V461_4K.png"),check_existing=True);h.image.colorspace_settings.name="Non-Color";b=n.nodes.new("ShaderNodeBump");b.inputs["Strength"].default_value=.30;b.inputs["Distance"].default_value=.004
n.links.new(tex.outputs["Color"],bs.inputs["Base Color"]);n.links.new(h.outputs["Color"],b.inputs["Height"]);n.links.new(b.outputs["Normal"],bs.inputs["Normal"]);n.links.new(bs.outputs["BSDF"],out.inputs["Surface"]);o.data.materials.clear();o.data.materials.append(mat)
sub=o.modifiers.new("BP3D_V462_VIRTUAL_SUBDIV","SUBSURF");sub.levels=2;sub.render_levels=2;sub.show_viewport=False
print("BP3D v4.6.2 continuous arm texture + black continuous-field boundaries applied to derived duplicate",o.name)
