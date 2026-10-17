# UKIE AI BRIDGE — Operations & Evidence Plan

## Source of truth by data type

| Data | Primary source of truth | Mirror / secondary |
|---|---|---|
| Source code / protocol / capability scripts | GitHub | Base44 checkpoint metadata |
| Device state / live control state | Base44 | Supabase durable ledger |
| Job history / events / artifact verification | Supabase | Base44 dashboard |
| Large artifacts (.blend, PNG, JSON, logs) | Google Drive | Supabase/Base44 refs only |
| Engineering work / incidents / acceptance gates | Linear | GitHub PR comments |
| Incident notification | Gmail label `UKIE AI BRIDGE/Alerts` | Linear incident/comment |
| Scheduled operations review | Google Calendar | Not created until the user selects a cadence/time |

## Reconciliation rule

A job is **not complete** because Blender exits with code 0.

`COMPLETED = process exit 0 AND expected local artifacts exist AND fresh run identity matches AND SHA-256 exists AND Drive upload succeeds AND Drive readback/size/hash verification succeeds`.

If Base44 and Supabase disagree, Supabase is the durable job/event ledger and Drive is the durable artifact source. Base44 is repaired from those sources rather than treating stale UI state as authoritative.

## P0 lifecycle

1. Base44 creates an allowlisted job.
2. Supabase records the durable job key and state.
3. Windows Bridge claims once using the stable `job_id` / idempotency key.
4. Input is downloaded into a per-job ASCII workspace.
5. Input SHA-256 is verified before Blender is started.
6. `ANALYZE_ONLY` runs in native local Blender background mode.
7. Bridge records stdout/stderr, scene report, versions, timestamps, and local artifact hashes.
8. Artifacts upload to Drive.
9. Bridge reads back Drive metadata/content as required and verifies size/hash.
10. Supabase receives append-only evidence events.
11. Base44 mirrors the final state for the user.
12. Human Visual QA can promote the result; headless success alone does not replace visual judgement.

## Failure policy

- Duplicate delivery: same `job_id` never runs a second modifying execution after a final state.
- Network loss: local job continues only when safe; result stays local until sync can resume.
- Blender hang: timeout kills the Blender process tree, not the Bridge service.
- Drive interruption: local artifacts are retained; upload resumes/retries; no `COMPLETED` state before readback.
- Unexpected script/API error: preserve traceback and pre-run scene data.
- Disk pressure: fail preflight before creating large derived copies.
- New permission requested by a capability: fail closed and require review.

## Evidence retained for every Blender job

- request / protocol version
- original filename and ASCII working filename
- input SHA-256 and size
- Blender version
- Blender Python version
- Bridge version
- capability/script version and hash
- `scene_before.json`
- executed script or analyzer hash
- stdout / stderr
- `scene_after.json` and scene diff when editing is introduced
- previews
- result SHA-256 and size
- Drive file id / URL
- readback verification status
- timestamps for every stage
- failure code / traceback when applicable

## Test gates

### Gate A — cloud foundation

- Base44 build passes.
- Supabase UKIE tables exist with RLS.
- GitHub Windows CI passes.
- Drive folder readback passes.

### Gate B — first real PC handshake

- Packaged EXE starts without administrator rights.
- `device-status` reports real Windows CPU/RAM and Blender discovery.
- No arbitrary command endpoint exists.

### Gate C — first Blender round trip

- Known `test_cube.blend` input SHA verified.
- Original is never opened for save.
- ASCII `input.blend` and `working.blend` created.
- Blender 4.2.23 background ANALYZE_ONLY succeeds.
- `scene_before.json`, logs, manifest generated.
- Drive upload + readback verification succeeds.

### Gate D — resilience

Run at least:

1. 10 consecutive normal jobs.
2. Duplicate job delivery.
3. Base44 disconnect during execution.
4. Network loss during upload.
5. Blender forced termination.
6. PC restart with an interrupted job.
7. Japanese original filename.
8. Wrong input SHA.
9. Wrong Blender version.
10. Insufficient local disk simulation.

## Operational severity

- **INFO**: successful run, expected offline state, CI pass.
- **WARN**: retry, resource wait, stale heartbeat, version mismatch before execution.
- **ERROR**: job failed, upload/readback mismatch, Blender crash/hang.
- **CRITICAL**: integrity violation, source overwrite attempt, permission expansion, repeated crash loop.

ERROR/CRITICAL events should create/append a Linear incident and may generate a Gmail alert. Alerting must not include secrets, OAuth tokens, full environment dumps, or purchased model bytes.

## Update policy

Core and Capability Packs remain separate.

- Read-only capability improvement: static test -> fixture test -> permission diff -> signed candidate -> canary -> health check.
- Any expansion involving delete, shell, registry, installer, broad filesystem, or new network permission requires a human gate.
- Three startup crashes after an update marks the release bad, rolls back to last-known-good, and pauses automatic updates.

## Current P0 stop condition

Do not merge the foundation PR and do not expand the remote command allowlist until the first real Windows `device-status` handshake and Blender/Drive round trip are evidenced in Supabase + Drive + Linear.
