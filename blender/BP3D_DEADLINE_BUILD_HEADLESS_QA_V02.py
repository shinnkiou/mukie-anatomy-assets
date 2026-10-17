import bpy, os, json, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
root_arg=os.environ.get('BP3D_DEADLINE_ROOT','').strip()
if root_arg:
    ROOT=Path(root_arg).resolve()
else:
    candidates=[HERE, HERE.parent, HERE/'BP3D_GRADUATION_DEADLINE_BUILD_V02_20260903', HERE.parent/'BP3D_GRADUATION_DEADLINE_BUILD_V02_20260903']
    ROOT=next((p for p in candidates if (p/'blender'/'BP3D_BUILD_DEADLINE_SCENE_V02.py').exists()),None)
if ROOT is None or not (ROOT/'blender'/'BP3D_BUILD_DEADLINE_SCENE_V02.py').exists():
    raise RuntimeError('BP3D Deadline Build V02 package root not found. Set BP3D_DEADLINE_ROOT to extracted package folder.')
OUT=ROOT/'qa_output'; OUT.mkdir(exist_ok=True)
report={'schema':'bp3d.deadline_build.headless_qa.v02','package_root':str(ROOT),'checks':{},'renders':[],'status':'RUNNING'}
try:
    ns={'__file__':str(ROOT/'blender'/'BP3D_BUILD_DEADLINE_SCENE_V02.py'),'__name__':'__bp3d_deadline_assembler__'}
    code=(ROOT/'blender'/'BP3D_BUILD_DEADLINE_SCENE_V02.py').read_text(encoding='utf-8')
    exec(compile(code,str(ROOT/'blender'/'BP3D_BUILD_DEADLINE_SCENE_V02.py'),'exec'),ns,ns)
    def col(name):
        c=bpy.data.collections.get(name)
        if not c: raise AssertionError('missing collection '+name)
        return c
    cbase=col('BP3D_DEADLINE_NEUTRAL_BASE_V02');carm=col('BP3D_DEADLINE_ARM_V02');cfoot=col('BP3D_DEADLINE_FOOT_LOWERLEG_V02');cbody=col('BP3D_DEADLINE_THIGH_PELVIS_TORSO_V02');ccam=col('BP3D_DEADLINE_CAMERAS_V02')
    def mesh_faces(c): return sum(len(o.data.polygons) for o in c.objects if o.type=='MESH')
    counts={'neutral_base_faces':mesh_faces(cbase),'arm_faces':mesh_faces(carm),'foot_lowerleg_faces':mesh_faces(cfoot),'body_faces':mesh_faces(cbody),'camera_count':sum(1 for o in ccam.objects if o.type=='CAMERA')}
    report['counts']=counts
    expected={'neutral_base_faces':13378,'arm_faces':2004,'foot_lowerleg_faces':2378,'body_faces':1928,'camera_count':8}
    report['checks']['face_and_camera_counts']={'expected':expected,'actual':counts,'pass':counts==expected}
    missing=[]; images=[]
    for m in bpy.data.materials:
        if not m.use_nodes or not m.node_tree: continue
        for n in m.node_tree.nodes:
            if n.bl_idname=='ShaderNodeTexImage':
                images.append({'material':m.name,'node':n.name,'image':n.image.name if n.image else None})
                if n.image is None: missing.append(m.name+':'+n.name)
    report['images']=images;report['checks']['texture_images_loaded']={'missing':missing,'pass':not missing}
    offset_fail=[];offset_count=0
    base_obj=next((o for o in cbase.objects if o.type=='MESH'),None)
    for c in [carm,cfoot,cbody]:
        for o in c.objects:
            if o.type!='MESH': continue
            mods=[m for m in o.modifiers if m.type=='SHRINKWRAP' and m.name=='BP3D_DISPLAY_OFFSET']
            if not mods or mods[0].target!=base_obj or abs(mods[0].offset-0.0008)>1e-7: offset_fail.append(o.name)
            else: offset_count+=1
    report['checks']['display_offsets']={'checked':offset_count+len(offset_fail),'failed_objects':offset_fail,'pass':not offset_fail}
    scene=bpy.context.scene
    try: scene.render.engine='BLENDER_EEVEE_NEXT';engine='BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine='BLENDER_WORKBENCH';engine='BLENDER_WORKBENCH'
    report['render_engine']=engine
    scene.render.resolution_x=640;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.world.color=(0.92,0.92,0.92)
    if engine!='BLENDER_WORKBENCH':
        for nm,loc,energy,size in [('BP3D_QA_KEY',(3,-4,4),1200,4),('BP3D_QA_FILL',(-3,-1,2),700,3),('BP3D_QA_BACK',(0,4,3),800,3)]:
            ld=bpy.data.lights.new(nm,'AREA');ld.energy=energy;ld.shape='DISK';ld.size=size;lo=bpy.data.objects.new(nm,ld);bpy.context.scene.collection.objects.link(lo);lo.location=loc
            import mathutils;target=mathutils.Vector((0,0,1));lo.rotation_euler=(target-lo.location).to_track_quat('-Z','Y').to_euler()
    cams=sorted([o for o in ccam.objects if o.type=='CAMERA'], key=lambda o:o.name)
    for cam in cams:
        scene.camera=cam; fn=OUT/(cam.name.replace('BP3D_CAM_','')+'.png'); scene.render.filepath=str(fn); bpy.ops.render.render(write_still=True); report['renders'].append(str(fn))
    blend_out=OUT/'BP3D_GRADUATION_DEADLINE_BUILD_V02_QA.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend_out));report['blend_output']=str(blend_out)
    report['status']='PASS' if all(v.get('pass',False) for v in report['checks'].values()) else 'FAIL'
except Exception as e:
    report['status']='ERROR';report['error']=str(e);report['traceback']=traceback.format_exc()
finally:
    (OUT/'BP3D_DEADLINE_BUILD_QA_RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if report['status']!='PASS': raise SystemExit(2)
