# UKIE AI BRIDGE — Foundation

This directory contains the P0 execution-plane foundation for BP3D / CSMC experiments.

## System split

- **ChatGPT**: analysis, script proposal, error diagnosis.
- **Base44**: control plane, device/job/result UI.
- **Windows Bridge**: execution plane on the user's real Windows PC.
- **Blender**: local native Blender, background mode first.
- **Google Drive**: artifact plane and durable result store.
- **Supabase**: durable device/job/event/artifact ledger.
- **Linear**: development and incident tracking.
- **Gmail / Calendar**: alerting and scheduled operations review only.

## P0 safety contract

1. No VM, Hyper-V, VirtualBox, virtual GPU, or kernel driver is required.
2. No arbitrary PowerShell, arbitrary executable launch, registry editing, or whole-disk access is exposed to AI.
3. Source files are immutable. Jobs use `original -> working copy -> result`.
4. Internal working names are ASCII. Original Unicode/Japanese filenames live only in manifests.
5. Every job has a stable `job_id` and is idempotent.
6. Every job records stdout, stderr, versions, input/output SHA-256, timestamps, and artifact refs.
7. `COMPLETED` is allowed only after Drive readback verification.
8. Blender runs as a child process with per-job timeout. Bridge survival is independent of Blender survival.
9. Blender version is project-pinned. BP3D production is pinned to **4.2.23** until compatibility tests approve another version.
10. Human Visual QA remains available and is not replaced by headless success.

## P0 commands

Initially expose only:

- `device_status`
- `analyze_blend`
- `upload_results`

Later P1 commands may add `run_blender_script`, `render_preview`, `render_views`, `save_blend_copy`, `compare_scene`, and `check_gpu`.

## Job state machine

`QUEUED -> CLAIMED -> INPUT_DOWNLOADING -> INPUT_VERIFIED -> WORKING_COPY_CREATED -> PREFLIGHT -> BLENDER_RUNNING -> LOCAL_SAVED -> HASHED -> UPLOADING -> UPLOADED -> READBACK_VERIFYING -> VERIFIED -> COMPLETED`

Failure branches: `FAILED`, `TIMEOUT`, `INTERRUPTED`, `WAIT_RESOURCE`, `NEEDS_HUMAN`.

## First acceptance test

`Base44 -> Bridge -> Drive input -> SHA verify -> ASCII working copy -> Blender 4.2.23 -b -> ANALYZE_ONLY -> scene_before.json + preview_front.png + logs + manifest -> SHA -> Drive upload -> Drive readback -> Base44 COMPLETED -> ChatGPT reads artifacts`.

The MVP is accepted only after ten consecutive successful runs plus negative tests for duplicate job delivery, network interruption, Blender forced termination, and interrupted Drive upload.
