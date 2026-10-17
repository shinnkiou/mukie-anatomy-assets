import bpy, os, json, math
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else bpy.path.abspath("//")
BASE=os.path.join(ROOT,'base'); ARM=os.path.join(ROOT,'arm'); FOOT=os.path.join(ROOT,'foot_lowerleg'); BODY=os.path.join(ROOT,'thigh_pelvis_torso')
ROOT_NAME='BP3D_GRADUATION_DEADLINE_BUILD_V02'
old=bpy.data.collections.get(ROOT_NAME)
if old:
    for o in list(old.all_objects): bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.collections.remove(old)
root=bpy.data.collections.new(ROOT_NAME); bpy.context.scene.collection.children.link(root)
def child(name):
    c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in root.children: root.children.link(c)
    return c
COL_BASE=child('BP3D_DEADLINE_NEUTRAL_BASE_V02'); COL_ARM=child('BP3D_DEADLINE_ARM_V02'); COL_FOOT=child('BP3D_DEADLINE_FOOT_LOWERLEG_V02'); COL_BODY=child('BP3D_DEADLINE_THIGH_PELVIS_TORSO_V02'); COL_BOUND=child('BP3D_DEADLINE_BOUNDARIES_V02'); COL_CAM=child('BP3D_DEADLINE_CAMERAS_V02')
def import_obj(path,col):
    before=set(bpy.data.objects)
    try: bpy.ops.wm.obj_import(filepath=path)
    except Exception: bpy.ops.import_scene.obj(filepath=path)
    new=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
    return new
def simple_mat(name,rgb,rough=.7):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
    bs=m.node_tree.nodes.get('Principled BSDF')
    if bs: bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=rough
    return m
def texmat(name,color_path,relief_path=None,strength=.2,distance=.01):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfPrincipled')
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(color_path,check_existing=True);tex.interpolation='Linear';nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if relief_path:
        ht=nt.nodes.new('ShaderNodeTexImage');ht.image=bpy.data.images.load(relief_path,check_existing=True);ht.image.colorspace_settings.name='Non-Color';b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=distance;nt.links.new(ht.outputs['Color'],b.inputs['Height']);nt.links.new(b.outputs['Normal'],bs.inputs['Normal'])
    if 'Roughness' in bs.inputs: bs.inputs['Roughness'].default_value=.58
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface']);return m
base_objs=import_obj(os.path.join(BASE,'BP3D_CLEAN_BODY_NEUTRAL.obj'),COL_BASE);base=base_objs[0]
base.name='BP3D_CLEAN_BODY_NEUTRAL_V02';base.data.materials.clear();base.data.materials.append(simple_mat('BP3D_NEUTRAL_BASE_MAT',(0.72,0.72,0.72),.78));base['bp3d_role']='NEUTRAL_GEOGRAPHIC_BASE';base['bp3d_semantic_authority']='NONE';base['bp3d_canonical_mutation']=False
def offset_overlay(o,offset=.0008):
    sw=o.modifiers.new('BP3D_DISPLAY_OFFSET','SHRINKWRAP');sw.target=base;sw.wrap_method='NEAREST_SURFACEPOINT';sw.wrap_mode='ON_SURFACE';sw.offset=offset
    o['bp3d_display_offset_m']=offset
arm=import_obj(os.path.join(ARM,'BP3D_ARM_ONLY_V462_V45.obj'),COL_ARM);amat=texmat('BP3D_ARM_V462_DEADLINE',os.path.join(ARM,'ARM_MUSCLE_COMPOSITE_BODY_TEXTURE_V462_4K.png'),os.path.join(ARM,'ARM_MUSCLE_RELIEF_HEIGHT_V461_4K.png'),.30,.004)
for o in arm:o.name='BP3D_ARM_ONLY_V462_V45';o.data.materials.clear();o.data.materials.append(amat);offset_overlay(o);o['bp3d_role']='DERIVED_VISUAL_OVERLAY';o['bp3d_face_count']=2004
foot=import_obj(os.path.join(FOOT,'BP3D_FOOT_LOWERLEG_OVERLAY_V011.obj'),COL_FOOT);fmat=texmat('BP3D_FOOT_LOWERLEG_V011_DEADLINE',os.path.join(FOOT,'FOOT_LOWERLEG_CONTINUOUS_COLOR_V011_4K.png'),os.path.join(FOOT,'FOOT_LOWERLEG_RELIEF_HEIGHT_V011_4K.png'),.18,.02)
for o in foot:o.name='BP3D_FOOT_LOWERLEG_V011';o.data.materials.clear();o.data.materials.append(fmat);offset_overlay(o);o['bp3d_role']='DERIVED_VISUAL_OVERLAY'
MAP=json.load(open(os.path.join(BODY,'DISPLAY_LABEL_MAP_V01.json'),encoding='utf-8'))['labels'];BOUND=json.load(open(os.path.join(BODY,'BOUNDARY_SEGMENTS_V01.json'),encoding='utf-8'))['segments']
def bmat(label):
    h=MAP[label]['color'].lstrip('#');rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];m=simple_mat('BP3D_BODYMAT_'+label,rgb,.62);alpha=.82 if MAP[label]['context_style'] else 1.0;m.diffuse_color=(*rgb,alpha);bs=m.node_tree.nodes.get('Principled BSDF')
    if bs:bs.inputs['Alpha'].default_value=alpha
    try:
        if alpha<1:m.surface_render_method='DITHERED'
    except Exception:pass
    return m
comp=os.path.join(BODY,'components')
for fn in sorted(os.listdir(comp)):
    if not fn.lower().endswith('.obj'):continue
    label=fn.split('.L.')[0].split('.R.')[0]
    if label=='DELTOID':continue
    for o in import_obj(os.path.join(comp,fn),COL_BODY):o.data.materials.clear();o.data.materials.append(bmat(label));offset_overlay(o);o['bp3d_label']=label;o['bp3d_display_only']=True
cd=bpy.data.curves.new('BP3D_DEADLINE_INTERNAL_BOUNDARIES_V02','CURVE');cd.dimensions='3D';cd.bevel_depth=.00085;cd.bevel_resolution=2
for s in BOUND:
    sp=cd.splines.new('POLY');sp.points.add(1);sp.points[0].co=(*s['p0'],1);sp.points[1].co=(*s['p1'],1)
co=bpy.data.objects.new('BP3D_DEADLINE_INTERNAL_BOUNDARIES_V02',cd);COL_BOUND.objects.link(co);cd.materials.append(simple_mat('BP3D_DEADLINE_BLACK',(0.005,0.005,0.005),.8))
coords=[base.matrix_world@v.co for v in base.data.vertices];xs=[p.x for p in coords];ys=[p.y for p in coords];zs=[p.z for p in coords];center=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,(min(zs)+max(zs))/2);span=max(max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs));dist=span*2.2
def add_cam(name,az):
    a=math.radians(az);loc=(center[0]+dist*math.sin(a),center[1]-dist*math.cos(a),center[2]);data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=span*1.18;o=bpy.data.objects.new(name,data);COL_CAM.objects.link(o);o.location=loc
    import mathutils;direction=mathutils.Vector(center)-o.location;o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();return o
for name,az in [('FRONT',0),('FRONT_OBLIQUE_30_R',30),('RIGHT',90),('BACK_OBLIQUE_30_R',150),('BACK',180),('BACK_OBLIQUE_30_L',210),('LEFT',270),('FRONT_OBLIQUE_30_L',330)]:add_cam('BP3D_CAM_'+name,az)
def set_mode(mode='FULL'):
    mode=mode.upper();isolated=mode.endswith('_ISOLATED');base_visible=(mode=='FULL' or not isolated)
    COL_BASE.hide_viewport=not base_visible;COL_BASE.hide_render=COL_BASE.hide_viewport
    COL_ARM.hide_viewport=mode not in {'FULL','ARM','ARM_ISOLATED'};COL_ARM.hide_render=COL_ARM.hide_viewport
    COL_FOOT.hide_viewport=mode not in {'FULL','LEG','LEG_ISOLATED'};COL_FOOT.hide_render=COL_FOOT.hide_viewport
    COL_BODY.hide_viewport=mode not in {'FULL','TORSO','TORSO_ISOLATED'};COL_BODY.hide_render=COL_BODY.hide_viewport
    COL_BOUND.hide_viewport=mode not in {'FULL','TORSO','TORSO_ISOLATED'};COL_BOUND.hide_render=COL_BOUND.hide_viewport
    bpy.context.scene['bp3d_deadline_mode']=mode
set_mode('FULL')
s=bpy.data.objects.get('大学用女性data　胸小.body')
if s:s.hide_viewport=True;s.hide_render=True;s['bp3d_hidden_by_deadline_build']=True
bpy.context.scene['bp3d_deadline_build']='V02_20260903';bpy.context.scene['bp3d_semantic_authority']='Final-v3 + V45';bpy.context.scene['bp3d_canonical_face_change']=0
print('BP3D Deadline Build V02 ready. Modes: FULL / ARM / ARM_ISOLATED / LEG / LEG_ISOLATED / TORSO / TORSO_ISOLATED')
