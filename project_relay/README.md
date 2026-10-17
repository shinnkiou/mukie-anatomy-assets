# PROJECT RELAY AGENT bootstrap

> Temporary public staging area for non-secret design and prototype code only. Do **not** store API keys, OAuth tokens, private project data, real `.blend` files, private screenshots, or user documents here. Do not attach a self-hosted runner to this public repository.

## Goal

PROJECT RELAY AGENT is a small Windows resident execution/transport layer. ChatGPT remains the reasoning layer. Relay receives machine-readable commands, runs allowlisted local jobs, watches files/processes, saves checkpoints, packages results, and reports status.

Primary operating loop:

`START -> run unattended -> STOP/deadline -> save state -> package/report -> RESUME`

## Design principles

1. Simple start/stop. One launcher, optional Windows startup registration later.
2. Deterministic execution. Relay does not need to be intelligent.
3. Safe unattended work. Every job has a command id, state directory, deadline support, heartbeat, logs, and stop semantics.
4. Evidence-based success. Exit code alone is never sufficient.
5. Prefer direct interfaces: API/CLI/DOM/UI Automation/screen coordinates in that order.
6. Preserve originals. Work on copies; verify SHA-256 when required.
7. No silent errors. Empty `catch {}` / swallowed exceptions are prohibited in critical paths.
8. No unlimited recursive search. Search is bounded by configured roots/depth.
9. No stale-result success. Outputs must be associated with the current command id/run start time.
10. Public-repo safety. No secrets or private artifacts; no self-hosted runner on public repos.

## Common job lifecycle

- `DISCOVER`
- `PREFLIGHT`
- `EXECUTE`
- `VERIFY`
- optional `DATA_QUALITY_CHECK`
- `PACKAGE`
- `CHECKPOINT`
- `REPORT`

## Standard states

- `QUEUED`
- `RUNNING`
- `PAUSING`
- `PAUSED`
- `STOPPING`
- `STOPPED`
- `SUCCESS`
- `FAILED`
- `BLOCKED`
- `INCOMPLETE`
- `DATA_QUALITY_WARNING`
- `NEEDS_REVIEW`

## Stop levels

- `SOFT`: request cooperative stop at a safe checkpoint.
- `HARD`: terminate the active process tree after a grace period, then collect diagnostics.
- `EMERGENCY`: immediate process-tree kill, then best-effort recovery.

## Planned plugins

- `bp3d`: PowerShell/Blender execution, progress.json, marker/SHA/result verification.
- `datascope`: dependency preflight, collector execution, data-quality checks.
- `sakura_drum`: watch/validate/analyze `PLAY_MEASURE_*.zip` and maintain play history.
- `life_archive`: artifact/job/report bridge and future web QA.

## v0.1 bootstrap scope

The bootstrap code intentionally uses Python standard library only. It provides:

- local inbox command transport (`queue/inbox/*.json`)
- command-id deduplication
- state/checkpoint/result/error directories
- bounded file lookup helper
- subprocess execution with continuous stdout/stderr draining
- deadline and stop-file support
- output freshness verification hooks
- SHA-256 helpers
- result manifest generation

Discord, Google Drive, Base44, browser automation, and phone satellite transports should be added behind plugins after the local execution loop is proven reliable.

## Public staging note

This folder lives temporarily in `mukie-anatomy-assets` only because no dedicated private PROJECT RELAY repository is currently available through the connected GitHub account. Move it to a dedicated **private** repository before adding credentials, personal artifacts, remote-control secrets, or a Windows runner.
