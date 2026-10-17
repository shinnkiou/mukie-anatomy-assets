import bpy, os, json, math, traceback
from pathlib import Path
from mathutils import Vector

SCHEMA='bp3d.deadline.capture.h1h5.v01'
ROOT_NAME='BP3D_GRADUATION_DEADLINE_BUILD_V02'
CAM_COL='BP3D_H1H5_CAMERAS_V01'
HERE=Path(__file__).resolve().parent
OUT=Path(os.environ.get('BP3D_CAPTURE_OUTPUT', str(HERE/'capture_output'))).resolve()
OUT.mkdir(parents=True, exist_ok=True)

# This geometry reproduces the project's historical 26-view pattern directly:
# H1 lower pole (1), H2 lower ring (8), H3 middle ring (8), H4 upper ring (8), H5 upper pole (1).
# No guessed numeric H-elevation angles are introduced.
AZ=[0,45,90,135,180,225,270,315]
VIEW_SPEC=[]
VIEW_SPEC.append(('H1',0,'lower_pole'))
for a in AZ: VIEW_SPEC.append(('H2',a,'lower_ring'))
for a in AZ: VIEW_SPEC.append(('H3',a,'middle_ring'))
for a in AZ: VIEW_SPEC.append(('H4',a,'upper_ring'))
VIEW_SPEC.append(('H5',0,'upper_pole'))

report={'schema':SCHEMA,'status':'RUNNING','view_count_expected':26,'views':[],'renders':[],'source_mutation':0,'semantic_mutation':0}
try:
    root=bpy.data.collections.get(ROOT_NAME)
    if not root:
        raise RuntimeError('Deadline Build V02 is not assembled. Run BP3D_BUILD_DEADLINE_SCENE_V02.py first.')
    base_col=bpy.data.collections.get('BP3D_DEADLINE_NEUTRAL_BASE_V02')
    if not base_col: raise RuntimeError('neutral base collection missing')
    base=next((o for o in base_col.objects if o.type=='MESH'),None)
    if not base: raise RuntimeError('neutral base mesh missing')
    coords=[base.matrix_world@v.co for v in base.data.vertices]
    xs=[p.x for p in coords]; ys=[p.y for p in coords]; zs=[p.z for p in coords]
    center=Vector(((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,(min(zs)+max(zs))/2))
    span=max(max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs))
    radius=span*2.2
    ortho=span*1.18
    old=bpy.data.collections.get(CAM_COL)
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(old)
    cams=bpy.data.collections.new(CAM_COL); root.children.link(cams)
    def position(kind,az):
        a=math.radians(az)
        if kind=='lower_pole': return center+Vector((0,0,-radius))
        if kind=='upper_pole': return center+Vector((0,0, radius))
        if kind=='middle_ring': hr=radius; z=0.0
        elif kind=='lower_ring': hr=radius/math.sqrt(2.0); z=-radius/math.sqrt(2.0)
        elif kind=='upper_ring': hr=radius/math.sqrt(2.0); z= radius/math.sqrt(2.0)
        else: raise ValueError(kind)
        # anatomical front=NEGATIVE_Y, so azimuth 0 is -Y/front.
        return center+Vector((hr*math.sin(a),-hr*math.cos(a),z))
    for h,az,kind in VIEW_SPEC:
        name=f'BP3D_{h}_{az:03d}'
        d=bpy.data.cameras.new(name); d.type='ORTHO'; d.ortho_scale=ortho
        o=bpy.data.objects.new(name,d); cams.objects.link(o); o.location=position(kind,az)
        o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
        o['bp3d_h_level']=h;o['bp3d_azimuth_deg']=az;o['bp3d_height_geometry']=kind;o['bp3d_front_axis']='NEGATIVE_Y'
        report['views'].append({'name':name,'h':h,'azimuth_deg':az,'height_geometry':kind,'location':list(o.location)})
    if len(report['views'])!=26: raise AssertionError('26-view camera count failed')
    report['view_count_actual']=26

    # Capture modes can be selected without changing the source. Default FULL only.
    modes=[m.strip().upper() for m in os.environ.get('BP3D_CAPTURE_MODES','FULL').split(',') if m.strip()]
    allowed={'FULL','ARM','ARM_ISOLATED','LEG','LEG_ISOLATED','TORSO','TORSO_ISOLATED'}
    bad=[m for m in modes if m not in allowed]
    if bad: raise RuntimeError('invalid BP3D_CAPTURE_MODES: '+','.join(bad))
    report['modes']=modes
    scene=bpy.context.scene
    scene.render.resolution_x=int(os.environ.get('BP3D_CAPTURE_WIDTH','1200'))
    scene.render.resolution_y=int(os.environ.get('BP3D_CAPTURE_HEIGHT','1200'))
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=True
    try: scene.render.engine='BLENDER_EEVEE_NEXT'
    except Exception: scene.render.engine='BLENDER_WORKBENCH'
    # set_mode comes from assembler if run in same namespace; recreate non-destructively if absent.
    def local_set_mode(mode):
        isolated=mode.endswith('_ISOLATED'); base_visible=(mode=='FULL' or not isolated)
        mapping={
            'BP3D_DEADLINE_NEUTRAL_BASE_V02':base_visible,
            'BP3D_DEADLINE_ARM_V02':mode in {'FULL','ARM','ARM_ISOLATED'},
            'BP3D_DEADLINE_FOOT_LOWERLEG_V02':mode in {'FULL','LEG','LEG_ISOLATED'},
            'BP3D_DEADLINE_THIGH_PELVIS_TORSO_V02':mode in {'FULL','TORSO','TORSO_ISOLATED'},
            'BP3D_DEADLINE_BOUNDARIES_V02':mode in {'FULL','TORSO','TORSO_ISOLATED'},
        }
        for n,vis in mapping.items():
            c=bpy.data.collections.get(n)
            if c: c.hide_viewport=not vis;c.hide_render=not vis
        scene['bp3d_deadline_mode']=mode
    for mode in modes:
        local_set_mode(mode)
        md=OUT/mode; md.mkdir(exist_ok=True)
        for h,az,kind in VIEW_SPEC:
            cam=bpy.data.objects.get(f'BP3D_{h}_{az:03d}')
            scene.camera=cam
            fn=md/f'{h}_{az:03d}.png';scene.render.filepath=str(fn)
            bpy.ops.render.render(write_still=True)
            report['renders'].append({'mode':mode,'view':f'{h}_{az:03d}','file':str(fn)})
    report['status']='PASS'
except Exception as e:
    report['status']='ERROR';report['error']=str(e);report['traceback']=traceback.format_exc()
finally:
    (OUT/'BP3D_H1H5_CAPTURE_RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if report['status']!='PASS': raise SystemExit(2)
