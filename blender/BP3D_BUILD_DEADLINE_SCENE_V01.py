import bpy, os, json
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else bpy.path.abspath("//")
ARM=os.path.join(ROOT,'arm'); FOOT=os.path.join(ROOT,'foot_lowerleg'); BODY=os.path.join(ROOT,'thigh_pelvis_torso')

ROOT_NAME='BP3D_GRADUATION_DEADLINE_BUILD_V01'
old=bpy.data.collections.get(ROOT_NAME)
if old:
    for o in list(old.all_objects): bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.collections.remove(old)
root=bpy.data.collections.new(ROOT_NAME); bpy.context.scene.collection.children.link(root)

def child(name):
    c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
    for parent in list(bpy.data.collections):
        if parent!=root and c.name in parent.children: parent.children.unlink(c)
    if c.name not in root.children: root.children.link(c)
    return c
COL_ARM=child('BP3D_DEADLINE_ARM_V01'); COL_FOOT=child('BP3D_DEADLINE_FOOT_LOWERLEG_V01'); COL_TORSO=child('BP3D_DEADLINE_THIGH_PELVIS_TORSO_V01'); COL_BOUND=child('BP3D_DEADLINE_BOUNDARIES_V01')

def import_obj(path, col):
    before=set(bpy.data.objects)
    try: bpy.ops.wm.obj_import(filepath=path)
    except Exception: bpy.ops.import_scene.obj(filepath=path)
    new=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
    return new

def principled_texture(name,color_path,relief_path=None,bump_strength=.2,bump_distance=.01):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear(); out=nt.nodes.new('ShaderNodeOutputMaterial'); bs=nt.nodes.new('ShaderNodeBsdfPrincipled')
    tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=bpy.data.images.load(color_path,check_existing=True); tex.interpolation='Linear'
    nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if relief_path:
        ht=nt.nodes.new('ShaderNodeTexImage'); ht.image=bpy.data.images.load(relief_path,check_existing=True); ht.image.colorspace_settings.name='Non-Color'
        bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=bump_strength; bump.inputs['Distance'].default_value=bump_distance
        nt.links.new(ht.outputs['Color'],bump.inputs['Height']); nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    if 'Roughness' in bs.inputs: bs.inputs['Roughness'].default_value=.58
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface']); return m

arm_objs=import_obj(os.path.join(ARM,'BP3D_ARM_ONLY_V462_V45.obj'),COL_ARM)
arm_mat=principled_texture('BP3D_ARM_V462_DEADLINE',os.path.join(ARM,'ARM_MUSCLE_COMPOSITE_BODY_TEXTURE_V462_4K.png'),os.path.join(ARM,'ARM_MUSCLE_RELIEF_HEIGHT_V461_4K.png'),.30,.004)
for o in arm_objs:
    o.name='BP3D_ARM_ONLY_V462_V45'; o.data.materials.clear(); o.data.materials.append(arm_mat)
    o['bp3d_role']='DERIVED_VISUAL_OVERLAY'; o['bp3d_authority']='Final-v3 + V45'; o['bp3d_face_count']=2004; o['bp3d_semantic_mutation']=False

foot_objs=import_obj(os.path.join(FOOT,'BP3D_FOOT_LOWERLEG_OVERLAY_V011.obj'),COL_FOOT)
foot_mat=principled_texture('BP3D_FOOT_LOWERLEG_V011_DEADLINE',os.path.join(FOOT,'FOOT_LOWERLEG_CONTINUOUS_COLOR_V011_4K.png'),os.path.join(FOOT,'FOOT_LOWERLEG_RELIEF_HEIGHT_V011_4K.png'),.18,.02)
for o in foot_objs:
    o.name='BP3D_FOOT_LOWERLEG_V011'; o.data.materials.clear(); o.data.materials.append(foot_mat); o['bp3d_role']='DERIVED_VISUAL_OVERLAY'; o['bp3d_semantic_mutation']=False

MAP=json.load(open(os.path.join(BODY,'DISPLAY_LABEL_MAP_V01.json'),encoding='utf-8'))['labels']
BOUND=json.load(open(os.path.join(BODY,'BOUNDARY_SEGMENTS_V01.json'),encoding='utf-8'))['segments']
def body_mat(label):
    name='BP3D_BODYMAT_'+label; m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
    h=MAP[label]['color'].lstrip('#'); rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]; alpha=.82 if MAP[label]['context_style'] else 1.0
    m.diffuse_color=(*rgb,alpha); bs=m.node_tree.nodes.get('Principled BSDF')
    if bs: bs.inputs['Base Color'].default_value=(*rgb,1); bs.inputs['Roughness'].default_value=.62; bs.inputs['Alpha'].default_value=alpha
    try:
        if alpha<1: m.surface_render_method='DITHERED'
    except Exception: pass
    return m
comp=os.path.join(BODY,'components')
for fn in sorted(os.listdir(comp)):
    if not fn.lower().endswith('.obj'): continue
    label=fn.split('.L.')[0].split('.R.')[0]
    if label=='DELTOID': continue
    for o in import_obj(os.path.join(comp,fn),COL_TORSO):
        o['bp3d_label']=label; o['bp3d_group']=MAP[label]['group']; o['bp3d_mean_confidence']=MAP[label]['mean_confidence']; o['bp3d_display_only']=True
        o.data.materials.clear(); o.data.materials.append(body_mat(label))

curve_data=bpy.data.curves.new('BP3D_DEADLINE_INTERNAL_BOUNDARIES','CURVE'); curve_data.dimensions='3D'; curve_data.bevel_depth=.00085; curve_data.bevel_resolution=2
for s in BOUND:
    sp=curve_data.splines.new('POLY'); sp.points.add(1); sp.points[0].co=(*s['p0'],1); sp.points[1].co=(*s['p1'],1)
curve_obj=bpy.data.objects.new('BP3D_DEADLINE_INTERNAL_BOUNDARIES',curve_data); COL_BOUND.objects.link(curve_obj)
black=bpy.data.materials.get('BP3D_DEADLINE_BLACK') or bpy.data.materials.new('BP3D_DEADLINE_BLACK'); black.diffuse_color=(.005,.005,.005,1); curve_data.materials.append(black)
curve_obj['bp3d_display_only']=True

def set_mode(mode='FULL'):
    mode=mode.upper()
    COL_ARM.hide_viewport=mode not in {'FULL','ARM'}; COL_ARM.hide_render=COL_ARM.hide_viewport
    COL_FOOT.hide_viewport=mode not in {'FULL','LEG'}; COL_FOOT.hide_render=COL_FOOT.hide_viewport
    COL_TORSO.hide_viewport=mode not in {'FULL','TORSO'}; COL_TORSO.hide_render=COL_TORSO.hide_viewport
    COL_BOUND.hide_viewport=mode not in {'FULL','TORSO'}; COL_BOUND.hide_render=COL_BOUND.hide_viewport
    bpy.context.scene['bp3d_deadline_mode']=mode
set_mode('FULL')

for name in ['大学用女性data　胸小.body']:
    s=bpy.data.objects.get(name)
    if s:
        s.hide_viewport=True; s.hide_render=True; s['bp3d_hidden_by_deadline_build']=True

bpy.context.scene['bp3d_deadline_build']='V01_20260903'; bpy.context.scene['bp3d_semantic_authority']='Final-v3 + V45'; bpy.context.scene['bp3d_canonical_face_change']=0
print('BP3D Deadline Build V01 ready:',len(COL_ARM.objects),'arm objects,',len(COL_FOOT.objects),'foot/lowerleg objects,',len(COL_TORSO.objects),'thigh/pelvis/torso objects')
print("Modes: run set_mode('FULL'), set_mode('ARM'), set_mode('LEG'), set_mode('TORSO') in this Text Editor session.")
