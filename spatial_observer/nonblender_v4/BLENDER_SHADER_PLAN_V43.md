# BP3D v4.3 Blender 4.2 practical display plan

## Goal

Use the derived v4.3 muscle split in Blender without making Blender a semantic/anatomical authority and without writing MASTER, R7, Production14, or Production13.

## Recommended geometry import

- Default: `side_splits/` = 112 objects (56 Detail labels x L/R).
- Alternate: `shell_splits/` = 128 objects when one Blender object must equal one connected mesh shell.
- Candidate overlays are review-only and must not replace canonical ownership.

## Collections and View Layers

Use Collections/View Layers for selection, visibility, isolation and photography. Suggested hierarchy is side x evidence state:

- L / R
- REVIEWED
- ESTABLISHED_OR_PARENT
- CONTEXT
- HYPOTHESIS

Collection membership is not treated as the shader's semantic muscle selector.

## Shader Editor

Use four shared materials rather than 112 independent material trees:

- `BP3D_MAT_REVIEWED`
- `BP3D_MAT_ESTABLISHED_OR_PARENT`
- `BP3D_MAT_CONTEXT`
- `BP3D_MAT_HYPOTHESIS`

Each object stores:

- `bp3d_label`
- `bp3d_side`
- `bp3d_confidence`
- `bp3d_evidence_code`
- `bp3d_color`

The Blender 4.2 Shader Attribute node is set to Object and reads `bp3d_color`, feeding Principled BSDF Base Color. Thus the shader tree is shared while color remains object-specific.

## Display modes

`BP3D_SWITCH_DISPLAY_MODE_V43.py` changes `bp3d_color` to support:

- ADJACENCY: five-color graph coloring, zero same-color touching Detail pairs.
- EVIDENCE: evidence-state inspection.
- CONFIDENCE: project confidence visualization.

Object/Outliner names remain the semantic identity; color is deliberately optimized for visual discrimination rather than one permanent unique color per muscle.

## Evidence caveats

The four head HYPOTHESIS labels remain uncertainty-marked. In particular, the current temporalis surface selection is interpreted only as a seed region, not the full fan-shaped temporalis extent. Deep structures such as rotator cuff are context and should not be converted into artificial skin-surface parts.

## Source safety

All scripts operate on derived OBJ imports. Source writes: MASTER=0, R7=0, Production14=0. Production13 remains permanently forbidden.
