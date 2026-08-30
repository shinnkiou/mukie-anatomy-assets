import bpy, math, json, os, sys, traceback, hashlib
from mathutils import Vector
from pathlib import Path
from math import radians

OUT = Path(os.environ.get('BAR_NEVATIA_OUT','artifacts/bar_nevatia')).resolve()
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'models').mkdir(exist_ok=True)
(OUT/'renders').mkdir(exist_ok=True)
(OUT/'reports').mkdir(exist_ok=True)

REV='R1'
MODULES=['SHELL','EXTERIOR','INTERIOR','FURNITURE','PROPS','LIGHTING']
collections={}

def log(msg):
    print('[BAR_NEVATIA]', msg, flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=960
scene.render.resolution_y=640
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.render.image_settings.color_mode='RGBA'
scene.world.color=(0.006,0.008,0.012)
try:
    scene.view_settings.look='AgX - Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure=0.2
scene.view_settings.gamma=1.0

for name in MODULES:
    c=bpy.data.collections.new('MOD_'+name)
    scene.collection.children.link(c)
    collections[name]=c

def link_obj(obj, module='SHELL'):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collections[module].objects.link(obj)
    obj['module']=module
    obj['bar_nevatia']=True
    return obj

def mat_principled(name, base, rough=.5, metal=0.0, ior=1.5, transmission=0.0, alpha=1.0, emission=None, emission_strength=0.0, noise=None, bump=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial')
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=(*base,1)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metal
    bs.inputs['IOR'].default_value=ior
    if 'Transmission Weight' in bs.inputs: bs.inputs['Transmission Weight'].default_value=transmission
    elif 'Transmission' in bs.inputs: bs.inputs['Transmission'].default_value=transmission
    bs.inputs['Alpha'].default_value=alpha
    if emission:
        if 'Emission Color' in bs.inputs: bs.inputs['Emission Color'].default_value=(*emission,1)
        elif 'Emission' in bs.inputs: bs.inputs['Emission'].default_value=(*emission,1)
        if 'Emission Strength' in bs.inputs: bs.inputs['Emission Strength'].default_value=emission_strength
    nt.links.new(bs.outputs['BSDF'], out.inputs['Surface'])
    if noise:
        tex=nt.nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value=noise.get('scale',5)
        tex.inputs['Detail'].default_value=noise.get('detail',3)
        tex.inputs['Roughness'].default_value=noise.get('roughness',.6)
        ramp=nt.nodes.new('ShaderNodeValToRGB')
        c1=noise.get('c1',base); c2=noise.get('c2',tuple(min(1,v*1.25) for v in base))
        ramp.color_ramp.elements[0].color=(*c1,1); ramp.color_ramp.elements[1].color=(*c2,1)
        nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bs.inputs['Base Color'])
        if bump:
            b=nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value=bump; b.inputs['Distance'].default_value=.12
            nt.links.new(tex.outputs['Fac'], b.inputs['Height']); nt.links.new(b.outputs['Normal'], bs.inputs['Normal'])
    if alpha<1.0:
        m.surface_render_method='DITHERED'
    return m

def add_box(name, size, loc, mat=None, module='SHELL', rot=(0,0,0), bevel=.04):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.dimensions=size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel>0:
        be=o.modifiers.new('Bevel','BEVEL'); be.width=bevel; be.segments=3
    if mat: o.data.materials.append(mat)
    return link_obj(o,module)

def add_cyl(name, radius, depth, loc, mat=None, module='PROPS', rot=(0,0,0), verts=32, bevel=.02):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name
    if bevel:
        be=o.modifiers.new('Bevel','BEVEL'); be.width=bevel; be.segments=2
    if mat: o.data.materials.append(mat)
    return link_obj(o,module)

def add_sphere(name, radius, loc, mat=None, module='PROPS', scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=radius, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat: o.data.materials.append(mat)
    return link_obj(o,module)

def add_text(name, text, loc, size=.35, extrude=.015, mat=None, module='PROPS', rot=(radians(90),0,0), align='CENTER'):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.data.body=text; o.data.align_x=align; o.data.align_y='CENTER'
    o.data.size=size; o.data.extrude=extrude; o.data.bevel_depth=.003; o.data.bevel_resolution=3
    font_candidates=['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc']
    for fp in font_candidates:
        if Path(fp).exists():
            try: o.data.font=bpy.data.fonts.load(fp); break
            except Exception: pass
    if mat: o.data.materials.append(mat)
    return link_obj(o,module)

def add_area(name, loc, energy, color, size=2.0, rot=(0,0,0), module='LIGHTING'):
    data=bpy.data.lights.new(name=name, type='AREA'); data.energy=energy; data.color=color; data.shape='RECTANGLE'; data.size=size; data.size_y=size
    o=bpy.data.objects.new(name,data); o.location=loc; o.rotation_euler=rot; collections[module].objects.link(o); o['module']=module; o['bar_nevatia']=True
    return o

def add_point(name, loc, energy, color, radius=.15, module='LIGHTING'):
    data=bpy.data.lights.new(name=name, type='POINT'); data.energy=energy; data.color=color; data.shadow_soft_size=radius
    o=bpy.data.objects.new(name,data); o.location=loc; collections[module].objects.link(o); o['module']=module; o['bar_nevatia']=True
    return o

def add_camera(name, loc, target, lens=38):
    data=bpy.data.cameras.new(name); data.lens=lens; data.sensor_width=36
    o=bpy.data.objects.new(name,data); scene.collection.objects.link(o); o.location=loc
    direction=Vector(target)-o.location; o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    return o

def set_camera(cam): scene.camera=cam

def export_module(module, filename):
    bpy.ops.object.select_all(action='DESELECT')
    for o in collections[module].objects:
        if o.type in {'MESH','CURVE','FONT'}:
            o.select_set(True)
    path=OUT/'models'/filename
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_apply=True, export_materials='EXPORT')
    return path

def export_final(filename='BAR_NEVATIA_FINAL_R1.glb'):
    bpy.ops.object.select_all(action='DESELECT')
    for c in collections.values():
        for o in c.objects:
            if o.type in {'MESH','CURVE','FONT'}: o.select_set(True)
    path=OUT/'models'/filename
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_apply=True, export_materials='EXPORT')
    return path

walnut=mat_principled('Walnut',(0.20,0.075,0.035),rough=.52,noise={'scale':4,'detail':5,'roughness':.65,'c1':(0.09,0.025,0.012),'c2':(0.34,0.12,0.045)},bump=.18)
walnut_dark=mat_principled('WalnutDark',(0.085,0.032,0.018),rough=.60,noise={'scale':7,'detail':3,'c1':(0.025,0.008,0.005),'c2':(0.16,0.05,0.02)},bump=.12)
wood_light=mat_principled('OakLight',(0.42,0.22,0.09),rough=.55,noise={'scale':5,'detail':4,'c1':(0.28,0.12,0.045),'c2':(0.58,0.32,0.12)},bump=.11)
plaster=mat_principled('Plaster',(0.46,0.43,0.39),rough=.86,noise={'scale':45,'detail':2,'c1':(0.37,0.35,0.32),'c2':(0.55,0.51,0.46)},bump=.08)
black=mat_principled('BlackMetal',(0.018,0.018,0.022),rough=.36,metal=.80)
steel=mat_principled('Steel',(0.28,0.30,0.32),rough=.33,metal=.92)
brass=mat_principled('Brass',(0.47,0.25,0.055),rough=.27,metal=1.0)
cream=mat_principled('CreamPaint',(0.79,0.74,0.65),rough=.74)
concrete=mat_principled('Concrete',(0.22,0.225,0.23),rough=.93,noise={'scale':18,'detail':2,'c1':(0.14,0.14,0.14),'c2':(0.32,0.32,0.31)},bump=.16)
asphalt=mat_principled('Asphalt',(0.055,0.058,0.06),rough=.96,noise={'scale':30,'detail':2,'c1':(0.025,0.025,0.026),'c2':(0.10,0.10,0.11)},bump=.13)
white_line=mat_principled('ParkingLine',(0.82,0.80,0.72),rough=.82)
blue_door=mat_principled('DoorBlue',(0.025,0.085,0.16),rough=.35,metal=.12)
clear_glass=mat_principled('ClearGlass',(0.10,0.16,0.18),rough=.08,metal=0,ior=1.45,transmission=1.0,alpha=.28)
frosted_glass=mat_principled('FrostedGlass',(0.30,0.39,0.42),rough=.32,metal=0,ior=1.45,transmission=.75,alpha=.55)
menu_paper=mat_principled('MenuPaper',(0.88,0.83,0.70),rough=.72)
blue_ink=mat_principled('BlueInk',(0.02,0.055,0.30),rough=.45)
red=mat_principled('Red',(0.42,0.03,0.02),rough=.42)
orange=mat_principled('Orange',(0.82,0.14,0.03),rough=.42)
softpink=mat_principled('SoapPink',(0.86,0.48,0.58),rough=.48)
whiteplastic=mat_principled('WhitePlastic',(0.72,0.73,0.70),rough=.52)
blackplastic=mat_principled('BlackPlastic',(0.025,0.026,0.03),rough=.44)
emissive_warm=mat_principled('WarmEmit',(1.0,0.38,0.10),rough=.3,emission=(1.0,0.18,0.035),emission_strength=3.2)
emissive_sign=mat_principled('SignEmit',(0.95,0.72,0.26),rough=.25,emission=(1.0,0.35,0.08),emission_strength=2.1)

BW,BD=7.28,9.10
WALL=.16
CEIL=3.0
add_box('Foundation',(BW+.4,BD+.4,.20),(0,BD/2,-.10),concrete,'SHELL',bevel=.02)
add_box('InteriorFloor',(BW-.22,BD-.22,.08),(0,BD/2,.02),walnut_dark,'SHELL',bevel=.015)
add_box('Wall_West',(WALL,BD,CEIL),(-BW/2,BD/2,CEIL/2),plaster,'SHELL')
add_box('Wall_East',(WALL,BD,CEIL),(BW/2,BD/2,CEIL/2),plaster,'SHELL')
add_box('Wall_Back',(BW,WALL,CEIL),(0,BD,CEIL/2),plaster,'SHELL')
add_box('FrontWall_L',(1.25,WALL,CEIL),(-3.015,0,CEIL/2),plaster,'SHELL')
add_box('FrontWall_M',(1.20,WALL,CEIL),(-.65,0,CEIL/2),plaster,'SHELL')
add_box('FrontWall_R',(1.15,WALL,CEIL),(3.05,0,CEIL/2),plaster,'SHELL')
add_box('FrontHeader',(BW,WALL,.45),(0,0,2.775),plaster,'SHELL')
add_box('FrontSillWin',(2.45,WALL,.82),(1.25,0,.41),plaster,'SHELL')
add_box('RearPartition',(BW,WALL,CEIL),(0,7.28,CEIL/2),plaster,'SHELL')
add_box('RearSplit',(WALL,1.82,CEIL),(1.82,8.19,CEIL/2),plaster,'SHELL')
add_box('FrontServicePartition',(WALL,1.82,CEIL),(-1.82,.91,CEIL/2),plaster,'SHELL')
add_box('Ceiling',(BW,BD,.08),(0,BD/2,CEIL+.04),plaster,'SHELL',bevel=.01)
roof_mat=mat_principled('Roof',(0.06,0.055,0.055),rough=.78,metal=.08)
roof_angle=radians(12); half=(BW+.7)/2
add_box('Roof_L',(half,BD+.8,.14),(-half/2,BD/2,3.42),roof_mat,'SHELL',rot=(0,-roof_angle,0),bevel=.02)
add_box('Roof_R',(half,BD+.8,.14),(half/2,BD/2,3.42),roof_mat,'SHELL',rot=(0,roof_angle,0),bevel=.02)
add_box('RoofFasciaFront',(BW+.8,.16,.28),(0,-.28,3.22),black,'SHELL',bevel=.02)

for i,x in enumerate([(-3.55 + i*.22) for i in range(33)]):
    if -2.15 < x < -1.15 or -.05 < x < 2.55: continue
    add_box(f'FacadeSlat_{i}',(.105,.10,2.45),(x,-.115,1.40),walnut,'EXTERIOR',bevel=.015)
add_box('EntranceDoor',(1.02,.10,2.28),(-1.65,-.13,1.16),blue_door,'EXTERIOR',bevel=.025)
add_box('DoorGlass',(.58,.06,.78),(-1.65,-.20,1.45),frosted_glass,'EXTERIOR',bevel=.02)
add_box('DoorHandle',(.045,.055,.42),(-1.28,-.24,1.13),brass,'EXTERIOR',bevel=.01)
add_box('FrontWindow',(2.45,.06,1.40),(1.25,-.20,1.53),frosted_glass,'EXTERIOR',bevel=.02)
add_box('WindowFrameTop',(2.62,.11,.08),(1.25,-.19,2.27),black,'EXTERIOR',bevel=.015)
add_box('WindowFrameBottom',(2.62,.11,.08),(1.25,-.19,.80),black,'EXTERIOR',bevel=.015)
for x in (.04,1.25,2.46): add_box('WindowMullion_'+str(x),(.06,.11,1.55),(x,-.19,1.53),black,'EXTERIOR',bevel=.01)
add_box('MainSignBoard',(3.45,.18,.72),(0.55,-.36,2.55),black,'EXTERIOR',bevel=.06)
add_text('MainSignText','BAR NEVATIA',(0.55,-.47,2.56),.34,.012,emissive_sign,'EXTERIOR',rot=(radians(90),0,0))
add_box('VerticalSignBoard',(.62,.18,1.65),(3.42,-.34,1.65),black,'EXTERIOR',bevel=.05)
add_text('VerticalSignText','NEVATIA',(3.42,-.45,1.65),.19,.01,emissive_sign,'EXTERIOR',rot=(radians(90),0,radians(90)))
add_box('Awning',(3.1,.85,.10),(.95,-.52,2.37),black,'EXTERIOR',rot=(radians(-6),0,0),bevel=.025)
for j,x in enumerate((2.55,3.13)):
    add_box(f'OutdoorAC_{j}',(.78,.42,.58),(x,.28,.56),whiteplastic,'EXTERIOR',bevel=.045)
    add_cyl(f'OutdoorACFan_{j}',.20,.025,(x,.055,.56),blackplastic,'EXTERIOR',rot=(radians(90),0,0),verts=32,bevel=0)
add_cyl('DrainPipe',.055,3.0,(-3.42,.02,1.50),steel,'EXTERIOR',verts=20)
add_box('MeterBox',(.32,.18,.48),(-3.15,-.18,1.03),steel,'EXTERIOR',bevel=.02)
add_box('CableDuct',(.045,.06,1.25),(-3.12,-.17,1.82),black,'EXTERIOR',bevel=.008)
add_box('Planter',(.72,.44,.42),(2.92,-.55,.23),walnut_dark,'EXTERIOR',bevel=.05)
leaf=mat_principled('Leaf',(0.045,0.16,0.055),rough=.72)
for k in range(7): add_sphere(f'PlantLeaf_{k}',.17,(2.73+(k%3)*.14,-.56,.52+(k//3)*.13),leaf,'EXTERIOR',scale=(.7,.35,1.5))
add_box('SiteAsphalt',(15.0,18.0,.12),(3.9,7.8,-.08),asphalt,'EXTERIOR',bevel=.02)
for i in range(4):
    x=4.05+i*2.55
    add_box(f'ParkingLineL_{i}',(.055,6.0,.012),(x,3.2,.005),white_line,'EXTERIOR',bevel=.002)
add_box('ParkingLineBack',(7.70,.055,.012),(7.88,6.2,.005),white_line,'EXTERIOR',bevel=.002)
for i,x in enumerate((5.35,7.90,10.45)): add_box(f'WheelStop_{i}',(1.65,.18,.16),(x,5.72,.09),concrete,'EXTERIOR',bevel=.04)
add_box('FrontWalk',(BW+1.2,1.25,.10),(0,-.75,.04),concrete,'EXTERIOR',bevel=.02)
add_box('EntranceStep',(1.40,.55,.16),(-1.65,-.42,.10),concrete,'EXTERIOR',bevel=.035)
add_box('ParkingSignPost',(.08,.08,1.65),(11.65,6.55,.83),steel,'EXTERIOR',bevel=.01)
add_box('ParkingSign',(.72,.08,.52),(11.65,6.55,1.55),blue_door,'EXTERIOR',bevel=.025)
add_text('ParkingSignText','P',(11.65,6.50,1.55),.35,.01,cream,'EXTERIOR',rot=(radians(90),0,0))

for i in range(32):
    x=-3.48+i*.218
    add_box(f'InteriorFrontSlat_{i}',(.11,.04,1.15),(x,.20,.92),walnut,'INTERIOR',bevel=.01)
add_box('BackbarMirror',(.055,4.60,1.15),(-3.48,4.55,1.65),frosted_glass,'INTERIOR',bevel=.015)
for y in (2.4,3.6,4.8,6.0):
    add_box(f'BackbarShelf_{y}',(.52,1.00,.055),(-3.15,y,1.08),walnut,'INTERIOR',bevel=.018)
    add_box(f'BackbarShelfTop_{y}',(.52,1.00,.055),(-3.15,y,1.72),walnut,'INTERIOR',bevel=.018)
for z in (1.18,1.83,2.42): add_box('Louver_'+str(z),(.11,5.3,.12),(-3.39,4.55,z),walnut,'INTERIOR',bevel=.015)
add_box('CounterGlowStrip',(3.9,.06,.05),(-.65,4.5,.57),emissive_warm,'INTERIOR',bevel=.01)
add_box('StoreDoor',(.85,.08,2.15),(-1.75,7.22,1.08),walnut_dark,'INTERIOR',bevel=.03)
add_box('WCDoor',(.82,.08,2.15),(2.55,7.22,1.08),walnut_dark,'INTERIOR',bevel=.03)
add_text('WCLabel','WC',(2.55,7.15,1.55),.12,.006,cream,'INTERIOR',rot=(radians(90),0,0))
for i,y in enumerate((2.3,4.55,6.75)):
    add_box(f'MenuFrame_{i}',(.12,.66,.90),(-3.34,y,1.80),walnut_dark,'INTERIOR',bevel=.025)
    add_box(f'MenuPaper_{i}',(.07,.56,.80),(-3.26,y,1.80),menu_paper,'INTERIOR',bevel=.006)
add_box('CoveLightHousing',(.32,5.8,.18),(-2.82,4.55,2.72),black,'INTERIOR',bevel=.03)
add_box('CoveLight',(0.08,5.2,.05),(-2.64,4.55,2.68),emissive_warm,'INTERIOR',bevel=.01)

add_box('BarCounterTop',(1.05,5.0,.14),(-1.35,4.45,1.02),walnut,'FURNITURE',bevel=.08)
add_box('BarCounterBody',(.78,4.85,.90),(-1.55,4.45,.50),walnut_dark,'FURNITURE',bevel=.04)
add_box('BarCounterFrontTop',(2.30,1.02,.14),(-.70,2.02,1.02),walnut,'FURNITURE',bevel=.08)
add_box('BarCounterFrontBody',(2.15,.78,.90),(-.70,1.85,.50),walnut_dark,'FURNITURE',bevel=.04)
stool_mat=mat_principled('SeatLeather',(0.055,0.035,0.025),rough=.38)
for i,y in enumerate((2.65,3.45,4.25,5.05,5.85,6.65)):
    add_cyl(f'StoolSeat_{i}',.28,.12,(-.58,y,.78),stool_mat,'FURNITURE',verts=32,bevel=.025)
    add_cyl(f'StoolPost_{i}',.055,.68,(-.58,y,.42),steel,'FURNITURE',verts=20,bevel=.01)
    add_cyl(f'StoolBase_{i}',.19,.035,(-.58,y,.10),steel,'FURNITURE',verts=32,bevel=.01)
for j,x in enumerate((.15,.90)):
    add_cyl(f'FrontStoolSeat_{j}',.28,.12,(x,2.88,.78),stool_mat,'FURNITURE',verts=32,bevel=.025)
    add_cyl(f'FrontStoolPost_{j}',.055,.68,(x,2.88,.42),steel,'FURNITURE',verts=20,bevel=.01)
    add_cyl(f'FrontStoolBase_{j}',.19,.035,(x,2.88,.10),steel,'FURNITURE',verts=32,bevel=.01)
for t,(x,y) in enumerate(((1.55,3.15),(1.75,4.75),(1.55,6.30))):
    add_box(f'TableTop_{t}',(1.10,.68,.08),(x,y,.74),walnut,'FURNITURE',bevel=.06)
    add_cyl(f'TableLeg_{t}',.06,.70,(x,y,.36),steel,'FURNITURE',verts=20,bevel=.01)
    add_cyl(f'TableBase_{t}',.22,.035,(x,y,.06),steel,'FURNITURE',verts=28,bevel=.01)
    for j,dx in enumerate((-.72,.72)):
        add_box(f'ChairSeat_{t}_{j}',(.44,.44,.08),(x+dx,y,.48),stool_mat,'FURNITURE',bevel=.055)
        add_box(f'ChairBack_{t}_{j}',(.08,.46,.62),(x+dx+(0.20 if dx<0 else -0.20),y,.80),walnut_dark,'FURNITURE',bevel=.035)
        for lx in (-.15,.15):
            for ly in (-.15,.15): add_cyl(f'ChairLeg_{t}_{j}_{lx}_{ly}',.025,.46,(x+dx+lx,y+ly,.24),black,'FURNITURE',verts=12,bevel=.004)
add_box('WindowBench',(2.15,.52,.12),(1.25,.52,.50),walnut,'FURNITURE',bevel=.06)
add_box('WindowBenchBase',(1.95,.42,.43),(1.25,.52,.25),walnut_dark,'FURNITURE',bevel=.04)

bottle_mats=[mat_principled('BottleAmber',(0.22,0.055,0.012),rough=.16,ior=1.48,transmission=.40,alpha=.72),mat_principled('BottleGreen',(0.015,0.12,0.045),rough=.14,ior=1.48,transmission=.42,alpha=.72),mat_principled('BottleClear',(0.38,0.48,0.50),rough=.10,ior=1.46,transmission=.68,alpha=.42),mat_principled('BottleBlue',(0.02,0.11,0.32),rough=.16,ior=1.47,transmission=.48,alpha=.70)]
idx=0
for row,z in enumerate((1.18,1.80)):
    for y in [2.15+i*.34 for i in range(15)]:
        for xoff in (0,.18):
            m=bottle_mats[idx%len(bottle_mats)]; idx+=1; x=-3.05+xoff
            add_cyl(f'BottleBody_{idx}',.065,.42,(x,y,z+.20),m,'PROPS',verts=18,bevel=.008)
            add_cyl(f'BottleNeck_{idx}',.030,.14,(x,y,z+.48),m,'PROPS',verts=16,bevel=.005)
            add_cyl(f'BottleCap_{idx}',.033,.035,(x,y,z+.56),brass if idx%3==0 else blackplastic,'PROPS',verts=16,bevel=.003)
for i,y in enumerate([2.35+i*.28 for i in range(12)]):
    add_cyl(f'GlassStem_{i}',.018,.18,(-2.72,y,2.03),clear_glass,'PROPS',verts=16,bevel=.002)
    add_cyl(f'GlassBowl_{i}',.085,.16,(-2.72,y,1.90),clear_glass,'PROPS',verts=24,bevel=.004)
add_cyl('BeerTower',.09,.86,(-2.16,3.25,1.42),brass,'PROPS',verts=28,bevel=.02)
add_cyl('BeerTowerHead',.13,.18,(-2.16,3.25,1.90),brass,'PROPS',rot=(0,radians(90),0),verts=28,bevel=.02)
add_cyl('BeerSpout',.026,.32,(-1.98,3.25,1.82),brass,'PROPS',rot=(0,radians(90),0),verts=16,bevel=.004)
add_box('SinkBase',(.70,.90,.78),(-2.55,5.45,.44),steel,'PROPS',bevel=.03)
add_box('SinkBasin',(.50,.62,.08),(-2.55,5.45,.86),blackplastic,'PROPS',bevel=.08)
add_cyl('FaucetStem',.025,.40,(-2.55,5.18,1.10),steel,'PROPS',verts=16,bevel=.004)
add_cyl('FaucetSpout',.025,.30,(-2.55,5.03,1.27),steel,'PROPS',rot=(radians(90),0,0),verts=16,bevel=.004)
add_box('IceBin',(.66,.86,.42),(-2.55,4.30,.74),steel,'PROPS',bevel=.04)
add_box('UnderCounterFridge',(.74,1.1,.84),(-2.55,6.45,.46),steel,'PROPS',bevel=.04)
add_box('FridgeDoor',(.05,.95,.70),(-2.16,6.45,.48),blackplastic,'PROPS',bevel=.025)
add_box('SoftDrinkFridge',(1.15,.72,1.86),(2.82,8.45,.96),blackplastic,'PROPS',bevel=.06)
add_box('SoftDrinkFridgeGlass',(1.00,.05,1.58),(2.82,8.06,1.00),clear_glass,'PROPS',bevel=.03)
can_green=mat_principled('CanGreen',(0.04,.30,.11),rough=.32,metal=.35)
can_mats=[red,orange,blue_door,cream,can_green]
for r,z in enumerate((.55,.90,1.25,1.60)):
    for c,x in enumerate((2.48,2.70,2.92,3.14)): add_cyl(f'DrinkCan_{r}_{c}',.055,.15,(x,8.02,z),can_mats[(r+c)%len(can_mats)],'PROPS',verts=18,bevel=.004)
add_box('SodaGunBase',(.42,.42,.18),(-.88,2.20,1.18),blackplastic,'PROPS',bevel=.04)
add_box('SodaGun',(.09,.24,.07),(-.88,2.20,1.36),blackplastic,'PROPS',rot=(0,0,radians(-18)),bevel=.025)
add_box('POSBase',(.42,.34,.10),(-.25,1.95,1.16),blackplastic,'PROPS',bevel=.04)
add_box('POSScreen',(.46,.05,.34),(-.25,2.06,1.43),blackplastic,'PROPS',rot=(radians(-12),0,0),bevel=.03)
add_box('POSDisplay',(.38,.025,.24),(-.25,2.025,1.43),blue_door,'PROPS',rot=(radians(-12),0,0),bevel=.015)
menu_texts=[['MENU','ソフトドリンク飲み放題','フライドポテト','ポテトチップス','ハチミツチップス','イブン・ガジのスパイス'],['MENU','支配血清','黄金の蜂蜜酒','落とし子の奈落','古のものポンチ','飛行するポリープゼリー']]
for mi,items in enumerate(menu_texts):
    y=3.45+mi*2.15
    add_box(f'CounterMenuFrame_{mi}',(.06,.56,.78),(-.74,y,1.48),walnut_dark,'PROPS',bevel=.025)
    add_box(f'CounterMenuPaper_{mi}',(.035,.48,.68),(-.70,y,1.48),menu_paper,'PROPS',bevel=.005)
    add_text(f'CounterMenuTitle_{mi}','MENU',(-.66,y,1.72),.085,.003,blackplastic,'PROPS',rot=(radians(90),0,radians(90)))
    for li,line in enumerate(items[1:4]): add_text(f'CounterMenuText_{mi}_{li}',line,(-.655,y,1.59-li*.13),.045,.002,blue_ink,'PROPS',rot=(radians(90),0,radians(90)),align='CENTER')
for i,y in enumerate((3.9,5.9)):
    add_cyl(f'PumpBottle_{i}',.07,.38,(-.60,y,1.22),softpink,'PROPS',verts=20,bevel=.015)
    add_cyl(f'PumpHead_{i}',.025,.15,(-.60,y,1.48),whiteplastic,'PROPS',verts=12,bevel=.004)
    add_box(f'PumpNozzle_{i}',(.13,.035,.035),(-.54,y,1.53),whiteplastic,'PROPS',bevel=.008)
add_box('NapkinHolder',(.18,.23,.28),(-.68,6.55,1.22),whiteplastic,'PROPS',bevel=.025)
add_box('RedStorageBin',(.75,.65,.48),(-2.45,2.45,1.29),red,'PROPS',bevel=.06)
for i in range(10):
    y=2.9+i*.38
    add_cyl(f'Coaster_{i}',.09,.008,(-.87,y,1.10),blackplastic,'PROPS',verts=32,bevel=.001)
for i,y in enumerate((2.3,4.55,6.75)): add_text(f'WallMenuTitle_{i}','MENU',(-3.18,y,2.05),.11,.004,blackplastic,'PROPS',rot=(radians(90),0,radians(90)))
add_box('ExteriorMenuBoard',(.08,.72,1.08),(2.35,-.70,.63),blackplastic,'PROPS',rot=(0,0,radians(-4)),bevel=.03)
add_text('ExteriorMenuText','WHISKY  COCKTAIL  COLA',(2.29,-.71,.76),.055,.004,cream,'PROPS',rot=(radians(90),0,radians(90)))
add_box('EntranceMat',(1.20,.75,.025),(-1.65,-.88,.09),blackplastic,'PROPS',bevel=.015)

scene.world.use_nodes=True
wn=scene.world.node_tree.nodes
bg=wn.get('Background'); bg.inputs['Color'].default_value=(0.015,0.020,0.030,1); bg.inputs['Strength'].default_value=.28
for i,y in enumerate((2.65,4.5,6.35)):
    add_point(f'PendantBulb_{i}',(-.45,y,2.50),95,(1.0,.45,.18),.10)
    add_cyl(f'PendantShade_{i}',.20,.42,(-.45,y,2.50),frosted_glass,'LIGHTING',verts=32,bevel=.01)
    add_cyl(f'PendantCord_{i}',.012,.50,(-.45,y,2.95),black,'LIGHTING',verts=10,bevel=.002)
add_area('InteriorFill',(1.1,4.7,2.72),500,(1.0,.55,.28),4.5,rot=(0,0,0))
add_area('BackbarWash',(-2.8,4.6,2.25),420,(1.0,.30,.10),4.0,rot=(0,radians(90),0))
for x in (-2.85,2.75): add_point('ExteriorLamp_'+str(x),(x,-.40,2.28),160,(1.0,.40,.12),.16)
add_area('ParkingFill',(7.0,3.0,7.5),950,(.33,.46,.70),8.0,rot=(0,0,0))
add_area('FacadeFill',(0,-5.0,5.2),650,(.55,.63,.80),6.0,rot=(radians(58),0,0))
add_point('SignGlow',(0.6,-.72,2.55),110,(1.0,.30,.06),.12)

cams={
    'EXTERIOR_FRONT': add_camera('Cam_ExteriorFront',(0,-11,3.6),(0,1.4,1.4),45),
    'EXTERIOR_OBLIQUE': add_camera('Cam_ExteriorOblique',(11,-10,5.2),(1.4,2.2,1.2),42),
    'INTERIOR_COUNTER': add_camera('Cam_InteriorCounter',(2.9,1.2,1.75),(-1.75,4.8,1.35),34),
    'INTERIOR_WIDE': add_camera('Cam_InteriorWide',(2.9,6.9,2.05),(-1.4,3.8,1.25),31),
    'TOP_PLAN': add_camera('Cam_Top',(0,4.55,14.5),(0,4.55,0),48),
}
scene['design_basis']='910mm Japanese shaku module; 8x10 modules = 7.28m x 9.10m'
scene['parking_basis']='3 stalls nominal 2.5m x 6.0m class; visual study only'
scene['reference_policy']='User reference images guide mood/props only; no exact venue copy.'
scene['shader_policy']='Blender Principled/OpenPBR-like values with custom working presets.'

for mod in ['SHELL','EXTERIOR','INTERIOR','FURNITURE','PROPS']:
    try:
        p=export_module(mod, f'BAR_NEVATIA_MODULE_{mod}_{REV}.glb')
        log(f'exported {p.name}')
    except Exception as e:
        log(f'module export failed {mod}: {e}')

blend_path=OUT/'models'/f'BAR_NEVATIA_ASSEMBLED_{REV}.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

def scene_stats():
    meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.get('bar_nevatia')]
    curves=[o for o in bpy.data.objects if o.type in {'CURVE','FONT'} and o.get('bar_nevatia')]
    mats=set(); verts=0; polys=0; issues=[]
    for o in meshes:
        verts+=len(o.data.vertices); polys+=len(o.data.polygons)
        for m in o.data.materials:
            if m: mats.add(m.name)
        vals=list(o.location)+list(o.scale)+list(o.rotation_euler)
        if any(not math.isfinite(v) for v in vals): issues.append(f'NONFINITE:{o.name}')
        if min(abs(s) for s in o.scale)<1e-6: issues.append(f'ZERO_SCALE:{o.name}')
        if len(o.data.polygons)==0: issues.append(f'EMPTY_MESH:{o.name}')
    return {'mesh_count':len(meshes),'curve_text_count':len(curves),'vertices':verts,'polygons':polys,'materials':len(mats),'issues':issues}

def render_metrics(cam_key, round_i):
    set_camera(cams[cam_key])
    scene.render.resolution_x=720; scene.render.resolution_y=480; scene.render.resolution_percentage=100
    path=OUT/'renders'/f'QA{round_i:02d}_{cam_key}.png'
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    img=bpy.data.images.get('Render Result')
    px=img.pixels[:]
    lum=[]
    for i in range(0,len(px)-3,4*64):
        r,g,b=px[i],px[i+1],px[i+2]
        lum.append(.2126*r+.7152*g+.0722*b)
    mean=sum(lum)/max(1,len(lum)); black=sum(v<.025 for v in lum)/max(1,len(lum)); white=sum(v>.96 for v in lum)/max(1,len(lum))
    return {'path':str(path.relative_to(OUT)),'mean_luminance':round(mean,4),'black_ratio':round(black,4),'white_ratio':round(white,4)}

qa=[]
for q in range(1,11):
    stats=scene_stats(); ext=render_metrics('EXTERIOR_OBLIQUE',q); interior=render_metrics('INTERIOR_COUNTER',q); changes=[]
    m=(ext['mean_luminance']+interior['mean_luminance'])/2; br=max(ext['black_ratio'],interior['black_ratio']); wr=max(ext['white_ratio'],interior['white_ratio'])
    if m<.10 or br>.62:
        scene.view_settings.exposure += .30; changes.append('EXPOSURE_UP_0.30')
    elif m>.46 or wr>.12:
        scene.view_settings.exposure -= .22; changes.append('EXPOSURE_DOWN_0.22')
    fill=bpy.data.lights.get('InteriorFill')
    if interior['mean_luminance']<.12 and fill:
        fill.energy*=1.18; changes.append('INTERIOR_FILL_UP_18PCT')
    elif interior['white_ratio']>.10 and fill:
        fill.energy*=.88; changes.append('INTERIOR_FILL_DOWN_12PCT')
    geom_ok=(stats['mesh_count']>=150 and stats['materials']>=16 and len(stats['issues'])==0)
    image_ok=(.10<=m<=.46 and br<.62 and wr<.12)
    qa.append({'round':q,'geometry':stats,'exterior':ext,'interior':interior,'changes':changes,'geometry_ok':geom_ok,'image_ok':image_ok,'exposure':scene.view_settings.exposure})
    log(f'QA {q}: geom={geom_ok} image={image_ok} mean={m:.3f} changes={changes}')
    if geom_ok and image_ok and q>=3: break

scene.render.resolution_x=1280; scene.render.resolution_y=850
for key in ('EXTERIOR_FRONT','EXTERIOR_OBLIQUE','INTERIOR_COUNTER','INTERIOR_WIDE','TOP_PLAN'):
    set_camera(cams[key]); scene.render.filepath=str(OUT/'renders'/f'FINAL_{key}.png'); bpy.ops.render.render(write_still=True)

final_glb=export_final()
final_blend=OUT/'models'/f'BAR_NEVATIA_FINAL_{REV}.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(final_blend))

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

final_stats=scene_stats(); files=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file(): files.append({'path':str(p.relative_to(OUT)),'size':p.stat().st_size,'sha256':sha256(p)})
manifest={'schema':'bar_nevatia_quality_v1','revision':REV,'status':'PASS' if final_stats['mesh_count']>=150 and not final_stats['issues'] else 'WARN','design':{'building_m':[BW,BD,CEIL],'module_m':.91,'seating':{'counter_stools':8,'table_seats':6,'window_bench':2},'parking_stalls':3,'modules':['SHELL','EXTERIOR','INTERIOR','FURNITURE','PROPS','LIGHTING'],'reference_mood':'dark walnut, frosted/clear glass, warm pendant lights, menu frames, backbar bottles, soda/beer equipment'},'shader_presets':{'walnut':{'roughness':[.48,.62],'metallic':0},'black_metal':{'roughness':.36,'metallic':.80},'steel':{'roughness':.33,'metallic':.92},'brass':{'roughness':.27,'metallic':1.0},'glass':{'ior':1.45,'roughness':[.08,.32],'transmission':[.75,1.0]},'plaster':{'roughness':.86},'lighting':'2700K-like warm RGB + cool parking fill'},'qa_rounds':qa,'final_stats':final_stats,'final_glb':str(final_glb.relative_to(OUT)),'final_blend':str(final_blend.relative_to(OUT)),'files':files,'limitations':['Visual/concept model, not construction documents or code compliance verification.','Parking geometry uses guideline-class visual dimensions, not a site survey.','User reference images were used only as mood/prop references.']}
(OUT/'reports'/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
report=f'''# BAR NEVATIA Quality Build Report\n\nStatus: {manifest['status']}\n\n## Design\n- Japanese residential 910mm grid: 8 x 10 modules = 7.28m x 9.10m.\n- Counter seats 8, table seats 6, window bench 2.\n- 3 parking stalls on the east side.\n- Modular exports: SHELL / EXTERIOR / INTERIOR / FURNITURE / PROPS + final combined GLB.\n- Exterior: dark wood residential-bar facade, blue entrance door, frosted window, illuminated BAR NEVATIA sign, AC units, meter, drainpipe, planter, parking markings.\n- Interior: long counter + table seating, backbar, mirrors/frosted panels, menu frames, pendant lights, bottle shelves, soda/beer/ice/sink/POS/fridge props.\n\n## QA\n- Automatic geometry/material QA + render luminance QA.\n- Rounds used: {len(qa)} / 10.\n- Final mesh objects: {final_stats['mesh_count']}; vertices: {final_stats['vertices']}; materials: {final_stats['materials']}.\n- Remaining machine issues: {final_stats['issues']}\n\n## Safety / scope\n- This is a visual 3D design study, not a building-code, fire-code, liquor-license, accessibility, structural or parking-compliance plan.\n'''
(OUT/'reports'/'REPORT.md').write_text(report,encoding='utf-8')
(OUT/'reports'/'ERROR_REPORT.json').write_text(json.dumps({'errors':[],'qa_warnings':[r for r in qa if not (r['geometry_ok'] and r['image_ok'])]},ensure_ascii=False,indent=2),encoding='utf-8')
log(json.dumps({'status':manifest['status'],'out':str(OUT),'qa_rounds':len(qa),'final_stats':final_stats},ensure_ascii=False))
