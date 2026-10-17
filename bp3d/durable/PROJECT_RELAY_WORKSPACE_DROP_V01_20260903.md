# BP3D PROJECT RELAY Workspace Drop V0.1 — Durable Record

Status: `DURABLE_WINDOWS_WORKSPACE_DROP_READBACK_PASS`

A PROJECT RELAY v1 contract-compliant Windows deployment/handoff package was generated for the current graduation mainline.

## Workspace contract

Target root:

`E:\PROJECT_RELAY\WORKSPACES\bp3d\`

Directories:
- `00_INPUT`
- `10_SPECS`
- `20_WORK`
- `30_OUTPUT`
- `40_REPORT`
- `50_CHECKPOINT`
- `90_LOG`
- `99_ARCHIVE`

## Durable package

- artifact key: `PROJECT_RELAY_WORKSPACE_DROP_V01_20260903`
- package size: 4,411,597 bytes
- SHA-256: `86f591fb78ce3c85502a5aa0882f74f4c2e0a6c310d87b166873e9d923aee963`
- Drive exact-byte readback: PASS
- ZIP CRC: PASS
- entries: 15

The large/private package remains in Google Drive and is not committed to GitHub.

## Contents and execution behavior

The deployment package contains the durable Graduation One-Click V0.1 input, a bounded Job Spec, source guards, state/checkpoint snapshots, SHA manifests, and a manual fallback runner.

The manual fallback:
1. verifies the one-click input SHA-256;
2. creates a fresh bounded work directory;
3. archives only a previous BP3D run directory inside `99_ARCHIVE`;
4. executes the one-click pipeline;
5. requires pipeline / QA / H1–H5 capture JSON status `PASS`;
6. refuses stale or missing output promotion;
7. copies only fresh validated output into `30_OUTPUT` and reports into `40_REPORT`;
8. writes explicit SUCCESS or FAILURE markers.

## Control-plane state at packaging

- `windows-main`: OFFLINE
- Relay SELFTEST: QUEUED
- BP3D queue runner: disabled until SELFTEST succeeds
- manual fallback: ready
- GitHub Blender 4.2.23 static/compile gate: PASS
- actual real-model Windows Blender QA: pending

## Source guards

- semantic authority: Final-v3 + V45
- anatomical front: NEGATIVE_Y
- MASTER writes: 0
- R7 writes: 0
- Production14: HOLD
- Production13: FORBIDDEN
- pre-V45 rollback: FORBIDDEN
- source mesh mutation: 0
- canonical semantic mutation: 0
- external-author pixels: 0

This is deployment/control-plane work only. It is not a semantic re-segmentation artifact.
