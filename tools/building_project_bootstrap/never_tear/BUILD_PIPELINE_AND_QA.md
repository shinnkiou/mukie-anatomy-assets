# NEVER TEAR Building Factory — Build Pipeline and QA

## 0 Reference / rights
Preserve exact user requests/references. Prefer CC0/public-domain/project-owned donors, record source/license/hash where possible, and keep donor files immutable.

## A Structure Pass
Build geometry needed for silhouette, scale, placement, contact and support: shell, roof/eaves, openings, awnings, decks/steps, frames, outdoor AC bodies/feet, gutters/downspouts, important conduits/pipe covers, meters, signs, fences/rails. Use simple temporary materials.

### Structure QA
Check ground/wall contact, floating elements, penetration, support, openings, rear/sides, scale, duplicates, transforms and content-only camera framing. Floating bars/pipes/service hardware must be fixed here.

## B Surface Pass
Only after Structure QA. Use geometry for silhouette, significant depth/parallax, support/contact/collision and important shadows. Use texture/normal/AO for AC fan/grille appearance, fine slots, screws, wall grain, concrete/wood/metal surface, rust, dirt, rain streaks and labels.

Prefer reusable BaseColor/Roughness/Normal-or-bump/AO families and texture atlases. Keep source-resolution and runtime-compressed assets separate. Minimize alpha/transparent overdraw.

### Outdoor AC realtime standard
Low-poly body + simple feet + optional shallow front rim; fan/grille/propeller via front texture/detail plane; side slots via texture/normal unless silhouette matters; important drain/pipe paths as simple geometry; contact depth from lighting/AO rather than dense grille geometry.

### Surface QA
Check UV scale/orientation, missing textures, stretching, normal direction, roughness/metal plausibility, AO, tiling, z-fighting, resolution and mobile memory.

## Appearance QA
Review front, rear, both sides, elevated/three-quarter and utility/service side. Check intended style, material hierarchy, restrained rust/dirt/AO, repetition and physically attached service equipment.

## Runtime/Mobile QA
Base44/Three.js lightweight baseline: build, page/WebGL, preset render, content-only framing, fog/near/far, mobile lower-cost path, page/console errors, context-lost handling, resize, no duplicate/runaway resources, import/export when relevant.

## Optional Blender final pass
Export lightweight GLB/OBJ → Blender high-quality material/UV/shader/light/bake/render → QA. Keep realtime and final-quality revisions separately.

## Canon / completion
Save meaningful milestones to Base44 checkpoint, GitHub machine/public-safe canon and Drive human canon. Read every save back. COMPLETE requires relevant implementation + QA + canonical readback + restore/restart point.

After three meaningful failures of the same broad method, document attempts and switch representation/tool/strategy.
