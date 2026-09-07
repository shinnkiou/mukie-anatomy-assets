# NEVER TEAR Visual Completion Rules & Lessons

Updated: 2026-09-07 JST

## Lesson learned
The Mars Branch reached strong process/QA/sync maturity before the user-visible model reached the expected visual quality. The main failure mode was treating technical correctness and persistence as equivalent to a finished visual asset.

## Visual-first completion policy
For visual deliverables:

`FINAL_COMPLETE = PROCESS_COMPLETE && VISUAL_COMPLETE`

Priority order:
1. user-visible visual result
2. structural/functional correctness
3. runtime correctness
4. persistence/readback
5. management metadata

A failure in a higher level blocks COMPLETE even if lower levels pass.

## Process vs visual completion
- `PROCESS_COMPLETE`: design, implementation, technical QA, save, readback, restore point, next_action are complete.
- `VISUAL_COMPLETE`: actual model is shown in Base44/Blender and visually works as the intended deliverable.

## Proxy policy
QA proxy/blockout/collision/performance meshes are not deliverables. Label them `QA PROXY`, `BLOCKOUT`, or `NON-CANONICAL` in UI/files/logs. Never present a proxy as the finished building.

## Surface terminology
Material assignment alone is `MATERIAL_BINDING_PASS`, not Surface completion.

`PBR_VISUAL_QA_PASS` requires, as appropriate:
- visible material differentiation
- UV or appropriate projection
- BaseColor / Roughness / Normal-Bump / Metallic / AO
- dust/dirt/weathering/wear
- decals/signage
- screenshot inspection

## 3D visual completion gate
A completed building/environment should have:
- strong macro silhouette and architecture
- medium detail: pipes, ducts, cable trays, beams, supports, rails, lights, panels, racks, machinery, door detail
- no sparse-box look
- visible material differences
- environmental storytelling: dust, rust, soot, grime, burn, damage, signs
- useful lighting
- minimum 3, recommended 5 QA shots
- Blender export without scale/orientation/material failure
- Base44 and Blender materially consistent
- `USER_VISUAL_QA_PASS`

A user screenshot expressing doubt or dissatisfaction is a `USER_VISUAL_QA_FAIL` and overrides numeric/build PASS results.

## Animation-background quality
When the goal is animation/background/3D layout use, require at minimum:
- camera-ready environment density
- acceptable small-to-medium distance appearance
- major surfaces and equipment not represented only by primitive boxes
- believable PBR response
- modular/editable structure

## Hero-area method
Finish one important area to target quality before spreading effort across the entire large facility.

Recommended order:
1. central corridor + blast junction
2. hangar
3. landing/exterior utilities
4. command/comms
5. remaining modules

Per hero area:
`Structure final -> detail geometry -> UV/material -> PBR -> dirt/damage -> decals -> lighting -> camera -> screenshot -> Blender check`

## Runner allocation
Normal production runner:
- 0-2 min READ STATE
- 2-18 min MAKE / MODEL / TEXTURE
- 18-22 min VISUAL QA
- 22-24 min FIX
- 24-25 min SAVE / next_action

Heavy multi-service synchronization should normally be moved to Daily Sync so production runners are not consumed by management overhead.

## QA naming
Use specific names where helpful:
- STRUCTURE_QA_PASS
- MATERIAL_BINDING_PASS
- PBR_VISUAL_QA_PASS
- RUNTIME_QA_PASS
- EXPORT_QA_PASS
- USER_VISUAL_QA_PASS

Do not hide multiple quality levels behind a single vague `Surface PASS`.

## Image-generation / Adobe lesson
Generated images are references or texture sources, not implementation completion. AI-generated text is not canonical signage; deterministic SVG/JSON text should remain canonical.

## Historical correction policy
If a task was previously marked process-complete but visual completion later fails, do not rewrite history. Add a remediation task and keep the original technical history. For Mars Branch: NT-BLD-001..020 remain historical workflow COMPLETE; NT-BLD-021 is the visual remediation task.

## Standard visual work unit
`Research -> Implement -> VISUAL INSPECT -> Fix -> Technical QA -> Save -> Readback -> Update next_action`
