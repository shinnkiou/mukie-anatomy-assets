import bpy, os, json, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
root_arg=os.environ.get('BP3D_DEADLINE_ROOT','').strip()
ROOT=Path(root_arg).resolve() if root_arg else HERE.parent
OUT=ROOT/'qa_torso_output'; OUT.mkdir(exist_ok=True)
report={'schema':'bp3d.torso_isolated.headless_qa.v01','semantic_authority':['Final-v3','Non-Blender v4','Non-Blender v4.1','Non-Blender v4.2','V45'],'anatomical_front':'NEGATIVE_Y','checks':{},'renders':[],'status':'RUNNING','guards':{'MASTER_write':0,'R7_write':0,'Production14':'HOLD','Production13':'FORBIDDEN','canonical_face_change':0,'external_author_pixel_use':0}}
try:
    for script in ['BP3D_BUILD_DEADLINE_SCENE_V02.py','BP3D_TORSO_ISOLATION_GUARD_V01.py']:
        p=ROOT/'blender'/script
        ns={'__file__':str(p),'__name__':'__bp3d_torso_qa__'}
        exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),ns,ns)
    scene=bpy.context.scene
    body=bpy.data.collections.get('BP3D_DEADLINE_THIGH_PELVIS_TORSO_V02')
    cams=bpy.data.collections.get('BP3D_DEADLINE_CAMERAS_V02')
    bound=bpy.data.collections.get('BP3D_DEADLINE_BOUNDARIES_V02')
    if not body or not cams: raise AssertionError('required V02 collections missing')
    allowed={'TRAPEZIUS_UPPER','PECTORALIS_MAJOR','LATISSIMUS_DORSI','RECTUS_ABDOMINIS','OBLIQUE','THORACOLUMBAR_FASCIA_CONTEXT','PELVIS_FRONT_CONTEXT','GLUTEUS_MAXIMUS','GLUTEUS_MEDIUS'}
    visible=[o for o in body.all_objects if o.type=='MESH' and not o.hide_render]
    violations=[{'name':o.name,'label':o.get('bp3d_label')} for o in visible if o.get('bp3d_label') not in allowed]
    report['visible_meshes']=[{'name':o.name,'label':o.get('bp3d_label'),'faces':len(o.data.polygons)} for o in visible]
    report['checks']['torso_allowlist_only']={'violations':violations,'pass':not violations}
    report['checks']['mixed_boundary_hidden']={'pass':bound is None or bound.hide_render}
    other=[]
    for cname in ['BP3D_DEADLINE_ARM_V02','BP3D_DEADLINE_FOOT_LOWERLEG_V02','BP3D_DEADLINE_NEUTRAL_BASE_V02']:
        c=bpy.data.collections.get(cname)
        if c and not c.hide_render: other.append(cname)
    report['checks']['non_torso_collections_hidden']={'visible':other,'pass':not other}
    report['checks']['canonical_guards']={'pass':scene.get('bp3d_canonical_face_change')==0 and scene.get('bp3d_external_author_pixel_use')==0 and scene.get('bp3d_anatomical_front')=='NEGATIVE_Y'}
    try: scene.render.engine='BLENDER_EEVEE_NEXT'
    except Exception: scene.render.engine='BLENDER_WORKBENCH'
    scene.render.resolution_x=640;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    for cam in sorted([o for o in cams.objects if o.type=='CAMERA'],key=lambda o:o.name):
        scene.camera=cam; fn=OUT/(cam.name.replace('BP3D_CAM_','TORSO_')+'.png'); scene.render.filepath=str(fn); bpy.ops.render.render(write_still=True); report['renders'].append(str(fn))
    report['checks']['eight_views_rendered']={'count':len(report['renders']),'pass':len(report['renders'])==8}
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BP3D_TORSO_ISOLATED_GUARDED_V01_QA.blend'))
    report['status']='PASS' if all(v.get('pass',False) for v in report['checks'].values()) else 'FAIL'
except Exception as e:
    report['status']='ERROR';report['error']=str(e);report['traceback']=traceback.format_exc()
finally:
    (OUT/'BP3D_TORSO_ISOLATED_QA_RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if report['status']!='PASS': raise SystemExit(2)
