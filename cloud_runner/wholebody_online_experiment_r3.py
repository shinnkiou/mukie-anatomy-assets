# -*- coding: utf-8 -*-
"""BP3D R3: public-safe refined segmentation after Run2 visual review."""
import bpy,sys,json,hashlib,traceback,colorsys
from pathlib import Path
from collections import Counter,defaultdict,deque
from array import array
from mathutils import Vector
MODES=('D3','E3','F3');SIZE=1024
N={1:'HEAD',2:'NECK_SCM_L',3:'NECK_SCM_R',4:'TRAPEZIUS_UPPER',5:'DELTOID_L',6:'DELTOID_R',7:'PECTORAL_L',8:'PECTORAL_R',9:'RECTUS_ABDOMINIS',10:'OBLIQUE_L',11:'OBLIQUE_R',12:'LATISSIMUS_L',13:'LATISSIMUS_R',14:'GLUTEAL_L',15:'GLUTEAL_R',16:'BICEPS_L',17:'BICEPS_R',18:'TRICEPS_L',19:'TRICEPS_R',20:'FOREARM_ANTERIOR_L',21:'FOREARM_ANTERIOR_R',22:'FOREARM_POSTERIOR_L',23:'FOREARM_POSTERIOR_R',24:'HAND_L',25:'HAND_R',26:'HIP_LATERAL_L',27:'HIP_LATERAL_R',28:'THIGH_ANTERIOR_L',29:'THIGH_ANTERIOR_R',30:'THIGH_MEDIAL_L',31:'THIGH_MEDIAL_R',32:'THIGH_POSTERIOR_L',33:'THIGH_POSTERIOR_R',34:'KNEE_L',35:'KNEE_R',36:'SHIN_L',37:'SHIN_R',38:'CALF_L',39:'CALF_R',40:'FOOT_L',41:'FOOT_R',42:'THORACOLUMBAR_FASCIA_CONTEXT',43:'PELVIS_FRONT_CONTEXT',101:'U1_SHOULDER_AXILLA',102:'U2_SCAPULAR_LAT',103:'U3_INGUINAL_HIP',104:'U4_KNEE_TRANSITION',105:'U5_WRIST_HAND_TRANSITION'}
REM={18:16,19:17,22:20,23:21,26:14,27:15,30:28,31:29,32:28,33:29,38:36,39:37,42:12,43:9}
def arg(k):
 a=sys.argv[sys.argv.index('--')+1:];return a[a.index(k)+1]
def js(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):
 h=hashlib.sha256();f=open(p,'rb')
 for b in iter(lambda:f.read(1048576),b''):h.update(b)
 f.close();return h.hexdigest()
def rgb(i):return (.94,.94,.94,1) if i>=100 else (*colorsys.hsv_to_rgb((i*.61803398875)%1,.68,.92),1)
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=c;m.use_nodes=True;t=m.node_tree;t.nodes.clear();o=t.nodes.new('ShaderNodeOutputMaterial');e=t.nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=c;t.links.new(e.outputs['Emission'],o.inputs['Surface']);return m
def comp(m):
 v2=[[] for _ in m.vertices]
 for p in m.polygons:
  for v in p.vertices:v2[v].append(p.index)
 seen=bytearray(len(m.polygons));out=[]
 for s in range(len(m.polygons)):
  if seen[s]:continue
  q=deque([s]);seen[s]=1;c=[]
  while q:
   f=q.popleft();c.append(f)
   for v in m.polygons[f].vertices:
    for n in v2[v]:
     if not seen[n]:seen[n]=1;q.append(n)
  out.append(c)
 return sorted(out,key=len,reverse=True)
def clean(src,ids):
 sm=src.data;m=bpy.data.meshes.new('BP3D_R3_CLEAN');m.from_pydata([v.co.copy() for v in sm.vertices],[],[list(sm.polygons[i].vertices) for i in ids]);m.update()
 if sm.uv_layers.active:
  su=sm.uv_layers.active;u=m.uv_layers.new(name=su.name or 'UVMap')
  for ni,si in enumerate(ids):
   a=sm.polygons[si];b=m.polygons[ni]
   for k in range(a.loop_total):u.data[b.loop_start+k].uv=su.data[a.loop_start+k].uv.copy()
 fa=m.attributes.new('BP3D_SOURCE_FACE_ID','INT','FACE')
 for i,x in enumerate(ids):fa.data[i].value=x
 o=bpy.data.objects.new('BP3D_R3_CLEAN_REFERENCE',m);bpy.context.scene.collection.objects.link(o);return o
def norm(o):
 used=sorted({v for p in o.data.polygons for v in p.vertices});vals=[[o.data.vertices[i].co[a] for i in used] for a in range(3)];sp=[max(x)-min(x) for x in vals];va=max(range(3),key=lambda a:sp[a]);r=[a for a in range(3) if a!=va];la=max(r,key=lambda a:sp[a]);da=[a for a in r if a!=la][0];cen=[(min(vals[a])+max(vals[a]))/2 for a in range(3)];hi=min(vals[va])+.88*sp[va];hd=[o.data.vertices[i].co[da] for i in used if o.data.vertices[i].co[va]>=hi];fs=1 if not hd or max(hd)-cen[da]>=cen[da]-min(hd) else -1
 for v in o.data.vertices:
  c=v.co.copy();v.co=Vector((c[la],c[da]*fs,c[va]))
 o.data.update();return {'vertical':va,'lateral':la,'depth':da,'front_sign':fs,'spans':sp}
def bounds(m):
 u=sorted({v for p in m.polygons for v in p.vertices});x=[m.vertices[i].co.x for i in u];y=[m.vertices[i].co.y for i in u];z=[m.vertices[i].co.z for i in u];return((min(x),min(y),min(z)),(max(x),max(y),max(z)),((min(x)+max(x))/2,(min(y)+max(y))/2,(min(z)+max(z))/2))
def depth_profile(m,b,bins=64):
 mn,mx,_=b;ys=[[] for _ in range(bins)]
 for p in m.polygons:
  h=(p.center.z-mn[2])/max(mx[2]-mn[2],1e-9);i=max(0,min(bins-1,int(h*bins)));ys[i].append(p.center.y)
 g=(mn[1]+mx[1])/2;mid=[((min(v)+max(v))/2 if v else None) for v in ys]
 for i in range(bins):
  if mid[i] is None:
   cand=[(abs(i-j),x) for j,x in enumerate(mid) if x is not None];mid[i]=min(cand)[1] if cand else g
 return mid
def cls(c,b,mode,dp):
 mn,mx,ct=b;h=(c.z-mn[2])/max(mx[2]-mn[2],1e-9);l=(c.x-ct[0])/max((mx[0]-mn[0])/2,1e-9);a=abs(l);bi=max(0,min(len(dp)-1,int(h*len(dp))));f=c.y>=dp[bi];s=lambda L,R:L if l<0 else R;unc=mode in ('D3','F3');wide=mode=='F3'
 if unc:
  if (.705 if not wide else .69)<h<(.775 if not wide else .79) and (.29 if not wide else .25)<a<(.47 if not wide else .51):return 101,.46
  if not f and (.575 if not wide else .56)<h<(.69 if not wide else .705) and (.18 if not wide else .14)<a<(.48 if not wide else .52):return 102,.48
  if (.405 if not wide else .395)<h<(.465 if not wide else .475) and (.14 if not wide else .10)<a<(.50 if not wide else .54):return 103,.48
  if (.188 if not wide else .18)<h<(.232 if not wide else .242) and a>.12:return 104,.53
  if (.445 if not wide else .43)<h<(.505 if not wide else .515) and a>(.55 if not wide else .51):return 105,.52
 if h>.89:r=(1,.94)
 elif h>.82 and a<.25:r=(s(2,3),.82)
 elif .38<h<.82 and a>.48:
  if h>.70:r=(s(5,6),.80)
  elif h>.58:r=((s(16,17),.78) if f else (s(18,19),.78))
  elif h>.49:r=((s(20,21),.75) if f else (s(22,23),.75))
  else:r=(s(24,25),.78)
 elif h>.70:r=(s(5,6),.79) if a>.30 else ((s(7,8),.83) if f else (4,.85))
 elif h>.50:r=((9,.87) if a<.17 else (s(10,11),.79)) if f else ((42,.74) if a<.16 and h<.61 else (s(12,13),.83))
 elif h>.40:r=((43,.72) if a<.18 else (s(26,27),.75)) if f else (s(14,15),.86)
 elif h>.24:r=(s(32,33),.84) if not f else ((s(30,31),.72) if a<.19 else (s(28,29),.83))
 elif h>.18:r=(s(34,35),.78)
 elif h>.055:r=(s(36,37),.79) if f else (s(38,39),.84)
 else:r=(s(40,41),.87)
 return (REM.get(r[0],r[0]),min(.96,r[1]+.03)) if mode=='E3' else r
def classify(o,mode):
 b=bounds(o.data);dp=depth_profile(o.data,b);L=[];C=[];co=Counter()
 for p in o.data.polygons:
  x,c=cls(p.center,b,mode,dp);L.append(x);C.append(c);co[x]+=1
 la=o.data.attributes.new('BP3D_LABEL_ID','INT','FACE');ca=o.data.attributes.new('BP3D_CONFIDENCE','FLOAT','FACE')
 for i,(x,c) in enumerate(zip(L,C)):la.data[i].value=x;ca.data[i].value=c
 for x in sorted(co):o.data.materials.append(mat('BP3D_%d_%s'%(x,N[x]),rgb(x)))
 ix={x:i for i,x in enumerate(sorted(co))}
 for p,x in zip(o.data.polygons,L):p.material_index=ix[x]
 return L,C,co,dp
def line(p,s,u,v,col,w):
 x0=int(max(0,min(s-1,u.x*(s-1))));y0=int(max(0,min(s-1,u.y*(s-1))));x1=int(max(0,min(s-1,v.x*(s-1))));y1=int(max(0,min(s-1,v.y*(s-1))));dx=abs(x1-x0);sx=1 if x0<x1 else -1;dy=-abs(y1-y0);sy=1 if y0<y1 else -1;e=dx+dy
 while 1:
  for yy in range(max(0,y0-w),min(s,y0+w+1)):
   for xx in range(max(0,x0-w),min(s,x0+w+1)):
    i=(yy*s+xx)*4;p[i:i+4]=array('f',col)
  if x0==x1 and y0==y1:break
  q=2*e
  if q>=dy:e+=dy;x0+=sx
  if q<=dx:e+=dx;y0+=sy
def texture(o,L,path):
 m=o.data;uv=m.uv_layers.active
 if not uv:return {'status':'NO_UV'}
 E=defaultdict(list)
 for p in m.polygons:
  z=list(p.loop_indices)
  for j,a in enumerate(z):
   b=z[(j+1)%len(z)];k=tuple(sorted((m.loops[a].vertex_index,m.loops[b].vertex_index)));E[k].append((p.index,uv.data[a].uv.copy(),uv.data[b].uv.copy()))
 px=array('f',[.94,.94,.94,1])*(SIZE*SIZE);n=un=0
 for vv in E.values():
  labs={L[x[0]] for x in vv}
  if len(labs)<2:continue
  n+=1;bad=any(x>=100 for x in labs);un+=bad;c=(.95,.06,.06,1) if bad else (.03,.03,.03,1)
  for _,a,b in vv:line(px,SIZE,a,b,c,2 if bad else 1)
 im=bpy.data.images.new(path.stem,width=SIZE,height=SIZE,alpha=True);im.pixels.foreach_set(px);im.filepath_raw=str(path);im.file_format='PNG';im.save();return {'status':'ORIGINAL_OBJ_UV','boundary_edges':n,'uncertain_edges':un}
def texmat(p):
 m=bpy.data.materials.new('BOUNDARY_TEXTURE');m.use_nodes=True;n=m.node_tree;n.nodes.clear();o=n.nodes.new('ShaderNodeOutputMaterial');e=n.nodes.new('ShaderNodeEmission');t=n.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(p));n.links.new(t.outputs['Color'],e.inputs['Color']);n.links.new(e.outputs['Emission'],o.inputs['Surface']);return m
def render(o,p,back=False):
 s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=800;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';
 if not s.world:s.world=bpy.data.worlds.new('W')
 s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.02,.02,.02,1)
 for x in bpy.data.objects:
  if x.type=='MESH':x.hide_render=x!=o
 mn,mx,c=bounds(o.data);c=Vector(c);scale=max(mx[0]-mn[0],mx[2]-mn[2]);dist=max(mx[i]-mn[i] for i in range(3))*3;d=bpy.data.cameras.new('C');cam=bpy.data.objects.new('C',d);s.collection.objects.link(cam);s.camera=cam;d.type='ORTHO';d.ortho_scale=scale*1.15;cam.location=c+Vector((0,-dist if back else dist,0));cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(p);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True);bpy.data.cameras.remove(d,do_unlink=True)
def split(o,mode):
 before=set(bpy.data.objects);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='MATERIAL');bpy.ops.object.mode_set(mode='OBJECT');xs=[x for x in bpy.data.objects if x not in before and x.type=='MESH']+[o]
 for x in xs:x.name=mode+'_PART_'+x.name
 return xs
def main():
 I=Path(arg('--input'));O=Path(arg('--output'));[(O/x).mkdir(parents=True,exist_ok=True) for x in ('textures','screenshots','models','reports')];H=sha(I);before=set(bpy.data.objects);bpy.ops.wm.obj_import(filepath=str(I));src=max([x for x in bpy.data.objects if x not in before and x.type=='MESH'],key=lambda x:len(x.data.polygons));src.hide_render=True;src.hide_set(True);cs=comp(src.data);ref=clean(src,cs[0]);plan=norm(ref);ref.hide_render=True;ref.hide_set(True);S={'schema_version':'bp3d_online_wholebody_experiment_r3','status':'RUNNING','source_sha256':H,'source_master_modified':False,'public_cc0_only':True,'user_assets_loaded':False,'review_basis':'Run2 screenshot/texture visual review','corrections':['local vertical-slice front/back centerline','reachable hand branch','narrower shoulder/axilla mask','scapular-lat excludes central spine','inguinal mask excludes central pelvis'],'source_mesh':{'vertices':len(src.data.vertices),'polygons':len(src.data.polygons),'uv_layers':[u.name for u in src.data.uv_layers]},'clean_face_count':len(cs[0]),'component_sizes':[len(x) for x in cs[:20]],'axis_plan':plan,'modes':{},'errors':[]};ok=0
 for mode in MODES:
  made=[]
  try:
   w=ref.copy();w.data=ref.data.copy();bpy.context.scene.collection.objects.link(w);w.hide_set(False);w.hide_render=False;made.append(w);L,C,co,dp=classify(w,mode);fa=w.data.attributes['BP3D_SOURCE_FACE_ID'];js(O/'reports'/(mode+'_face_labels.json'),{'mode':mode,'faces':[{'clean_face_index':i,'source_face_index':fa.data[i].value,'label_id':L[i],'label_key':N[L[i]],'confidence':C[i]} for i in range(len(L))]});tp=O/'textures'/(mode+'_boundary_lines.png');tr=texture(w,L,tp);render(w,O/'screenshots'/(mode+'_REGION_FRONT.png'));render(w,O/'screenshots'/(mode+'_REGION_BACK.png'),True);t=w.copy();t.data=w.data.copy();bpy.context.scene.collection.objects.link(t);made.append(t);t.data.materials.clear();t.data.materials.append(texmat(tp));[setattr(p,'material_index',0) for p in t.data.polygons];render(t,O/'screenshots'/(mode+'_TEXTURE_APPLY_FRONT.png'));t.hide_render=True;t.hide_set(True);xs=split(w,mode);made+=xs;bpy.ops.wm.save_as_mainfile(filepath=str(O/'models'/(mode+'_SPLIT.blend')),copy=True)
   try:bpy.ops.object.select_all(action='DESELECT');[x.select_set(True) for x in xs];bpy.context.view_layer.objects.active=xs[0];bpy.ops.export_scene.gltf(filepath=str(O/'models'/(mode+'_SPLIT.glb')),export_format='GLB',use_selection=True)
   except Exception as e:S['errors'].append({'mode':mode,'stage':'GLB_EXPORT','error':str(e)})
   S['modes'][mode]={'status':'SUCCESS','label_count':len(co),'face_count':len(L),'mean_confidence':sum(C)/len(C),'uncertainty_faces':sum(v for k,v in co.items() if k>=100),'counts':dict(co),'texture':tr,'split_object_count':len(xs),'hand_faces':co.get(24,0)+co.get(25,0),'calf_faces':co.get(38,0)+co.get(39,0),'upper_arm_front_faces':co.get(16,0)+co.get(17,0),'upper_arm_back_faces':co.get(18,0)+co.get(19,0)};ok+=1
  except Exception as e:S['errors'].append({'mode':mode,'stage':'MODE','error':str(e),'traceback':traceback.format_exc()});S['modes'][mode]={'status':'FAILED','error':str(e)};js(O/'reports'/(mode+'_ERROR.json'),S['errors'][-1])
  finally:
   for x in set(made):
    try:bpy.data.objects.remove(x,do_unlink=True)
    except:pass
 S['successful_mode_count']=ok;S['status']='PASS' if ok==3 else 'PARTIAL';js(O/'summary.json',S);(O/'SUCCESS_MARKER.txt').write_text(S['status']+'\n');print(json.dumps({'status':S['status'],'modes':ok,'clean_faces':len(cs[0])},indent=2))
 if ok<3:raise RuntimeError('Only %d/3 modes succeeded'%ok)
if __name__=='__main__':main()
