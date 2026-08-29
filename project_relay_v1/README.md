# PROJECT RELAY v1 — Virtual/Cloud Bootstrap

Date: 2026-08-30

## Goal

The human-facing command surface should converge on **Discord only**. Everything else should be self-contained as far as possible:

`Discord -> Base44 Control Plane -> Brain Router -> Cloud/Windows Worker -> Validation -> Artifact -> Base44 -> Discord`

## Roles

- **Discord**: human command inbox, notification, STOP, approval. Not the database.
- **Base44**: control plane / state source of truth.
- **ChatGPT**: preferred reasoning brain when a supported route exists.
- **Base44 PROJECT RELAY Super Agent**: temporary/fallback reasoning brain when ChatGPT is not directly routable.
- **GitHub**: code, runner, schema, CI, version history.
- **Google Drive**: large artifacts, diagnostics, checkpoints and reports.
- **Windows Agent**: only for local/desktop-only work such as existing local assets, desktop Blender, Adobe, etc.
- **GitHub Actions Virtual Worker**: cloud execution for declarative/non-Windows jobs.

## Base44 entities added for v1

Existing RelayJob / RelayEvent / RelayNode / RelayRunner / RelayArtifact / RelayTransport remain.

New:

- `RelayProject` — project policy, brain route, worker preference, allowed runners.
- `RelayInbox` — external message intake and dedupe.
- `RelayAttempt` — one execution attempt.
- `RelayFailure` — classified failure evidence.
- `RelayRepairPlan` — bounded self-repair action.
- `RelayBrainRoute` — ChatGPT primary / Base44 Super Agent fallback.

## Base44 agent

A dedicated `project_relay_agent` configuration was added to Creative Ops Lab.

It is required to:

1. Route natural-language instructions through allowlisted runners only.
2. Never execute arbitrary shell text from Discord.
3. Create attempt/failure/repair records.
4. Auto-repair only bounded, non-destructive failures.
5. Escalate delete/overwrite/publish/auth/billing/secret changes.
6. Never declare SUCCESS from exit code alone.
7. Use ChatGPT when available; fall back to the Base44 Super Agent when ChatGPT routing is unavailable.

## Virtual BAT policy

Cloud Linux workers do **not** pretend to execute Windows `.bat` files.

BAT responsibilities are decomposed into fixed-schema `VirtualAction`s handled by `VIRTUAL_FLOW_V1`. Desktop-only work is handed to the future Windows Agent v1.

Allowed virtual actions in the current proof:

- WRITE_TEXT
- WRITE_JSON
- VALIDATE_EXISTS
- VALIDATE_NONZERO
- PACKAGE_ZIP

## First autonomous self-repair proof

GitHub Actions run `33269770045`:

1. attempt 1 intentionally validates a missing required output.
2. failure is classified as `OUTPUT`.
3. a rule-engine repair plan is generated.
4. `WRITE_TEXT` is prepended before validation.
5. attempt 2 runs automatically.
6. required output exists and is non-zero.
7. RESULTS.zip is created and re-open tested.
8. final status is SUCCESS.

This proves the control-loop shape `FAIL -> DIAGNOSE -> REPAIR PLAN -> RETRY -> VERIFY` in a cloud worker without touching the user's PC.

## Discord status

Base44 exposes an official Discord connector (`integration_type=discord`). It is currently **not authorized**. Until the user authorizes it, Relay must report `AUTH_REQUIRED` and must not pretend that external Discord write-back succeeded.

Target behavior after authorization:

- one Discord instruction is accepted once (message-id dedupe)
- automatic acknowledgement
- progress update(s)
- one final SUCCESS or FAILED/WAITING_APPROVAL notification
- no routine requirement to run both `/relay status` and `/relay jobs`

## Windows Agent v1 requirements

The existing beta local-folder/BAT approach is not the final design. Windows Agent v1 should eventually provide:

- one persistent application/service, not repeated ZIP extraction and BAT launches
- Base44 remote poll/claim
- process supervision
- STOP / RESUME / checkpoint
- updater + SHA validation + rollback
- Drive upload
- Discord status write-back
- allowlisted runners
- no arbitrary shell from external messages
- local desktop automation only where cloud execution cannot replace it

## ChatGPT UI automation

A Windows program that clicks the ChatGPT UI, enters text and submits it is **not implemented yet** and must not be treated as a reliable integration. It is a future fallback/bridge option. Preferred long-term routing should use supported APIs/connectors/context packages rather than fragile screen-coordinate automation where possible.

## Next gates

1. Authorize Base44 Discord connector.
2. Prove Discord -> RelayInbox -> RelayJob and Base44 -> Discord acknowledgement.
3. Connect `project_relay_agent` to NEW RelayInbox processing.
4. Add GitHub Actions dispatch from a fixed-schema cloud job.
5. Implement Base44 <-> Windows Agent remote claim/poll.
6. Build one persistent Windows Agent v1.
7. Use `bar3d_sandbox` / Never Tear as the first real production proof after the control plane passes.
