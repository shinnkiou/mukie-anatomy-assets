# NEVER TEAR Building Factory — Next Chat Handoff / Visual Recovery

Updated: 2026-09-07 JST

## Formal state
- NT-BLD-001..020: **historical workflow COMPLETE** (design/spec/implementation/technical QA/sync history preserved)
- NT-BLD-021: **ACTIVE / visual deliverable remediation**
- Linear: `RIO-41`

Do not equate administrative/process completion with a finished visual deliverable.

## User expectation
The Mars Branch should open in Base44/Blender as a believable Mars industrial base with visible texture/material differences, dust, soot, burn, rust, decals, pipes/ducts/cables/lights/equipment, believable damage and sufficient environment density to be useful as an animation background / 3D layout asset.

Boxes, QA proxies, material-tag assignment and simple floor-plan views are not a finished asset.

## Current Base44 recovery
App: Creative Ops Lab
App ID: `6a2ae58cc6b153727abb83f1`
Route: `/ai-3d-model-lab`

Current implementation:
- `src/lib/3d/neverTearMarsFullBuild.js`
- version `2026-09-07-r1`
- UI: `Mars Full Build` = user inspection target
- UI: `Mars QA Proxy` = old 24-mesh runtime proxy, never call it the finished model

Checkpoint: `6a9ec01582f38c50f3b79d71`
Commit: `f13a7faf647235fe5717ec8afca1529b142185df`

## Recovered structural source
WalkMyPlan plan: `aacb32598eb746758d60c8`
Structure lock: **50 walls / 26 openings / 87 fixtures / 14 rooms**.

Recovered:
- 50 walls + 26 openings from WalkMyPlan revision-family around rev230
- fixture 0-73 from revision-family around rev350
- fixture 74-82 from NT-BLD-013 canon
- fixture 83-86 damage proxies are currently approximate; never pretend they are exact source geometry

## Current technical QA for Mars Full Build r1
- 234 render meshes
- 50/50 walls
- 26/26 openings
- 87/87 fixtures
- 14 rooms
- material binding 234/234
- missing module/material family = 0
- geometryMutation = false
- production Vite build PASS

This is **technical/structural QA only**, not animation-background visual quality.

## Next chat startup
1. Read Drive `00`, `04`, `05`, `06`.
2. Read Base44 `runtime_state.json` and `task_queue.json`.
3. Read Linear `RIO-41`.
4. Keep WalkMyPlan structure locked unless a real visual/structural fix requires editing it.
5. Treat user screenshots from Base44/Blender as highest-priority QA input.
6. If the result looks weak, spend the runner on modeling/PBR/lighting rather than more management work.
7. Keep NT-BLD-021 ACTIVE until user-facing visual QA passes.

## Hero-area order
1. Central corridor + blast damage junction
2. Hangar
3. Exterior landing/service/fuel/antenna
4. Command/comms
5. Remaining modules

Each hero area must go through:
`Structure final -> detail geometry -> UV/material -> PBR -> dirt/damage -> decals -> lighting -> camera -> screenshot -> Blender check`

## Completion gate for NT-BLD-021
Do not mark COMPLETE until:
- Base44 shows the actual `Mars Full Build` and user can inspect it
- Blender GLB opens with materially equivalent result
- minimum 3, recommended 5 visual QA shots
- central corridor, hangar, landing/exterior and blast area are visually credible
- material/texture differences are visible in screenshots
- major equipment does not read as a sparse collection of boxes
- USER_VISUAL_QA_PASS
- save/readback to Drive/GitHub/Base44/Linear/Supabase

## Exact next_action
`Base44 Mars Full Build or Blender Full Build GLB user visual inspection -> list visible defects -> finish one hero area through real modeling/PBR/lighting -> visual QA -> save/readback; keep NT-BLD-021 ACTIVE until user visual PASS.`
