import bpy

# BP3D BODY/TORSO fail-closed render guard.
# Visual-layer only: no canonical Face ownership or source mesh mutation.
ALLOWED_LABELS = {
    'TRAPEZIUS_UPPER','PECTORALIS_MAJOR','LATISSIMUS_DORSI',
    'RECTUS_ABDOMINIS','OBLIQUE','THORACOLUMBAR_FASCIA_CONTEXT',
    'PELVIS_FRONT_CONTEXT','GLUTEUS_MAXIMUS','GLUTEUS_MEDIUS'
}
REVIEW_ONLY = {'SERRATUS_ANTERIOR','INFRASPINATUS','TERES_MAJOR'}

body = bpy.data.collections.get('BP3D_DEADLINE_THIGH_PELVIS_TORSO_V02')
if body is None:
    raise RuntimeError('TORSO guard: V02 body collection missing')

visible=[]
hidden=[]
unknown=[]
for o in body.all_objects:
    if o.type != 'MESH':
        continue
    label=o.get('bp3d_label')
    if label in ALLOWED_LABELS:
        o.hide_render=False; o.hide_viewport=False; visible.append((o.name,label))
    else:
        o.hide_render=True; o.hide_viewport=True; hidden.append((o.name,label))
        if label not in REVIEW_ONLY:
            unknown.append((o.name,label))

# Other specialized overlays must not render in torso-isolated QA.
for cname in ['BP3D_DEADLINE_ARM_V02','BP3D_DEADLINE_FOOT_LOWERLEG_V02','BP3D_DEADLINE_NEUTRAL_BASE_V02']:
    c=bpy.data.collections.get(cname)
    if c:
        c.hide_render=True; c.hide_viewport=True

# Boundaries are allowed only as derived internal-boundary display.
bound=bpy.data.collections.get('BP3D_DEADLINE_BOUNDARIES_V02')
if bound:
    bound.hide_render=False; bound.hide_viewport=False

bpy.context.scene['bp3d_deadline_mode']='TORSO_ISOLATED_GUARDED_V01'
bpy.context.scene['bp3d_torso_allowed_label_count']=len(ALLOWED_LABELS)
bpy.context.scene['bp3d_torso_visible_mesh_count']=len(visible)
bpy.context.scene['bp3d_torso_hidden_mesh_count']=len(hidden)
bpy.context.scene['bp3d_canonical_face_change']=0
bpy.context.scene['bp3d_external_author_pixel_use']=0
bpy.context.scene['bp3d_anatomical_front']='NEGATIVE_Y'

# Fail closed if anything visible is outside the allowlist.
violations=[]
for o in body.all_objects:
    if o.type=='MESH' and not o.hide_render and o.get('bp3d_label') not in ALLOWED_LABELS:
        violations.append((o.name,o.get('bp3d_label')))
if violations:
    raise RuntimeError('TORSO isolation violation: '+repr(violations))

print('BP3D_TORSO_ISOLATION_GUARD_PASS', {'visible':len(visible),'hidden':len(hidden),'unknown_hidden':len(unknown)})
