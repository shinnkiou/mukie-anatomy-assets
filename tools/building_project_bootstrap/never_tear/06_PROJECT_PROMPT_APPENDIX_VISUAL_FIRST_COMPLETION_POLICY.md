# PROJECT PROMPT APPENDIX — VISUAL-FIRST COMPLETION POLICY

This file mirrors the 2026-09-07 Drive project prompt addendum.

## Highest-level rule
For 3D buildings, environments, sets, backgrounds, and other visual deliverables in NEVER TEAR Building Factory:

`FINAL_COMPLETE = PROCESS_COMPLETE AND VISUAL_COMPLETE`

`PROCESS_COMPLETE` means design/implementation/technical QA/save/readback/recovery/next_action are complete.

`VISUAL_COMPLETE` means the actual model is rendered/displayed in Base44/Blender and visually works as the requested finished deliverable.

Priority:
1. User-visible visual result
2. Structural / functional correctness
3. Runtime correctness
4. Persistence / readback
5. Management metadata

A failure at a higher level blocks COMPLETE.

## Proxy separation
QA proxy, blockout, collision and performance meshes must be explicitly labeled `QA PROXY`, `BLOCKOUT`, or `NON-CANONICAL`. They are never the finished user-facing building.

## Surface completion
Material-family assignment is `MATERIAL_BINDING_PASS`, not PBR Surface completion.

PBR visual completion requires visible material differentiation, UV/projection, appropriate BaseColor/Roughness/Normal-Bump/Metallic/AO, weathering/dust/dirt, decals/signage and screenshot inspection.

## Visual completion gate
Require:
- credible architecture/silhouette
- medium-detail environment density (pipes, ducts, cables, supports, rails, lights, panels, racks, machinery, doors)
- no sparse-box look
- material differences visible on screen
- dust/rust/soot/grime/burn/damage/signage as appropriate
- believable lighting
- minimum 3, recommended 5 visual QA shots
- Blender export QA
- Base44/Blender consistency
- USER_VISUAL_QA_PASS

User screenshot dissatisfaction = USER_VISUAL_QA_FAIL and overrides build/numeric QA passes.

## Hero-area strategy
For large facilities, finish one hero area completely, then reuse its quality standard:
`Structure final -> detail geometry -> UV/material -> PBR -> dirt/damage -> decals -> lighting -> camera -> screenshot -> Blender check`

## Runner allocation
Normal production runner should prioritize actual art production:
0-2 READ STATE / 2-18 MAKE-MODEL-TEXTURE / 18-22 VISUAL QA / 22-24 FIX / 24-25 SAVE-next_action.
Move heavy cross-service synchronization to Daily Sync where possible.

## QA naming
Prefer specific gates:
`STRUCTURE_QA_PASS`, `MATERIAL_BINDING_PASS`, `PBR_VISUAL_QA_PASS`, `RUNTIME_QA_PASS`, `EXPORT_QA_PASS`, `USER_VISUAL_QA_PASS`.

## Historical correction
Do not erase earlier process-complete history when visual quality later fails. Create a remediation task. Mars Branch NT-BLD-001..020 remain historical workflow COMPLETE; NT-BLD-021 remains ACTIVE visual remediation until the user-visible model passes.

## Standard visual work unit
`Research -> Implement -> VISUAL INSPECT -> Fix -> Technical QA -> Save -> Readback -> Update next_action`
