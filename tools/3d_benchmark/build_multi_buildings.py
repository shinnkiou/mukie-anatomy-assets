from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, json, random, time, shutil
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2] if 'tools' in Path(__file__).parts else Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT/'02_models'
QA_ROOT = ROOT/'03_qa'
for p in [MODEL_ROOT, QA_ROOT]: p.mkdir(parents=True, exist_ok=True)
random.seed(20260829)

FONT_CANDIDATES=['/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
def font(sz):
    for p in FONT_CANDIDATES:
        if Path(p).exists(): return ImageFont.truetype(p,sz)
    return ImageFont.load_default()

def tex_noise(path, base, size=(512,512), blur=.35, stripes=None):
    im=Image.new('RGB',size,base); d=ImageDraw.Draw(im)
    if stripes:
        for x in range(0,size[0],stripes):
            delta=random.randint(-10,10); c=tuple(max(0,min(255,v+delta)) for v in base)
            d.rectangle((x,0,min(size[0]-1,x+stripes-2),size[1]),fill=c)
    for _ in range(size[0]*size[1]//14):
        x=random.randrange(size[0]); y=random.randrange(size[1]); delta=random.randint(-14,14)
        c=tuple(max(0,min(255,v+delta)) for v in base); d.point((x,y),fill=c)
    if blur: im=im.filter(ImageFilter.GaussianBlur(blur))
    im.save(path)

def tex_sign(path, text, bg, fg='white', accent=None, size=(1024,240)):
    im=Image.new('RGB',size,bg); d=ImageDraw.Draw(im)
    if accent: d.rectangle((0,0,size[0],max(10,size[1]//12)),fill=accent)
    f=font(max(44,int(size[1]*.42))); bb=d.textbbox((0,0),text,font=f); w=bb[2]-bb[0]; h=bb[3]-bb[1]
    d.text(((size[0]-w)/2,(size[1]-h)/2-8),text,font=f,fill=fg); im.save(path)

def B(name,size,pos,mat,stage=1,rot_z=0): return {'type':'box','name':name,'size':list(size),'position':list(pos),'material':mat,'stage':stage,'rot_z':rot_z}
def C(name,radius,height,pos,mat,stage=3,segments=16): return {'type':'cylinder','name':name,'radius':radius,'height':height,'position':list(pos),'material':mat,'stage':stage,'segments':segments}
def rotate_z(p,a):
    x,y,z=p; c=math.cos(a); s=math.sin(a); return (x*c-y*s,x*s+y*c,z)
def box_faces(part):
    sx,sy,sz=part['size']; px,py,pz=part['position']; a=part.get('rot_z',0)
    cs=[(-sx/2,-sy/2,-sz/2),(sx/2,-sy/2,-sz/2),(sx/2,sy/2,-sz/2),(-sx/2,sy/2,-sz/2),(-sx/2,-sy/2,sz/2),(sx/2,-sy/2,sz/2),(sx/2,sy/2,sz/2),(-sx/2,sy/2,sz/2)]
    cs=[rotate_z(c,a) for c in cs]; cs=[(x+px,y+py,z+pz) for x,y,z in cs]
    idx=[[0,1,5,4],[2,3,7,6],[3,0,4,7],[1,2,6,5],[4,5,6,7],[3,2,1,0]]
    return [[cs[i] for i in f] for f in idx]

def building_specs():
    return {
      'convenience_store': {'title':'東京の都市型コンビニ（架空）','sign':'KONBINI 24','unit_scale':1.0,
        'materials':{'wall':{'Kd':'0.82 0.82 0.80','map':'textures/wall.png'},'dark':{'Kd':'0.08 0.09 0.10'},'glass':{'Kd':'0.20 0.38 0.48','d':'0.66','illum':'4'},'sign':{'Kd':'1.0 1.0 1.0','Ke':'0.20 0.28 0.24','map':'textures/sign.png'},'metal':{'Kd':'0.55 0.58 0.60'},'concrete':{'Kd':'0.45 0.44 0.42'},'green':{'Kd':'0.10 0.42 0.25'},'blue':{'Kd':'0.10 0.27 0.48'},'red':{'Kd':'0.70 0.12 0.10'},'white':{'Kd':'0.9 0.9 0.9'}},
        'textures':[('wall.png',(202,202,198),'noise'),('sign.png',None,'sign')],
        'parts':[B('StoreShell',(11.5,6.8,4.2),(0,2.9,2.1),'wall',1),B('Sidewalk',(14,2.5,.16),(0,-1.25,-.08),'concrete',1),B('StorefrontFrame',(10.5,.22,2.85),(0,-.60,1.60),'dark',1),B('GlassLeft',(3.5,.08,2.35),(-3.0,-.74,1.55),'glass',1),B('GlassRight',(3.5,.08,2.35),(3.0,-.74,1.55),'glass',1),B('EntranceFrame',(1.8,.16,2.7),(0,-.72,1.5),'dark',1),B('EntranceGlass',(1.45,.06,2.35),(0,-.82,1.5),'glass',1),B('SignBand',(11.0,.20,.82),(0,-.76,3.65),'sign',2),B('Canopy',(11.2,1.0,.16),(0,-1.0,3.25),'white',2),B('ATMPanel',(1.0,.28,1.8),(4.55,-.85,.95),'blue',2),B('PosterPanel',(1.3,.08,1.2),(-4.2,-.83,1.5),'red',2),B('TrashBin1',(.65,.60,1.0),(4.0,-1.25,.5),'metal',3),B('TrashBin2',(.65,.60,1.0),(4.75,-1.25,.5),'metal',3),B('CrateStack',(1.3,.55,.75),(-4.5,-1.10,.38),'blue',3),B('ACUnit',(1.1,.5,.75),(4.5,0,3.1),'metal',3),B('TactileStrip',(9.2,.42,.025),(-.4,-2.15,.02),'green',3),B('Curb',(14,.35,.22),(0,-2.55,-.11),'concrete',3),C('Bollard1',.09,.8,(-5.1,-1.55,.4),'metal',3),C('Bollard2',.09,.8,(5.1,-1.55,.4),'metal',3)]},
      'gas_station': {'title':'東京の都市型ガソリンスタンド（架空）','sign':'CITY FUEL','unit_scale':1.0,
        'materials':{'concrete':{'Kd':'0.42 0.43 0.44','map':'textures/concrete.png'},'white':{'Kd':'0.92 0.92 0.90'},'dark':{'Kd':'0.09 0.10 0.11'},'glass':{'Kd':'0.20 0.36 0.42','d':'0.68','illum':'4'},'sign':{'Kd':'1.0 1.0 1.0','Ke':'0.22 0.20 0.16','map':'textures/sign.png'},'red':{'Kd':'0.72 0.10 0.08'},'metal':{'Kd':'0.56 0.58 0.60'},'yellow':{'Kd':'0.85 0.72 0.10'}},
        'textures':[('concrete.png',(112,112,112),'noise'),('sign.png',None,'sign')],
        'parts':[B('Forecourt',(22,17,.18),(0,2.5,-.09),'concrete',1),B('ServiceBox',(9,4.8,3.8),(4.7,6.1,1.9),'white',1),B('ServiceGlass',(5.8,.08,2.2),(4.0,3.68,1.55),'glass',1),B('CanopyDeck',(16,10,.45),(-2,1.9,5.15),'white',1),C('CanopyColumn1',.22,5,(-7,-1,2.5),'metal',1),C('CanopyColumn2',.22,5,(3,-1,2.5),'metal',1),C('CanopyColumn3',.22,5,(-7,4.8,2.5),'metal',1),C('CanopyColumn4',.22,5,(3,4.8,2.5),'metal',1),B('CanopyFasciaFront',(16,.25,.72),(-2,-3,5.15),'sign',2),B('PriceTotem',(1.8,.55,5.6),(8.8,-4.8,2.8),'sign',2),B('PumpIsland1',(1.1,2.4,.22),(-5,-.6,.11),'concrete',2),B('PumpBody1',(.95,.65,2),(-5,-.6,1.1),'red',2),B('PumpIsland2',(1.1,2.4,.22),(0,-.6,.11),'concrete',2),B('PumpBody2',(.95,.65,2),(0,-.6,1.1),'red',2),B('PumpIsland3',(1.1,2.4,.22),(-5,3.6,.11),'concrete',2),B('PumpBody3',(.95,.65,2),(-5,3.6,1.1),'red',2),B('PumpIsland4',(1.1,2.4,.22),(0,3.6,.11),'concrete',2),B('PumpBody4',(.95,.65,2),(0,3.6,1.1),'red',2),B('ServiceDoor',(1.1,.1,2.2),(7.7,3.64,1.2),'dark',3),B('AirMachine',(1,.65,1.4),(7.7,1,.7),'metal',3),B('WheelStop1',(2.2,.25,.18),(5.2,10,.09),'yellow',3),B('WheelStop2',(2.2,.25,.18),(8.2,10,.09),'yellow',3),B('EntryMark',(4,.5,.025),(-7.5,-5,.02),'yellow',3,rot_z=.35),B('ExitMark',(4,.5,.025),(4.5,-5,.02),'yellow',3,rot_z=-.35)]},
      'ramen_shop': {'title':'東京の路面ラーメン屋（架空）','sign':'麺処 月路','unit_scale':1.0,
        'materials':{'plaster':{'Kd':'0.75 0.72 0.67','map':'textures/plaster.png'},'wood':{'Kd':'0.28 0.14 0.08','map':'textures/wood.png'},'dark':{'Kd':'0.035 0.04 0.045'},'glass':{'Kd':'0.22 0.38 0.44','d':'0.70','illum':'4'},'sign':{'Kd':'1.0 0.92 0.72','Ke':'0.26 0.16 0.05','map':'textures/sign.png'},'noren':{'Kd':'0.08 0.10 0.12','map':'textures/noren.png'},'red':{'Kd':'0.70 0.08 0.06'},'metal':{'Kd':'0.55 0.56 0.56'},'concrete':{'Kd':'0.43 0.42 0.40'},'warm':{'Kd':'0.95 0.52 0.20','Ke':'0.25 0.10 0.03'}},
        'textures':[('plaster.png',(185,178,166),'noise'),('wood.png',(76,43,29),'wood'),('sign.png',None,'sign'),('noren.png',None,'noren')],
        'parts':[B('ShopShell',(6.4,5.5,4.3),(0,2,2.15),'plaster',1),B('LowerWood',(6.4,.30,1.15),(0,-.66,.58),'wood',1),B('Sidewalk',(8,2,.16),(0,-1.45,-.08),'concrete',1),B('DoorFrame',(1.3,.18,2.45),(-1.65,-.72,1.35),'dark',1),B('DoorGlass',(1,.06,2.15),(-1.65,-.83,1.35),'glass',1),B('FrontWindowFrame',(2.6,.18,2.05),(.95,-.72,1.45),'dark',1),B('FrontWindow',(2.3,.06,1.8),(.95,-.83,1.45),'glass',1),B('SignBoard',(5.3,.20,.95),(0,-.77,3.65),'sign',2),B('Awning',(5.5,.9,.16),(0,-1.05,2.85),'dark',2),B('Noren',(2.2,.04,.85),(-.1,-1.18,2.2),'noren',2),B('MenuBoard',(.8,.18,1.25),(2.2,-1.35,.68),'dark',3,rot_z=-.1),B('TicketMachine',(.75,.55,1.7),(-2.35,-1,.85),'red',3),C('Lantern1',.23,.65,(1.4,-1.35,2.25),'red',3,segments=20),C('Lantern2',.23,.65,(1.95,-1.35,2.25),'red',3,segments=20),B('Bench',(1.8,.42,.38),(.2,-1.55,.32),'wood',3),B('ACUnit',(1,.52,.72),(2.45,-.45,3),'metal',3),C('DrainPipe',.06,4,(-2.75,-.48,2),'metal',3),B('WarmGlow',(2.1,.03,1.5),(.95,-.88,1.45),'warm',3)]}
    }

def make_textures(spec, folder):
    tex=folder/'textures'; tex.mkdir(parents=True,exist_ok=True)
    for name,base,kind in spec['textures']:
        p=tex/name
        if kind=='noise': tex_noise(p,base)
        elif kind=='wood': tex_noise(p,base,stripes=18)
        elif kind=='sign':
            if 'convenience' in folder.name: tex_sign(p,spec['sign'],'white','#12382b','#1b6f4a')
            elif 'gas_station' in folder.name: tex_sign(p,spec['sign'],'#f7f7f3','#b21610','#e8a10b')
            else: tex_sign(p,spec['sign'],'#c6a46a','#17120d')
        elif kind=='noren': tex_sign(p,'ラーメン','#15191e','#f1ede0',size=(1024,460))

def write_mtl(spec,path):
    lines=[]
    for name,m in spec['materials'].items():
        lines += [f'newmtl {name}',f'Kd {m.get("Kd","0.8 0.8 0.8")}', 'Ka 0.02 0.02 0.02','Ks 0.08 0.08 0.08','Ns 35']
        if 'Ke' in m: lines.append(f'Ke {m["Ke"]}')
        if 'd' in m: lines.append(f'd {m["d"]}')
        if 'illum' in m: lines.append(f'illum {m["illum"]}')
        if 'map' in m: lines.append(f'map_Kd {m["map"]}')
        lines.append('')
    path.write_text('\n'.join(lines),encoding='utf-8')

def write_obj(spec,stage,path,mtl_name):
    lines=[f'mtllib {mtl_name}',f'# stage {stage}']; vi=ti=1
    for p in spec['parts']:
        if p['stage']>stage: continue
        lines += [f'o {p["name"]}',f'usemtl {p["material"]}']
        if p['type']=='box':
            for face in box_faces(p):
                for v in face: lines.append('v %.6f %.6f %.6f'%v)
                for uv in [(0,0),(1,0),(1,1),(0,1)]: lines.append('vt %.6f %.6f'%uv)
                lines.append('f '+' '.join(f'{vi+j}/{ti+j}' for j in range(4))); vi+=4; ti+=4
        else:
            n=p.get('segments',16); cx,cy,cz=p['position']; r=p['radius']; h=p['height']; rings=[]
            for zz in [cz-h/2,cz+h/2]:
                ring=[]
                for i in range(n):
                    a=2*math.pi*i/n; lines.append('v %.6f %.6f %.6f'%(cx+r*math.cos(a),cy+r*math.sin(a),zz)); ring.append(vi); vi+=1
                rings.append(ring)
            bottom,top=rings
            for i in range(n):
                j=(i+1)%n; lines.append(f'f {bottom[i]} {bottom[j]} {top[j]} {top[i]}')
            lines.append('f '+' '.join(map(str,reversed(bottom)))); lines.append('f '+' '.join(map(str,top)))
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')

def build_glb(spec,stage,path):
    scene=trimesh.Scene(); palette={}
    for k,m in spec['materials'].items():
        kd=[float(x) for x in m.get('Kd','0.7 0.7 0.7').split()]; palette[k]=[int(255*x) for x in kd]+[255]
    for p in spec['parts']:
        if p['stage']>stage: continue
        mesh=trimesh.creation.box(extents=p['size']) if p['type']=='box' else trimesh.creation.cylinder(radius=p['radius'],height=p['height'],sections=p.get('segments',16))
        if p.get('rot_z'): mesh.apply_transform(trimesh.transformations.rotation_matrix(p['rot_z'],[0,0,1]))
        mesh.apply_translation(p['position']); mesh.visual.face_colors=np.tile(palette[p['material']],(len(mesh.faces),1)); scene.add_geometry(mesh,node_name=p['name'],geom_name=p['name'])
    path.write_bytes(scene.export(file_type='glb'))

def validate_obj(spec,path):
    txt=path.read_text(encoding='utf-8'); verts=[]; uvs=faces=objs=0; mats=set(); warnings=[]
    for l in txt.splitlines():
        if l.startswith('v '): verts.append(list(map(float,l.split()[1:4])))
        elif l.startswith('vt '): uvs+=1
        elif l.startswith('f '): faces+=1
        elif l.startswith('o '): objs+=1
        elif l.startswith('usemtl '): mats.add(l.split(None,1)[1])
    arr=np.array(verts) if verts else np.zeros((0,3))
    if not len(verts): warnings.append('no vertices')
    if np.isnan(arr).any() or np.isinf(arr).any(): warnings.append('NaN/Inf')
    if uvs==0: warnings.append('no UV')
    for m in mats:
        if m not in spec['materials']: warnings.append(f'unknown material:{m}')
    return {'objects':objs,'vertices':len(verts),'uvs':uvs,'faces':faces,'materials':len(mats),'warnings':warnings}

def texel_check(spec,folder):
    missing=[]
    for m in spec['materials'].values():
        if m.get('map') and not (folder/m['map']).exists(): missing.append(m['map'])
    return {'mapped_materials':sum(1 for m in spec['materials'].values() if m.get('map')),'missing_textures':missing,'uv_policy':'all box faces 0..1; debug-grade, not production atlas'}

def run():
    specs=building_specs(); summary={'date':'2026-08-29','models':{}}
    for key,spec in specs.items():
        folder=MODEL_ROOT/key; folder.mkdir(parents=True,exist_ok=True); make_textures(spec,folder); mtl=folder/f'{key}_v3.mtl'; write_mtl(spec,mtl)
        qrounds=[]
        for stage in (1,2,3):
            write_obj(spec,stage,folder/f'{key}_v{stage}.obj',mtl.name)
            if stage<3: shutil.copyfile(mtl,folder/f'{key}_v{stage}.mtl')
            q=validate_obj(spec,folder/f'{key}_v{stage}.obj'); q['round']=stage; qrounds.append(q)
        build_glb(spec,3,folder/f'{key}_v3.glb')
        tex=texel_check(spec,folder); warnings=qrounds[-1]['warnings']+[f'missing:{x}' for x in tex['missing_textures']]
        report={'qa_rounds_used':3,'qa_rounds_max':5,'rounds':qrounds,'texture_qa':tex,'final_glb_bytes':(folder/f'{key}_v3.glb').stat().st_size,'status':'PASS' if not warnings else 'WARN','warnings':warnings}
        (QA_ROOT/key).mkdir(parents=True,exist_ok=True); (QA_ROOT/key/'qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); summary['models'][key]=report
    (QA_ROOT/'benchmark_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': run()
