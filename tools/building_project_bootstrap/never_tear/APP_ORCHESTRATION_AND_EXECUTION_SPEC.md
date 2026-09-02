# NEVER TEAR Building Factory — App Orchestration & Execution Spec

Canonical name: NEVER TEAR
Canonical project key: `never_tear_buildings`
Canonical branch: `never-tear-building-bootstrap-20260902`

## 1. Principle

Do not touch every service on every run. Use one orchestration loop and route each step to the minimum app set required for that task. The unit of work is:

`READ STATE -> SELECT TASK -> WORK -> QA -> SAVE -> READBACK -> UPDATE next_action`

A task is not COMPLETE until relevant QA, durable save, and readback pass.

## 2. System of record by responsibility

- Google Drive / Docs: human-readable canon, decisions, reference packs, QA reports, handoff/recovery notes.
- GitHub: machine-readable canon, schemas, queue JSON, code, QA rules, reproducible configuration, public-safe artifacts.
- Base44 Creative Ops Lab: active execution cache, preview/runtime state, checkpoints, model jobs, fast operator UI.
- Linear: NT-BLD issue/task lifecycle, priority, dependency, blocker, owner/status mirror.
- Supabase: append-oriented run history, artifact metadata, task queue mirror, metrics, status and next_action for reliable query/readback.
- Notion: project wiki/decision log/how-to mirror; never outranks Drive/GitHub canon.
- Vercel: preview deployments and browser/runtime verification for web viewers and Three.js/Base44-adjacent frontends.
- Miro: spatial planning, module/dependency maps, adjacency and facility-flow diagrams when visual planning is materially useful.
- WalkMyPlan — Floor Plans in 3D: rapid floor-plan / room-layout exploration before detailed structure modeling.
- to3D: convert suitable 2D concept/reference images into rough 3D donor/reference assets; outputs are references, not automatic canon.
- Adobe / Adobe Express: texture atlases, decals, signage, image cleanup, presentation/reference boards, social/export variants when needed.
- Adobe Acrobat: PDF reference extraction, page organization, redaction, comparison, and archival QA.
- Gmail: project-input monitoring only when a message/attachment is an explicit dependency; no external send without separate user confirmation.
- Google Calendar: milestone/deadline awareness and non-destructive scheduling context; ChatGPT Automations remains the production runner.
- ChatGPT Automations: queue runner and synchronization scheduler.

## 3. App routing by phase

### REFERENCE
Primary: Drive, Acrobat, Miro, Notion.
Conditional: Gmail for required inbound references; WalkMyPlan for floor-plan studies; to3D for rough donor geometry.
Outputs: provenance, rights, dimensions, reference pack, task-ready acceptance criteria.

### STRUCTURE
Primary: Base44 + GitHub.
Conditional: WalkMyPlan, to3D, Miro.
Store geometry-critical decisions in Drive and machine parameters in GitHub. Do not begin Surface before Structure QA passes.

### STRUCTURE_QA
Primary: Base44, Vercel/browser preview, GitHub QA definitions.
Mirror status to Linear and run metrics to Supabase.
Acceptance examples: silhouette/scale correct, no floating parts, required doors/windows/equipment exist, intersections/contact pass, desktop/mobile preview renders.

### SURFACE
Primary: Adobe/Adobe Express + Base44.
Use BaseColor/albedo, AO, Roughness, Normal/Bump, Metallic only where applicable, rust, soot, dirt, decals and reusable atlases. Prefer texture/Normal/AO for fan grilles, screws, fine slots, wall grain and microdetail instead of geometry.

### SURFACE_QA
Primary: Base44 + Vercel/browser QA.
Check assignment, tiling, seams, scale, material response, readability at target distance, mobile cost.

### RUNTIME_QA
Primary: Vercel + Base44.
Record runtime/console/visual/mobile results in Supabase and Linear. GitHub contains reproducible configuration and QA scripts/specs.

### SYNCED / COMPLETE
Drive human report + GitHub machine canon + Base44 checkpoint + Linear status + Supabase run/artifact rows must agree on `task_id`, status and `next_action`. Notion is updated only as a secondary knowledge mirror.

## 4. 25-minute runner contract

- 0-3 min: read canon / queue / last run / blockers.
- 3-17 min: execute one bounded work milestone.
- 17-21 min: QA.
- 21-24 min: fix or freeze artifact.
- 24-25 min: durable save, readback, exact restart point.

Queue priority:
`BLOCKED-unblocking > QA-fix > ACTIVE continuation > HIGH/URGENT runnable > NORMAL/LOW runnable`.
Keep the same building through Structure QA unless blocked.

## 5. NT-BLD task contract

Each task requires at least:
`task_id, title, building_name, original_request, goal, priority, dependencies, phase_scope, time_budget_minutes, references, acceptance_criteria, status, attempt_count, last_error, blocker, artifact_refs, qa_summary, next_action, notes`.

Canonical lifecycle:
`REFERENCE -> STRUCTURE -> STRUCTURE_QA -> SURFACE -> SURFACE_QA -> RUNTIME_QA -> SYNCED -> COMPLETE`.
Exceptional states: `BLOCKED`, `FAILED`, `PAUSED`.

## 6. Failover rules

Do not loop a rejected write indefinitely. After about three meaningful failures in the same representation/path, switch to an authorized durable alternative and preserve the error:

- Drive -> GitHub
- GitHub -> Base44
- Base44 -> Supabase
- Linear -> JSON task queue
- API write -> file canon

Do not bypass OAuth, RLS, branch protection, organization policy or connector safety controls.

## 7. Daily schedule (JST)

- 08:00: Queue Runner A — REFERENCE / STRUCTURE / foundation research.
- 12:00: Queue Runner B — continuation / STRUCTURE_QA / fixes.
- 16:00: Queue Runner C — SURFACE / texture / AO / PBR, only if Structure QA passed.
- 20:00: Queue Runner D — RUNTIME_QA / Base44 / Vercel / final fixes.
- 23:00: Daily Sync — reconcile Drive/GitHub/Base44/Linear/Supabase and read back writes.
- Sunday 23:30: Weekly Maintenance — DONE cleanup, BLOCKED review, duplicate consolidation, failure trends, reusable asset extraction, next-week priorities.

## 8. Notification and communication policy

Gmail is read-only/monitoring for project dependencies by default. Never send project mail in the user's name without explicit confirmation. Calendar may provide milestone context, but production cadence is owned by Automations.

## 9. Definition of COMPLETE

A task may be marked COMPLETE only when:
1. implementation is materially finished,
2. phase-relevant QA passes,
3. durable artifact/reference IDs are saved,
4. writes are read back,
5. exact `next_action` is either `NONE_COMPLETE` or a documented follow-up task,
6. Drive/GitHub/Base44 plus configured Linear/Supabase mirrors are not contradictory.
