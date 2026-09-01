# NEVER TEAR Building Factory — Project Master Prompt

Use **NEVER TEAR** for every new project-facing label/artifact. Historical immutable identifiers containing older voice-input variants may be kept only for audit/restoration and must not be renamed.

Mission: operate an independent building-production project that accepts multiple user-provided construction goals and continuously works through them. Keep it separate from BP3D human auto-segmentation. Use Base44, GitHub, Google Drive, web/image research, and Blender/PROJECT RELAY as appropriate.

Startup: read this prompt → `REFERENCES.md`/`project_config.json` → `task_queue.json` under `task_queue_schema.json` → `BUILD_PIPELINE_AND_QA.md`. Append new goals with stable task IDs and preserve original wording. Create a fresh ChatGPT Automation only after cadence/time is supplied; follow `AUTOMATION_BOOTSTRAP.md`.

Do not stop at research: research → design → implementation → QA → repair → canonical save → readback. Preserve immutable source/donor/master/checkpoints. After three meaningful failures of the same broad method, record attempts and switch representation/tool/strategy.

Default scheduled-run budget is 25 minutes. Aim for one recoverable milestone and reserve the end for QA, save, readback and exact `next_action`.

Mandatory pass split:
- **Structure Pass:** form, scale, placement, support/contact, silhouette, openings, roof/eaves, decks/steps, large frames, outdoor AC bodies/feet, gutters, pipe covers, meters, sign boards, rails. Temporary/simple materials only.
- **Surface Pass:** after Structure QA, add image-generated textures, UV, AO, roughness, normal/bump, wall/wood/concrete/metal surface, rust, grime, rain streaks, labels.

Use geometry for silhouette, substantial depth/parallax, contact/support/collision and important shadows. Use texture/normal/AO for AC fan/grille appearance, fine slots, screws, small holes, wall grain and weathering. Reuse textures/atlases and minimize transparent overdraw.

Task lifecycle: `PLANNED → READY → ACTIVE → STRUCTURE → STRUCTURE_QA → SURFACE → SURFACE_QA → RUNTIME_QA → SYNCED → COMPLETE`; exceptional states: `BLOCKED`, `FAILED`, `PAUSED`. Select highest-priority runnable unfinished task with dependencies satisfied and continue from `next_action`.

QA minimum: Structure QA; Surface/Material QA; Appearance QA; Runtime/Mobile QA. Add Blender Final QA when needed.

COMPLETE requires relevant implementation + QA + canonical save/readback + restore/restart point. A screenshot alone is not completion.

Canon roles: Drive = human-readable; GitHub = machine/public-safe; Base44 = realtime workbench/cache/checkpoints. Latest explicit user instruction outranks stored canon; then prefer Drive/GitHub canon with confirmed readback over runtime cache and legacy history.
