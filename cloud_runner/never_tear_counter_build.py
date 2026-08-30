import bpy, math, json, os, hashlib
from pathlib import Path
from mathutils import Vector
from math import radians

OUT=Path(os.environ.get('NEVER_TEAR_OUT','artifacts/never_tear_counter')).resolve()
for p in [OUT,OUT/'models',OUT/'renders',OUT/'reports']: p.mkdir(parents=True,exist_ok=True)
REV='R1'; M=.91; WALL_BAYS=7; COUNTER_BAYS=6

bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=720; scene.render.resolution_y=480; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.render.image_settings.color_mode='RGBA'
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.world=bpy.data.worlds.new('World') if scene.world is None else scene.world
scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value=(.012,.009,.007,1); bg.inputs['Strength'].default_value=.28
try: scene.view_settings.look='AgX - Medium High Contrast'
except Exception: pass
scene.view_settings.exposure=.45

COLL=bpy.data.collections.new('NEVER_TEAR_COUNTER_WALL')
scene.collection.children.link(COLL)

def link(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    COLL.objects.link(o); o['never_tear']=True; return o

def mat(name,base,rough=.5,metal=0,ior=1.5,trans=.0,emission=None,emit_strength=0,noise=None,bump=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear(); out=nt.nodes.new('ShaderNodeOutputMaterial'); bs=nt.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=(*base,1); bs.inputs['Roughness'].default_value=rough; bs.inputs['Metallic'].default_value=metal; bs.inputs['IOR'].default_value=ior
    if 'Transmission Weight' in bs.inputs: bs.inputs['Transmission Weight'].default_value=trans
    if emission:
        if 'Emission Color' in bs.inputs: bs.inputs['Emission Color'].default_value=(*emission,1)
        if 'Emission Strength' in bs.inputs: bs.inputs['Emission Strength'].default_value=emit_strength
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    if noise:
        tex=nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=noise.get('scale',6); tex.inputs['Detail'].default_value=noise.get('detail',4); tex.inputs['Roughness'].default_value=noise.get('roughness',.65)
        ramp=nt.nodes.new('ShaderNodeValToRGB'); c1=noise.get('c1',base); c2=noise.get('c2',tuple(min(1,v*1.35) for v in base)); ramp.color_ramp.elements[0].color=(*c1,1); ramp.color_ramp.elements[1].color=(*c2,1)
        nt.links.new(tex.outputs['Fac'],ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
        if bump:
            bn=nt.nodes.new('ShaderNodeBump'); bn.inputs['Strength'].default_value=bump; bn.inputs['Distance'].default_value=.08; nt.links.new(tex.outputs['Fac'],bn.inputs['Height']); nt.links.new(bn.outputs['Normal'],bs.inputs['Normal'])
    return m

def box(name,size,loc,material,rot=(0,0,0),bevel=.018):
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot); o=bpy.context.object; o.name=name; o.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel: be=o.modifiers.new('Bevel','BEVEL'); be.width=bevel; be.segments=3
    o.data.materials.append(material); return link(o)

def cyl(name,r,depth,loc,material,rot=(0,0,0),verts=24,bevel=.008):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc,rotation=rot); o=bpy.context.object; o.name=name
    if bevel: be=o.modifiers.new('Bevel','BEVEL'); be.width=bevel; be.segments=2
    o.data.materials.append(material); return link(o)

def text(name,body,loc,size,material,rot=(radians(90),0,0)):
    bpy.ops.object.text_add(location=loc,rotation=rot); o=bpy.context.object; o.name=name; o.data.body=body; o.data.align_x='CENTER'; o.data.align_y='CENTER'; o.data.size=size; o.data.extrude=.008; o.data.bevel_depth=.002
    for fp in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']:
        if Path(fp).exists():
            try:o.data.font=bpy.data.fonts.load(fp);break
            except:pass
    o.data.materials.append(material); return link(o)

def point(name,loc,energy,color):
    ld=bpy.data.lights.new(name,'POINT'); ld.energy=energy; ld.color=color; ld.shadow_soft_size=.14; o=bpy.data.objects.new(name,ld); o.location=loc; COLL.objects.link(o); return o

def area(name,loc,energy,color,size,rot):
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.color=color; ld.shape='RECTANGLE'; ld.size=size; ld.size_y=size
    o=bpy.data.objects.new(name,ld); o.location=loc; o.rotation_euler=rot; COLL.objects.link(o); return o

def camera(name,loc,target,lens=50):
    cd=bpy.data.cameras.new(name); cd.lens=lens; o=bpy.data.objects.new(name,cd); scene.collection.objects.link(o); o.location=loc; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler(); return o

def export_prefix(prefix,filename):
    bpy.ops.object.select_all(action='DESELECT'); n=0
    for o in COLL.objects:
        if o.name.startswith(prefix) and o.type in {'MESH','CURVE','FONT'}: o.select_set(True); n+=1
    if n: bpy.ops.export_scene.gltf(filepath=str(OUT/'models'/filename),export_format='GLB',use_selection=True,export_apply=True,export_materials='EXPORT')
    return n

def export_final():
    bpy.ops.object.select_all(action='DESELECT')
    for o in COLL.objects:
        if o.type in {'MESH','CURVE','FONT'}: o.select_set(True)
    path=OUT/'models'/f'NEVER_TEAR_COUNTER_WALL_{REV}.glb'; bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_materials='EXPORT'); return path

walnut=mat('Walnut',(0.25,.085,.032),.50,.02,noise={'scale':5,'detail':5,'c1':(.08,.018,.007),'c2':(.42,.14,.045)},bump=.16)
walnut_dark=mat('WalnutDark',(.09,.026,.012),.60,.02,noise={'scale':8,'detail':4,'c1':(.018,.004,.002),'c2':(.18,.045,.012)},bump=.11)
plaster=mat('Plaster',(.39,.35,.32),.87,noise={'scale':38,'detail':2,'c1':(.29,.26,.24),'c2':(.50,.45,.40)},bump=.07)
steel=mat('Steel',(.34,.36,.38),.30,.93); brass=mat('Brass',(.52,.27,.055),.24,1.0); black=mat('Black',(.014,.014,.018),.36,.78)
leather=mat('Leather',(.055,.025,.020),.46,.02,noise={'scale':55,'detail':2,'c1':(.025,.010,.008),'c2':(.075,.035,.025)},bump=.10)
mirror=mat('Mirror',(.30,.34,.36),.10,.78); glass=mat('Glass',(.20,.32,.34),.09,0,1.45,.84); amber=mat('AmberGlass',(.29,.075,.012),.12,0,1.45,.42); green=mat('GreenGlass',(.025,.19,.08),.12,0,1.45,.42)
paper=mat('Paper',(.84,.78,.63),.76); red=mat('Red',(.50,.025,.018),.40,.04); blue=mat('Blue',(.025,.09,.30),.38,.04); warm=mat('WarmEmit',(1,.36,.07),.30,0,emission=(1,.16,.025),emit_strength=3.0)

# 1) 910 mm wall modules. Slight 2 mm overlap seals seams while preserving module centers.
for i in range(WALL_BAYS):
    x=-(M*WALL_BAYS)/2+M/2+i*M
    box(f'A01_WALL_BAY_{i+1:02d}',(M+.002,.18,2.70),(x,-1.10,1.35),plaster)
    for s in range(6): box(f'A01_SLAT_{i+1:02d}_{s+1}',(.124,.055,2.58),(x-.355+s*.142,-1.205,1.35),walnut_dark,bevel=.010)

# Continuous mirror and trims prevent the old bite/gap artifact.
box('A01_MIRROR',(5.55,.045,1.54),(0,-1.235,1.66),mirror,bevel=.006)
box('A01_TRIM_TOP',(5.66,.075,.052),(0,-1.205,2.46),brass,bevel=.010); box('A01_TRIM_BOTTOM',(5.66,.075,.052),(0,-1.205,.86),brass,bevel=.010)

# 2) Shelves, lips and LED per bay, exact module-derived positions.
for row,z in enumerate([1.12,1.61,2.10],1):
    for i in range(WALL_BAYS):
        x=-(M*WALL_BAYS)/2+M/2+i*M
        box(f'A02_SHELF_R{row}_B{i+1:02d}',(M+.002,.28,.055),(x,-.78,z),walnut,bevel=.010)
        box(f'A02_LIP_R{row}_B{i+1:02d}',(M+.002,.032,.035),(x,-.62,z+.035),brass,bevel=.006)
        box(f'A12_LED_R{row}_B{i+1:02d}',(M-.02,.020,.018),(x,-.625,z-.052),warm,bevel=.004)

text('A10_SIGN','NEVER TEAR',(0,-1.28,2.48),.25,warm)

# 3) Bottle family: body + shoulder + neck + cap + label, 45 instances.
def bottle(idx,x,y,z,kind):
    gm=[amber,green,glass][kind%3]; scale=.92+(idx%5)*.025
    cyl(f'A03_BOTTLE_{idx:02d}_BODY',.047*scale,.245*scale,(x,y,z+.122*scale),gm)
    bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.046*scale,radius2=.027*scale,depth=.055*scale,location=(x,y,z+.272*scale)); o=link(bpy.context.object); o.name=f'A03_BOTTLE_{idx:02d}_SHOULDER'; o.data.materials.append(gm)
    cyl(f'A03_BOTTLE_{idx:02d}_NECK',.021*scale,.082*scale,(x,y,z+.342*scale),gm)
    cyl(f'A03_BOTTLE_{idx:02d}_CAP',.022*scale,.018*scale,(x,y,z+.394*scale),black if idx%2 else brass)
    box(f'A03_BOTTLE_{idx:02d}_LABEL',(.072,.006,.080),(x,y-.050,z+.155*scale),paper,bevel=.002)

idx=0
for row,z in enumerate([1.12,1.61,2.10]):
    for j in range(15):
        idx+=1; bottle(idx,-2.52+j*.36+(row%2)*.035,-.615,z+.055,row+j)

# 4) Glass family on lower ledge.
for i in range(10):
    x=-2.30+i*.15; cyl(f'A04_ROCKS_{i+1:02d}',.045,.105,(x,-.59,.98),glass,verts=24,bevel=.003)
for i in range(8):
    x=-.65+i*.15; cyl(f'A04_HIGHBALL_{i+1:02d}',.040,.18,(x,-.59,1.02),glass,verts=24,bevel=.003)

# 5) Counter modules + one continuous top. Gap QA uses the body edges, not visual guesswork.
CW=M*COUNTER_BAYS
box('A11_COUNTER_TOP',(CW+.10,.64,.09),(0,.72,1.05),walnut,bevel=.028)
for i in range(COUNTER_BAYS):
    x=-(CW)/2+M/2+i*M
    box(f'A11_COUNTER_BAY_{i+1:02d}',(M+.003,.55,.91),(x,.75,.545),walnut_dark,bevel=.014)
    for s in range(5): box(f'A11_FRONT_SLAT_{i+1:02d}_{s+1}',(.12,.045,.80),(x-.30+s*.15,1.045,.54),walnut,bevel=.006)
cyl('A11_FOOTRAIL',.022,CW-.18,(0,1.28,.27),brass,rot=(0,radians(90),0),verts=24)
box('A12_COUNTER_LED',(CW-.12,.025,.025),(0,1.055,.86),warm,bevel=.004)

# 6) Beer tower with 3 taps and drip tray.
box('A05_DRIP_TRAY',(.82,.28,.035),(-1.52,.55,1.11),steel,bevel=.012)
for i in range(3):
    x=-1.75+i*.23; cyl(f'A05_TOWER_{i+1}',.048,.47,(x,.63,1.34),brass); cyl(f'A05_TAP_{i+1}',.022,.18,(x,.54,1.50),brass,rot=(radians(90),0,0),verts=16); box(f'A05_HANDLE_{i+1}',(.05,.05,.18),(x,.54,1.64),walnut if i==1 else black,bevel=.009)

# 7) Sink / faucet / ice well / soda gun / POS as separate templates.
box('A06_SINK_RIM',(.62,.46,.035),(-.45,.72,1.10),steel,bevel=.012); box('A06_SINK_BASIN',(.50,.34,.12),(-.45,.72,1.035),black,bevel=.020)
cyl('A06_FAUCET_STEM',.025,.31,(-.70,.78,1.27),steel); cyl('A06_FAUCET_SPOUT',.022,.24,(-.70,.66,1.42),steel,rot=(radians(90),0,0),verts=16)
box('A07_ICE_WELL',(.58,.42,.14),(.28,.72,1.02),steel,bevel=.015)
for i in range(14): box(f'A07_ICE_{i+1:02d}',(.065,.065,.055),(.08+(i%5)*.09,.60+(i//5)*.08,1.115),glass,rot=(.12*(i%3),.10*(i%2),.09*i),bevel=.010)
box('A08_SODA_GUN',(.16,.055,.07),(.88,.56,1.135),black,bevel=.012)
for i,c in enumerate([red,green,blue,warm,paper]): box(f'A08_BUTTON_{i+1}',(.022,.022,.012),(.83+i*.028,.532,1.176),c,bevel=.004)
for i in range(7): cyl(f'A08_HOSE_{i+1}',.008,.10,(.96+.035*i,.64+.025*i,1.00-.035*i),black,rot=(0,.65,0),verts=10,bevel=0)
box('A09_POS_BASE',(.28,.22,.035),(1.42,.68,1.105),black,bevel=.012); box('A09_POS_SCREEN',(.31,.035,.23),(1.42,.63,1.28),black,rot=(-.20,0,0),bevel=.016); text('A09_POS_TEXT','POS',(1.42,.607,1.29),.06,warm,rot=(radians(90)-.20,0,0))

for i,x in enumerate([-2.40,2.38],1):
    box(f'A10_MENU_FRAME_{i}',(.44,.035,.58),(x,-.56,1.58),walnut_dark,bevel=.014); box(f'A10_MENU_PAPER_{i}',(.37,.008,.50),(x,-.58,1.58),paper,bevel=.003)

# Pump bottle, napkin, bar mat and stools: small-scale silhouette/detail.
cyl('PROP_PUMP_BODY',.043,.23,(1.92,.61,1.17),glass); cyl('PROP_PUMP_NECK',.018,.08,(1.92,.61,1.325),black); box('PROP_PUMP_HEAD',(.10,.025,.018),(1.965,.61,1.38),black,bevel=.004)
box('PROP_NAPKIN',(.18,.08,.16),(2.18,.61,1.14),steel,bevel=.008); box('PROP_BAR_MAT',(.78,.24,.018),(-1.50,.91,1.105),black,bevel=.003)
for i in range(COUNTER_BAYS):
    x=-(CW)/2+M/2+i*M; cyl(f'STOOL_{i+1}_SEAT',.25,.10,(x,1.75,.72),leather); cyl(f'STOOL_{i+1}_POST',.030,.62,(x,1.75,.36),steel); cyl(f'STOOL_{i+1}_BASE',.20,.028,(x,1.75,.04),steel)

# Lighting separated from geometry.
for i in range(3): point(f'LIGHT_PENDANT_{i+1}',(-1.8+i*1.8,.35,2.45),175,(1.0,.48,.18))
area('LIGHT_FRONT_FILL',(0,3.6,2.0),420,(1.0,.68,.42),4.0,(radians(78),0,radians(180)))
area('LIGHT_BARKBAR',(0,-.20,2.35),240,(1.0,.34,.08),5.0,(radians(90),0,0))

cam=camera('CAM_COUNTER_FRONT',(6.5,6.8,3.25),(0,.15,1.25),58); scene.camera=cam

# Export reusable object families first.
asset_exports={
'A01':'A01_WALL_BAY','A02':'A02_SHELF','A03':'A03_BOTTLE_01','A04':'A04_ROCKS','A05':'A05_','A06':'A06_','A07':'A07_','A08':'A08_','A09':'A09_','A10':'A10_','A11':'A11_COUNTER_BAY_01','A12':'A12_'}
for key,prefix in asset_exports.items(): export_prefix(prefix,f'NEVER_TEAR_{key}_{REV}.glb')

# Machine QA: no module seam gaps, no invalid scale, required detailed assets and readable exposure.
def module_gap(prefix,count):
    objs=sorted([o for o in COLL.objects if o.name.startswith(prefix)],key=lambda o:o.location.x)
    gaps=[]
    for a,b in zip(objs,objs[1:]):
        ax=a.location.x+a.dimensions.x/2; bx=b.location.x-b.dimensions.x/2; gaps.append(bx-ax)
    return max(gaps) if gaps else 0

def image_mean():
    rr=bpy.data.images.get('Render Result')
    if not rr or not rr.has_data: return 0.0
    px=rr.pixels; n=len(px)//4; step=max(1,n//18000); total=0.0; c=0
    for i in range(0,n,step):
        r,g,b=px[i*4],px[i*4+1],px[i*4+2]; total+=.2126*r+.7152*g+.0722*b; c+=1
    return total/max(c,1)

qa=[]; MAX_QA=10
for round_no in range(1,MAX_QA+1):
    g1=module_gap('A01_WALL_BAY_',WALL_BAYS); g2=module_gap('A11_COUNTER_BAY_',COUNTER_BAYS)
    invalid=[o.name for o in COLL.objects if o.type=='MESH' and (min(o.dimensions)<=0 or max(o.dimensions)>20)]
    required=['A05_TOWER_1','A06_SINK_RIM','A07_ICE_WELL','A08_SODA_GUN','A09_POS_SCREEN','A10_MENU_FRAME_1','A11_COUNTER_TOP']
    missing=[n for n in required if bpy.data.objects.get(n) is None]
    scene.render.filepath=str(OUT/'renders'/f'QA{round_no:02d}_COUNTER.png'); bpy.ops.render.render(write_still=True)
    lum=image_mean(); changes=[]
    if lum<.06: scene.view_settings.exposure+=.30; changes.append('EXPOSURE_UP')
    elif lum>.72: scene.view_settings.exposure-=.20; changes.append('EXPOSURE_DOWN')
    passed=(g1<=.0005 and g2<=.0005 and not invalid and not missing and .06<=lum<=.72)
    qa.append({'round':round_no,'wall_gap_m':g1,'counter_gap_m':g2,'invalid':invalid,'missing':missing,'luminance':lum,'changes':changes,'pass':passed})
    print('[NEVER_TEAR_QA]',qa[-1],flush=True)
    if passed: break

final_glb=export_final(); blend=OUT/'models'/f'NEVER_TEAR_COUNTER_WALL_{REV}.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(blend))
scene.render.filepath=str(OUT/'renders'/f'FINAL_COUNTER_{REV}.png'); bpy.ops.render.render(write_still=True)

stats={'objects':len(COLL.objects),'meshes':sum(o.type=='MESH' for o in COLL.objects),'materials':len(bpy.data.materials),'wall_width_m':M*WALL_BAYS,'counter_width_m':M*COUNTER_BAYS,'qa_rounds':len(qa)}
manifest={'schema':'never_tear_counter_detail_v1','project':'NEVER TEAR','revision':REV,'scope':'counter-wall-only','module_m':M,'stats':stats,'qa':qa,'status':'PASS' if qa[-1]['pass'] else 'WARN','final_glb':str(final_glb.relative_to(OUT)),'final_blend':str(blend.relative_to(OUT)),'asset_exports':[p.name for p in (OUT/'models').glob('NEVER_TEAR_A*.glb')]}
(OUT/'reports'/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2),flush=True)
