# -*- coding: utf-8 -*-
"""BP3D zone-based segmentation review loop.
Public-safe: MakeHuman CC0 base.obj only. Never loads user masters/textbook images.
Runs five bounded correction cycles, then emits SAFE/BALANCED/FINE final hypotheses.
"""
import bpy, sys, json, math, hashlib, traceback, colorsys
from pathlib import Path
from collections import Counter, defaultdict, deque
from mathutils import Vector

MAX_CYCLES = 5
FINAL_MODES = ("SAFE", "BALANCED", "FINE")
PALETTE = [
    (0.91,0.25,0.25,1),(0.25,0.56,0.92,1),(0.26,0.72,0.40,1),(0.95,0.67,0.18,1),
    (0.62,0.36,0.86,1),(0.10,0.73,0.73,1),(0.92,0.42,0.72,1),(0.55,0.73,0.18,1),
    (0.98,0.48,0.18,1),(0.35,0.42,0.92,1),(0.58,0.38,0.25,1),(0.25,0.75,0.62,1),
    (0.78,0.30,0.54,1),(0.45,0.62,0.82,1),(0.72,0.58,0.18,1),(0.55,0.55,0.55,1)
]
N = {
1:'HEAD',2:'NECK_SCM_L',3:'NECK_SCM_R',4:'TRAPEZIUS_UPPER',5:'DELTOID_L',6:'DELTOID_R',7:'PECTORAL_L',8:'PECTORAL_R',9:'RECTUS_ABDOMINIS',10:'OBLIQUE_L',11:'OBLIQUE_R',12:'LATISSIMUS_L',13:'LATISSIMUS_R',14:'GLUTEAL_L',15:'GLUTEAL_R',16:'BICEPS_L',17:'BICEPS_R',18:'TRICEPS_L',19:'TRICEPS_R',20:'FOREARM_ANTERIOR_L',21:'FOREARM_ANTERIOR_R',22:'FOREARM_POSTERIOR_L',23:'FOREARM_POSTERIOR_R',24:'HAND_L',25:'HAND_R',26:'HIP_LATERAL_L',27:'HIP_LATERAL_R',28:'THIGH_ANTERIOR_L',29:'THIGH_ANTERIOR_R',30:'THIGH_MEDIAL_L',31:'THIGH_MEDIAL_R',32:'THIGH_POSTERIOR_L',33:'THIGH_POSTERIOR_R',34:'KNEE_L',35:'KNEE_R',36:'SHIN_L',37:'SHIN_R',38:'CALF_L',39:'CALF_R',40:'FOOT_L',41:'FOOT_R',42:'THORACOLUMBAR_FASCIA_CONTEXT',43:'PELVIS_FRONT_CONTEXT',
44:'ELBOW_L',45:'ELBOW_R',46:'WRIST_L',47:'WRIST_R',48:'ANKLE_L',49:'ANKLE_R',50:'FOOT_DORSUM_L',51:'FOOT_DORSUM_R',52:'FOOT_PLANTAR_L',53:'FOOT_PLANTAR_R',54:'HEEL_L',55:'HEEL_R',56:'HALLUX_L',57:'HALLUX_R',58:'TOES_2_5_L',59:'TOES_2_5_R',60:'HAND_PALM_L',61:'HAND_PALM_R',62:'HAND_DORSUM_L',63:'HAND_DORSUM_R',64:'FINGER_PROXIMAL_L',65:'FINGER_PROXIMAL_R',66:'FINGER_MIDDLE_L',67:'FINGER_MIDDLE_R',68:'FINGER_DISTAL_L',69:'FINGER_DISTAL_R',70:'THUMB_L',71:'THUMB_R',
101:'U1_SHOULDER_AXILLA',102:'U2_SCAPULAR_LAT',103:'U3_INGUINAL_HIP',104:'U4_KNEE_TRANSITION',105:'U5_WRIST_HAND_TRANSITION',106:'U6_HAND_FINE',107:'U7_FOOT_FINE'
}
ZONE = {}
for i in (1,2,3): ZONE[i]='HED'
for i in (5,6,7,8,101): ZONE[i]='SHD'
for i in (9,10,11): ZONE[i]='TRS'
for i in (4,12,13,42,102): ZONE[i]='BCK'
for i in (16,17,18,19,20,21,22,23,44,45,46,47,105): ZONE[i]='ARM'
for i in (24,25,60,61,62,63,64,65,66,67,68,69,70,71,106): ZONE[i]='HND'
for i in (14,15,26,27,43,103): ZONE[i]='HIP'
for i in (28,29,30,31,32,33): ZONE[i]='THG'
for i in (34,35,104): ZONE[i]='KNE'
for i in (36,37,38,39,48,49): ZONE[i]='LEG'
for i in (40,41,50,51,52,53,54,55,56,57,58,59,107): ZONE[i]='FOT'

PAIR_IDS = [(2,3),(5,6),(7,8),(10,11),(12,13),(14,15),(16,17),(18,19),(20,21),(22,23),(24,25),(26,27),(28,29),(30,31),(32,33),(34,35),(36,37),(38,39),(40,41),(44,45),(46,47),(48,49),(50,51),(52,53),(54,55),(56,57),(58,59),(60,61),(62,63),(64,65),(66,67),(68,69),(70,71)]

CYCLE_PARAMS = [
 {"name":"C1_LOCAL_AXIS","arm_cut":[.18,.45,.54,.79,.88],"arm_width":.18,"u":1.00,"foot_toe":.74,"foot_heel":.22,"motion_blend":.018},
 {"name":"C2_HAND_RECOVERY","arm_cut":[.17,.43,.52,.78,.86],"arm_width":.17,"u":.82,"foot_toe":.72,"foot_heel":.24,"motion_blend":.035},
 {"name":"C3_TEXTBOOK_TRANSITIONS","arm_cut":[.16,.42,.51,.77,.85],"arm_width":.16,"u":.66,"foot_toe":.70,"foot_heel":.25,"motion_blend":.052},
 {"name":"C4_MOTION_SMOOTH","arm_cut":[.15,.41,.50,.76,.84],"arm_width":.155,"u":.52,"foot_toe":.69,"foot_heel":.26,"motion_blend":.072},
 {"name":"C5_BALANCED_FINAL","arm_cut":[.15,.40,.49,.75,.83],"arm_width":.15,"u":.42,"foot_toe":.68,"foot_heel":.27,"motion_blend":.090}
]

def args():
    a=sys.argv[sys.argv.index('--')+1:]
    def v(k): return a[a.index(k)+1]
    return Path(v('--input')), Path(v('--output'))
def write_json(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def smoothstep(x):
    x=max(0.0,min(1.0,x)); return x*x*(3-2*x)
def side_id(left,right,x): return left if x < 0 else right

def connected_components(mesh):
    v2=[[] for _ in mesh.vertices]
    for p in mesh.polygons:
        for v in p.vertices: v2[v].append(p.index)
    seen=bytearray(len(mesh.polygons)); out=[]
    for s in range(len(mesh.polygons)):
        if seen[s]: continue
        q=deque([s]); seen[s]=1; c=[]
        while q:
            f=q.popleft(); c.append(f)
            for v in mesh.polygons[f].vertices:
                for n in v2[v]:
                    if not seen[n]: seen[n]=1; q.append(n)
        out.append(c)
    return sorted(out,key=len,reverse=True)

def copy_component(src, face_ids):
    sm=src.data; m=bpy.data.meshes.new('BP3D_ZONE_CLEAN')
    m.from_pydata([v.co.copy() for v in sm.vertices],[],[list(sm.polygons[i].vertices) for i in face_ids]); m.update()
    if sm.uv_layers.active:
        su=sm.uv_layers.active; uv=m.uv_layers.new(name=su.name or 'UVMap')
        for ni,si in enumerate(face_ids):
            a=sm.polygons[si]; b=m.polygons[ni]
            for k in range(a.loop_total): uv.data[b.loop_start+k].uv=su.data[a.loop_start+k].uv.copy()
    att=m.attributes.new('BP3D_SOURCE_FACE_ID','INT','FACE')
    for i,src_id in enumerate(face_ids): att.data[i].value=src_id
    o=bpy.data.objects.new('BP3D_ZONE_CLEAN_REFERENCE',m); bpy.context.scene.collection.objects.link(o); return o

def normalize_axes(obj):
    used=sorted({v for p in obj.data.polygons for v in p.vertices})
    vals=[[obj.data.vertices[i].co[a] for i in used] for a in range(3)]
    spans=[max(x)-min(x) for x in vals]; vertical=max(range(3),key=lambda a:spans[a])
    rem=[a for a in range(3) if a!=vertical]; lateral=max(rem,key=lambda a:spans[a]); depth=[a for a in rem if a!=lateral][0]
    center=[(min(vals[a])+max(vals[a]))/2 for a in range(3)]
    hi=min(vals[vertical])+.88*spans[vertical]
    head_depth=[obj.data.vertices[i].co[depth] for i in used if obj.data.vertices[i].co[vertical]>=hi]
    front_sign=1 if not head_depth or max(head_depth)-center[depth]>=center[depth]-min(head_depth) else -1
    for v in obj.data.vertices:
        c=v.co.copy(); v.co=Vector((c[lateral],c[depth]*front_sign,c[vertical]))
    obj.data.update()
    return {"vertical":vertical,"lateral":lateral,"depth":depth,"front_sign":front_sign,"spans":spans}

def bounds(mesh):
    used=sorted({v for p in mesh.polygons for v in p.vertices})
    xs=[mesh.vertices[i].co.x for i in used]; ys=[mesh.vertices[i].co.y for i in used]; zs=[mesh.vertices[i].co.z for i in used]
    mn=(min(xs),min(ys),min(zs)); mx=(max(xs),max(ys),max(zs)); ct=tuple((mn[i]+mx[i])/2 for i in range(3)); return mn,mx,ct

def face_edges(mesh):
    edge_faces=defaultdict(list)
    for p in mesh.polygons:
        vs=list(p.vertices)
        for i,a in enumerate(vs): edge_faces[tuple(sorted((a,vs[(i+1)%len(vs)])))].append(p.index)
    return edge_faces

def mesh_edges(mesh):
    return list(face_edges(mesh).keys())

def arm_geometry(mesh,b):
    mn,mx,ct=b; half=(mx[0]-mn[0])/2; zspan=mx[2]-mn[2]
    z0=mn[2]+.78*zspan; z1=mn[2]+.56*zspan; x0=.30*half; x1=.985*half
    dx=x1-x0; dz=z1-z0; den=dx*dx+dz*dz
    meta=[]; bins=[[] for _ in range(48)]
    for p in mesh.polygons:
        x=abs(p.center.x); z=p.center.z
        t=((x-x0)*dx+(z-z0)*dz)/den
        px=x0+t*dx; pz=z0+t*dz; dist=math.hypot(x-px,z-pz)
        candidate=(x>.24*half and -.12<t<1.18 and dist<(.075*zspan + .35*(1-max(0,min(1,t)))))
        meta.append((candidate,t,dist,-1 if p.center.x<0 else 1))
        if candidate:
            bi=max(0,min(47,int(max(0,min(.999,t))*48))); bins[bi].append(p.center.y)
    centers=[]; global_y=ct[1]
    for i,v in enumerate(bins):
        if v: centers.append((min(v)+max(v))/2)
        else:
            near=[(abs(i-j),(min(w)+max(w))/2) for j,w in enumerate(bins) if w]
            centers.append(min(near)[1] if near else global_y)
    return {"p0":(x0,z0),"p1":(x1,z1),"d":(dx,dz),"den":den,"meta":meta,"depth_centers":centers,"half":half,"zspan":zspan}

def body_depth_profile(mesh,b,bins=64):
    mn,mx,ct=b; ys=[[] for _ in range(bins)]
    for p in mesh.polygons:
        h=(p.center.z-mn[2])/max(mx[2]-mn[2],1e-9); i=max(0,min(bins-1,int(h*bins))); ys[i].append(p.center.y)
    out=[]
    for i,v in enumerate(ys):
        if v: out.append((min(v)+max(v))/2)
        else:
            q=[(abs(i-j),(min(w)+max(w))/2) for j,w in enumerate(ys) if w]; out.append(min(q)[1] if q else ct[1])
    return out

def foot_geometry(mesh,b):
    mn,mx,ct=b; zspan=mx[2]-mn[2]; zcut=mn[2]+.075*zspan
    by_side={-1:[],1:[]}
    for p in mesh.polygons:
        if p.center.z<=zcut:
            by_side[-1 if p.center.x<0 else 1].append((p.index,p.center.x,p.center.y,p.center.z))
    out={}
    for s,rows in by_side.items():
        if not rows: continue
        ys=[r[2] for r in rows]; xs=[abs(r[1]) for r in rows]
        out[s]={"miny":min(ys),"maxy":max(ys),"minx":min(xs),"maxx":max(xs),"zcut":zcut}
    return out

def classify(mesh, mode, param):
    b=bounds(mesh); mn,mx,ct=b; zspan=mx[2]-mn[2]; arm=arm_geometry(mesh,b); bodydp=body_depth_profile(mesh,b); foot=foot_geometry(mesh,b)
    labels=[]; conf=[]; aux=[]
    cuts=param['arm_cut']; u=param['u']
    for p in mesh.polygons:
        x,y,z=p.center; h=(z-mn[2])/zspan; lateral=(x-ct[0])/max((mx[0]-mn[0])/2,1e-9); a=abs(lateral); side=-1 if x<0 else 1
        bi=max(0,min(len(bodydp)-1,int(max(0,min(.999,h))*len(bodydp)))); front=y>=bodydp[bi]
        ac,t,dist,_=arm['meta'][p.index]
        if ac:
            abi=max(0,min(47,int(max(0,min(.999,t))*48))); afront=y>=arm['depth_centers'][abi]
            # Shoulder/axilla is intentionally an unresolved seam in conservative/detail modes when evidence is weak.
            if t < cuts[0]:
                if mode!='BALANCED' and t>.08 and dist>(.48+.20*u): lab=101; c=.55
                else: lab=side_id(5,6,x); c=.86
            elif t < cuts[1]: lab=side_id(16,17,x) if afront else side_id(18,19,x); c=.84
            elif t < cuts[2]: lab=side_id(44,45,x); c=.83
            elif t < cuts[3]: lab=side_id(20,21,x) if afront else side_id(22,23,x); c=.82
            elif t < cuts[4]:
                lab=105 if mode=='SAFE' else side_id(46,47,x); c=.64 if lab==105 else .80
            else:
                q=max(0,min(1,(t-cuts[4])/max(1.12-cuts[4],1e-6)))
                if mode=='SAFE': lab=side_id(24,25,x); c=.82
                elif mode=='BALANCED': lab=side_id(60,61,x) if afront else side_id(62,63,x); c=.78
                else:
                    # Fine hand: segment along distal axis; thumb remains conservative where local branch identity is ambiguous.
                    if q<.36: lab=side_id(60,61,x) if afront else side_id(62,63,x); c=.76
                    elif q<.58: lab=side_id(64,65,x); c=.70
                    elif q<.78: lab=side_id(66,67,x); c=.67
                    else: lab=side_id(68,69,x); c=.66
            labels.append(lab); conf.append(c); aux.append({"arm_t":t,"front":afront,"h":h}); continue
        # Feet/ankles use local depth + surface normal, not whole-body height alone.
        fg=foot.get(side)
        if h < .105 and fg:
            fq=(y-fg['miny'])/max(fg['maxy']-fg['miny'],1e-9)
            if h>.067:
                lab=side_id(48,49,x); c=.82
            elif mode=='SAFE':
                lab=side_id(40,41,x); c=.86
            elif fq < param['foot_heel']:
                lab=side_id(54,55,x); c=.85
            elif fq > param['foot_toe']:
                medial=(abs(x)-fg['minx'])/max(fg['maxx']-fg['minx'],1e-9)
                lab=side_id(56,57,x) if medial<.31 else side_id(58,59,x); c=.74
            else:
                nz=p.normal.z
                lab=side_id(52,53,x) if nz < -.22 else side_id(50,51,x); c=.78
            labels.append(lab); conf.append(c); aux.append({"foot_q":fq,"h":h}); continue
        # Main body / legs.
        if h>.89: lab=1; c=.94
        elif h>.82 and a<.28: lab=side_id(2,3,x); c=.84
        elif h>.70:
            if a>.30: lab=side_id(5,6,x); c=.79
            elif front: lab=side_id(7,8,x); c=.84
            else: lab=4; c=.86
        elif h>.50:
            if front: lab=9 if a<.18 else side_id(10,11,x); c=.84
            else:
                if a<.18 and h<.61: lab=42; c=.76
                elif .20<a<.34 and .58<h<.69 and mode!='BALANCED': lab=102; c=.58
                else: lab=side_id(12,13,x); c=.84
        elif h>.40:
            if .15<a<.52 and .405<h<.465 and mode!='BALANCED' and u>.45: lab=103; c=.58
            elif front: lab=43 if a<.18 else side_id(26,27,x); c=.78
            else: lab=side_id(14,15,x); c=.87
        elif h>.24:
            if not front: lab=side_id(32,33,x); c=.85
            elif a<.20: lab=side_id(30,31,x); c=.76
            else: lab=side_id(28,29,x); c=.84
        elif h>.18:
            if mode!='BALANCED' and .192<h<(.228+.01*u): lab=104; c=.60
            else: lab=side_id(34,35,x); c=.82
        elif h>.105:
            lab=side_id(36,37,x) if front else side_id(38,39,x); c=.84
        else:
            lab=side_id(40,41,x); c=.80
        labels.append(lab); conf.append(c); aux.append({"h":h,"front":front})
    return labels,conf,aux,{"bounds":b,"arm":arm,"foot":foot}

def label_adjacency(mesh,labels):
    pairs=set(); ef=face_edges(mesh)
    for fs in ef.values():
        if len(fs)==2:
            a,b=labels[fs[0]],labels[fs[1]]
            if a!=b: pairs.add(tuple(sorted((a,b))))
    return pairs

def graph_colors(labels,pairs):
    labs=sorted(set(labels)); neigh={x:set() for x in labs}
    for a,b in pairs: neigh[a].add(b); neigh[b].add(a)
    order=sorted(labs,key=lambda x:(-len(neigh[x]),x)); assignment={}
    for lab in order:
        used={assignment[n] for n in neigh[lab] if n in assignment}; idx=next((i for i in range(len(PALETTE)) if i not in used),0); assignment[lab]=idx
    conflicts=sum(1 for a,b in pairs if assignment.get(a)==assignment.get(b)); return assignment,conflicts

def make_material(name,color):
    m=bpy.data.materials.new(name); m.diffuse_color=color; m.use_nodes=True; nt=m.node_tree; nt.nodes.clear(); out=nt.nodes.new('ShaderNodeOutputMaterial'); em=nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value=color; em.inputs['Strength'].default_value=1; nt.links.new(em.outputs['Emission'],out.inputs['Surface']); return m

def apply_labels(obj,labels,conf,revision):
    mesh=obj.data; pairs=label_adjacency(mesh,labels); colors,conflicts=graph_colors(labels,pairs)
    la=mesh.attributes.new('BP3D_LABEL_ID','INT','FACE'); ca=mesh.attributes.new('BP3D_CONFIDENCE','FLOAT','FACE')
    for i,(lab,c) in enumerate(zip(labels,conf)): la.data[i].value=lab; ca.data[i].value=c
    lab_order=sorted(set(labels)); midx={}
    for lab in lab_order:
        c=PALETTE[colors[lab]]; mesh.materials.append(make_material('BP3D_%d_%s'%(lab,N[lab]),c)); midx[lab]=len(mesh.materials)-1
    for p,lab in zip(mesh.polygons,labels): p.material_index=midx[lab]
    return {"adjacency_pairs":len(pairs),"color_conflicts":conflicts,"color_index":{str(k):v for k,v in colors.items()}}

def render(obj,path,view='FRONT',res=(520,700)):
    s=bpy.context.scene; s.render.engine='BLENDER_EEVEE_NEXT'; s.render.resolution_x=res[0]; s.render.resolution_y=res[1]; s.render.resolution_percentage=100; s.render.image_settings.file_format='PNG'; s.render.film_transparent=False
    if not s.world: s.world=bpy.data.worlds.new('BP3D_WORLD')
    s.world.use_nodes=True; s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.018,.018,.022,1); s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
    for x in bpy.data.objects:
        if x.type=='MESH': x.hide_render=(x!=obj)
    mn,mx,ct=bounds(obj.data); center=Vector(ct); span=max(mx[i]-mn[i] for i in range(3)); camd=bpy.data.cameras.new('BP3D_CAM'); cam=bpy.data.objects.new('BP3D_CAM',camd); s.collection.objects.link(cam); s.camera=cam; camd.type='ORTHO'; camd.ortho_scale=max(mx[0]-mn[0],mx[2]-mn[2])*1.12
    if view=='FRONT': off=Vector((0,span*3,0))
    elif view=='BACK': off=Vector((0,-span*3,0))
    elif view=='LEFT': off=Vector((-span*3,0,0))
    else: off=Vector((span*3,0,0))
    cam.location=center+off; cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler(); s.render.filepath=str(path); bpy.ops.render.render(write_still=True); bpy.data.objects.remove(cam,do_unlink=True); bpy.data.cameras.remove(camd,do_unlink=True)

def rotate_about_x(v,pivot,ang):
    y=v.y-pivot.y; z=v.z-pivot.z; c=math.cos(ang); s=math.sin(ang); return Vector((v.x,pivot.y+c*y-s*z,pivot.z+s*y+c*z))
def rotate_about_y(v,pivot,ang):
    x=v.x-pivot.x; z=v.z-pivot.z; c=math.cos(ang); s=math.sin(ang); return Vector((pivot.x+c*x+s*z,v.y,pivot.z-s*x+c*z))
def blend_vec(a,b,w): return a*(1-w)+b*w

def motion_pose(obj, geo, pose, blend):
    out=obj.copy(); out.data=obj.data.copy(); bpy.context.scene.collection.objects.link(out); out.name='POSE_'+pose
    mn,mx,ct=geo['bounds']; zspan=mx[2]-mn[2]; arm=geo['arm']; x0,z0=arm['p0']; dx,dz=arm['d']; den=arm['den']
    half=(mx[0]-mn[0])/2
    for v in out.data.vertices:
        co=v.co.copy(); x=co.x; side=-1 if x<0 else 1; ax=abs(x); t=((ax-x0)*dx+(co.z-z0)*dz)/den
        target=co.copy(); w=0.0
        if pose=='SHOULDER_RAISE' and ax>.22*half and t>-.05:
            pivot=Vector((side*x0,0,z0)); target=rotate_about_y(co,pivot,side*math.radians(68)); w=smoothstep((t+.04)/max(blend,1e-4))
        elif pose=='ELBOW_BEND' and ax>.25*half and t>.42:
            ex=x0+.49*dx; ez=z0+.49*dz; pivot=Vector((side*ex,0,ez)); target=rotate_about_x(co,pivot,math.radians(82)); w=smoothstep((t-.42)/max(blend*1.4,1e-4))
        elif pose=='HIP_FLEX' and co.z<mn[2]+.47*zspan and abs(x)>.06*half:
            pivot=Vector((side*.23*half,0,mn[2]+.43*zspan)); target=rotate_about_x(co,pivot,math.radians(48)); w=smoothstep((.45-(co.z-mn[2])/zspan)/max(blend*1.6,1e-4))
        elif pose=='KNEE_BEND' and co.z<mn[2]+.25*zspan and abs(x)>.06*half:
            pivot=Vector((side*.23*half,0,mn[2]+.22*zspan)); target=rotate_about_x(co,pivot,math.radians(-72)); w=smoothstep((.24-(co.z-mn[2])/zspan)/max(blend*1.5,1e-4))
        elif pose=='ANKLE_TOE' and co.z<mn[2]+.09*zspan and abs(x)>.06*half:
            pivot=Vector((side*.23*half,0,mn[2]+.07*zspan)); target=rotate_about_x(co,pivot,math.radians(30)); w=smoothstep((.095-(co.z-mn[2])/zspan)/max(blend,1e-4))
        v.co=blend_vec(co,target,w)
    out.data.update(); return out

def stretch_metric(src,posed):
    bad=0; severe=0; maxr=1.0; total=0
    for a,b in mesh_edges(src.data):
        l0=(src.data.vertices[a].co-src.data.vertices[b].co).length
        if l0<1e-8: continue
        l1=(posed.data.vertices[a].co-posed.data.vertices[b].co).length; r=l1/l0; total+=1; maxr=max(maxr,r,1/max(r,1e-8))
        if r>1.35 or r<.74: bad+=1
        if r>1.70 or r<.50: severe+=1
    return {"edges":total,"bad_edges":bad,"severe_edges":severe,"bad_pct":100*bad/max(total,1),"max_stretch_or_collapse":maxr}

def per_label_components(mesh,labels):
    ef=face_edges(mesh); adj=[[] for _ in mesh.polygons]
    for fs in ef.values():
        if len(fs)==2: adj[fs[0]].append(fs[1]); adj[fs[1]].append(fs[0])
    by=defaultdict(list)
    for i,l in enumerate(labels): by[l].append(i)
    result={}
    for lab,faces in by.items():
        pool=set(faces); comps=[]
        while pool:
            s=pool.pop(); q=[s]; n=1
            while q:
                f=q.pop()
                for g in adj[f]:
                    if g in pool and labels[g]==lab: pool.remove(g); q.append(g); n+=1
            comps.append(n)
        result[lab]=sorted(comps,reverse=True)
    return result

def quality(mesh,labels,conf,color_meta,motion):
    counts=Counter(labels); pair_err=[]
    for l,r in PAIR_IDS:
        if l in counts or r in counts:
            d=abs(counts.get(l,0)-counts.get(r,0))/max(counts.get(l,0)+counts.get(r,0),1); pair_err.append(d)
    comps=per_label_components(mesh,labels); fragments=sum(max(0,len(v)-1) for v in comps.values()); slivers=sum(1 for v in counts.values() if v<12); unresolved=sum(v for k,v in counts.items() if k>=100)
    required_presence={
      'arm_hand': all(counts.get(i,0)>0 for i in (16,17,18,19,20,21,22,23,44,45,46,47)),
      'hand_macro': (counts.get(24,0)+counts.get(25,0)+counts.get(60,0)+counts.get(61,0)+counts.get(62,0)+counts.get(63,0)+counts.get(64,0)+counts.get(65,0)+counts.get(66,0)+counts.get(67,0)+counts.get(68,0)+counts.get(69,0))>0,
      'calf': counts.get(38,0)+counts.get(39,0)>0,
      'foot': counts.get(40,0)+counts.get(41,0)+counts.get(50,0)+counts.get(51,0)+counts.get(52,0)+counts.get(53,0)+counts.get(54,0)+counts.get(55,0)>0
    }
    bad_motion=sum(x['bad_pct'] for x in motion.values())/max(len(motion),1)
    score=100.0
    score-=min(18,unresolved/len(labels)*100*.65); score-=min(12,fragments*.35); score-=min(10,slivers*1.1); score-=min(18,bad_motion*1.4); score-=min(10,(sum(pair_err)/max(len(pair_err),1))*35); score-=color_meta['color_conflicts']*5
    score+=sum(2 for v in required_presence.values() if v)
    return {"score":round(score,3),"counts":{str(k):v for k,v in counts.items()},"mean_confidence":sum(conf)/len(conf),"unresolved_faces":unresolved,"unresolved_pct":100*unresolved/len(labels),"symmetry_mean_error":sum(pair_err)/max(len(pair_err),1),"fragment_excess_components":fragments,"sliver_label_count":slivers,"required_presence":required_presence,"color":color_meta,"motion":motion,"components":{str(k):v for k,v in comps.items()}}

def split_and_name(obj,mode,rev):
    before=set(bpy.data.objects); bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
    xs=[x for x in bpy.data.objects if x not in before and x.type=='MESH']+[obj]
    for x in xs:
        matname=x.data.materials[0].name if x.data.materials else ''
        lab=None
        if matname.startswith('BP3D_'):
            try: lab=int(matname.split('_')[1])
            except: pass
        if lab in N:
            zone=ZONE.get(lab,'UNK'); part=N[lab]; side='L' if part.endswith('_L') else ('R' if part.endswith('_R') else 'C'); surf='ALL'
            if 'ANTERIOR' in part: surf='ANT'
            elif 'POSTERIOR' in part: surf='POST'
            elif 'PALM' in part: surf='PAL'
            elif 'DORSUM' in part: surf='DOR'
            elif 'PLANTAR' in part: surf='PLN'
            detail=3 if mode=='FINE' else (2 if mode=='BALANCED' else 1)
            x.name=f'BP3D_{zone}_{part}_{side}_{surf}_L{detail}_R{rev}'
    return xs

def save_final(ref,mode,param,outdir,rev):
    work=ref.copy(); work.data=ref.data.copy(); bpy.context.scene.collection.objects.link(work); work.hide_set(False); work.hide_render=False
    labels,conf,aux,geo=classify(work.data,mode,param); color=apply_labels(work,labels,conf,rev)
    motions={}; pose_objs=[]
    for pose in ('SHOULDER_RAISE','ELBOW_BEND','HIP_FLEX','KNEE_BEND','ANKLE_TOE'):
        po=motion_pose(work,geo,pose,param['motion_blend']); pose_objs.append(po); motions[pose]=stretch_metric(work,po); render(po,outdir/'screenshots'/f'{mode}_{pose}.png','FRONT',(480,640)); po.hide_render=True; po.hide_set(True)
    q=quality(work.data,labels,conf,color,motions)
    render(work,outdir/'screenshots'/f'{mode}_FRONT.png','FRONT'); render(work,outdir/'screenshots'/f'{mode}_BACK.png','BACK'); render(work,outdir/'screenshots'/f'{mode}_SIDE.png','RIGHT')
    srcatt=work.data.attributes['BP3D_SOURCE_FACE_ID']; write_json(outdir/'reports'/f'{mode}_face_labels.json',{'mode':mode,'revision':rev,'faces':[{'clean_face_index':i,'source_face_index':srcatt.data[i].value,'label_id':labels[i],'label_key':N[labels[i]],'confidence':conf[i]} for i in range(len(labels))]})
    xs=split_and_name(work,mode,rev); bpy.ops.wm.save_as_mainfile(filepath=str(outdir/'models'/f'BP3D_{mode}_FINAL_R{rev}.blend'),copy=True)
    try:
        bpy.ops.object.select_all(action='DESELECT'); [x.select_set(True) for x in xs]; bpy.context.view_layer.objects.active=xs[0]; bpy.ops.export_scene.gltf(filepath=str(outdir/'models'/f'BP3D_{mode}_FINAL_R{rev}.glb'),export_format='GLB',use_selection=True)
    except Exception as e: q['glb_error']=str(e)
    for x in set(xs+pose_objs):
        try: bpy.data.objects.remove(x,do_unlink=True)
        except: pass
    return q

def main():
    inp,out=args();
    for d in ('cycles','screenshots','models','reports'): (out/d).mkdir(parents=True,exist_ok=True)
    h0=sha256(inp); before=set(bpy.data.objects); bpy.ops.wm.obj_import(filepath=str(inp)); src=max([o for o in bpy.data.objects if o not in before and o.type=='MESH'],key=lambda o:len(o.data.polygons)); source_counts=(len(src.data.vertices),len(src.data.polygons)); comps=connected_components(src.data); ref=copy_component(src,comps[0]); plan=normalize_axes(ref); ref.hide_render=True; ref.hide_set(True)
    report={"schema_version":"bp3d_zone_review_loop_v1","status":"RUNNING","source_sha256_before":h0,"source_master_modified":False,"public_cc0_only":True,"user_assets_loaded":False,"textbook_images_loaded":False,"abc_abcd_modified":False,"source_mesh":{"vertices":source_counts[0],"polygons":source_counts[1],"clean_faces":len(comps[0]),"uv_layers":[u.name for u in src.data.uv_layers]},"axis_plan":plan,"cycles":[],"final":{},"errors":[]}
    best=None
    for ci,param in enumerate(CYCLE_PARAMS,1):
        w=ref.copy(); w.data=ref.data.copy(); bpy.context.scene.collection.objects.link(w); w.hide_set(False); w.hide_render=False
        try:
            labels,conf,aux,geo=classify(w.data,'BALANCED',param); color=apply_labels(w,labels,conf,ci); motions={}; poses=[]
            for pose in ('SHOULDER_RAISE','ELBOW_BEND','HIP_FLEX','KNEE_BEND','ANKLE_TOE'):
                po=motion_pose(w,geo,pose,param['motion_blend']); poses.append(po); motions[pose]=stretch_metric(w,po)
            q=quality(w.data,labels,conf,color,motions); q['cycle']=ci; q['name']=param['name']; q['params']=param
            render(w,out/'cycles'/f'C{ci}_FRONT.png','FRONT',(420,560)); render(w,out/'cycles'/f'C{ci}_BACK.png','BACK',(420,560)); report['cycles'].append(q)
            if best is None or q['score']>best['score']: best=q
            for po in poses:
                try:bpy.data.objects.remove(po,do_unlink=True)
                except:pass
        except Exception as e:
            er={'cycle':ci,'error':str(e),'traceback':traceback.format_exc()}; report['errors'].append(er); write_json(out/'reports'/f'C{ci}_ERROR.json',er)
        finally:
            try:bpy.data.objects.remove(w,do_unlink=True)
            except:pass
    if not best: raise RuntimeError('No correction cycle completed')
    best_param=CYCLE_PARAMS[best['cycle']-1]; report['best_cycle']=best['cycle']; report['best_cycle_score']=best['score']
    final_params={
      'SAFE':dict(best_param, u=max(.75,best_param['u']), motion_blend=max(.11,best_param['motion_blend'])),
      'BALANCED':dict(best_param),
      'FINE':dict(best_param, u=max(.50,best_param['u']*.85), motion_blend=max(.075,best_param['motion_blend']*.90))
    }
    predictions={
      'SAFE':{'success_prediction':'lowest seam/detail risk and strongest motion tolerance','failure_prediction':'may under-segment hand/foot and preserve unresolved transition bands'},
      'BALANCED':{'success_prediction':'best drawing-oriented compromise using textbook macro anatomy and local limb axes','failure_prediction':'some fine hand/foot subregions may remain approximate without user-master texture/rig evidence'},
      'FINE':{'success_prediction':'highest anatomical/drawing detail for hand and foot targets','failure_prediction':'highest sliver, naming uncertainty and motion-weight risk; should be accepted only where evidence and user-master pose tests agree'}
    }
    for mode in FINAL_MODES:
        q=save_final(ref,mode,final_params[mode],out,5); q['prediction']=predictions[mode]; report['final'][mode]=q
    h1=sha256(inp); report['source_sha256_after']=h1; report['source_unchanged']=(h0==h1); report['status']='PASS' if report['source_unchanged'] and len(report['final'])==3 else 'FAIL'
    lines=['# BP3D Zone Review Loop Report','',f"Status: **{report['status']}**",f"Source unchanged: **{report['source_unchanged']}**",f"Best correction cycle: **C{report['best_cycle']}** score {report['best_cycle_score']}",'','## Correction cycles']
    for c in report['cycles']:
        lines.append(f"- C{c['cycle']} {c['name']}: score={c['score']}, unresolved={c['unresolved_pct']:.2f}%, fragments={c['fragment_excess_components']}, motion_bad_mean={sum(v['bad_pct'] for v in c['motion'].values())/len(c['motion']):.2f}%")
    lines+=['','## Final hypotheses']
    for mode,q in report['final'].items():
        lines.append(f"- {mode}: score={q['score']}; success={q['prediction']['success_prediction']}; failure={q['prediction']['failure_prediction']}")
    lines+=['','## Interpretation','Technical PASS is not anatomical approval. Online motion is a proxy because the public MakeHuman CC0 mesh does not include the user master rig. The duplicated user master must later receive the same labels/colors and undergo real pose/weight validation.']
    (out/'reports'/'ZONE_REVIEW_REPORT.md').write_text('\n'.join(lines),encoding='utf-8'); write_json(out/'summary.json',report); (out/'SUCCESS_MARKER.txt').write_text(report['status']+'\n',encoding='utf-8'); print(json.dumps({'status':report['status'],'best_cycle':report['best_cycle'],'final_modes':list(report['final'])},indent=2))
    if report['status']!='PASS': raise RuntimeError('Zone review loop failed validation')
if __name__=='__main__': main()
