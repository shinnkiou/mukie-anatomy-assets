# NEVER TEAR AI3D — AI3D-002 Physical Companion Start Guide

## Purpose

This guide is the human-side gate for AI3D-002. It does **not** widen the worker allowlist, does not queue jobs manually, and does not claim physical execution before evidence exists.

## Verified package

- Google Drive file: `AI3D-002_WINDOWS_WORKER_CANARY_34743230600.zip`
- Drive file ID: `1p8f9gOzRGcl6NMa87Sr-6pDI0JiOHUKx`
- ZIP SHA-256: `f06f0a122e2f24e28620ebdce7ff13c17e6e3bb49e27ee202a3e8f1c7498e03b`
- Executable: `NEVER_TEAR_AI3D_WORKER_CANARY.exe`
- EXE SHA-256: `53595f20432f1a586ddd654ec9d3bdb7c37a93f3ad1b468a181dda91246ec625`
- Worker version: `0.1.0-ai3d-canary`
- Contract: `never-tear-ai3d-worker-v1`
- Only allowlisted action: `ai3d_blender_physical_mvp_v1`

The ZIP from the verified run is intentionally preserved unchanged. Do not rebuild it merely to add convenience scripts.

## Preconditions

1. Use the **same Windows user account** that already paired UKIE AI BRIDGE. The companion reuses the DPAPI-protected credential at `%LOCALAPPDATA%\UKIE_AI_BRIDGE\worker\credential.json`.
2. Blender must be installed and discoverable either in PATH or under the standard `Blender Foundation\Blender *\blender.exe` location.
3. Run only **one** AI3D companion instance during the canary.
4. Do not queue an AI3D job to legacy worker `0.18.2-p0.18.2 / ukie_worker_v1`.

## Start procedure

1. Download the verified ZIP from the Drive file above.
2. Optional but recommended: verify the ZIP hash in PowerShell:

   ```powershell
   (Get-FileHash -Algorithm SHA256 .\AI3D-002_WINDOWS_WORKER_CANARY_34743230600.zip).Hash.ToLower()
   ```

   Expected: `f06f0a122e2f24e28620ebdce7ff13c17e6e3bb49e27ee202a3e8f1c7498e03b`

3. Extract the ZIP.
4. Optional but recommended: verify the EXE hash:

   ```powershell
   (Get-FileHash -Algorithm SHA256 .\NEVER_TEAR_AI3D_WORKER_CANARY.exe).Hash.ToLower()
   ```

   Expected: `53595f20432f1a586ddd654ec9d3bdb7c37a93f3ad1b468a181dda91246ec625`

5. Start `NEVER_TEAR_AI3D_WORKER_CANARY.exe` by double-clicking it, or from PowerShell:

   ```powershell
   .\NEVER_TEAR_AI3D_WORKER_CANARY.exe
   ```

6. Leave the console open through the canary. Expected startup text begins with:

   `NEVER TEAR AI3D Worker 0.1.0-ai3d-canary online`

## What happens automatically

The companion immediately sends a heartbeat carrying its exact worker version and capability. The Supabase fail-closed Auto-Arm Gate accepts the heartbeat only when all required predicates match. It then inserts exactly one fixed CANARY:

- job key: `AI3D-002-PHYSICAL-CANARY-001`
- command ID: `AI3D-002-CANARY-001-NEVER-TEAR`
- `max_attempts = 1`

The companion then claims the job, runs Blender with `shell=False`, uploads the PNG, verifies provider SHA readback, and reports automated QA. Visual QA remains a separate gate.

## Local evidence locations

Worker-owned evidence is stored under:

`%LOCALAPPDATA%\UKIE_AI_BRIDGE\ai3d`

Job data is under `jobs\...` and receipts under `receipts\...`.

## Success boundary

A console saying the worker is online is **not** success by itself. AI3D-002 passes only after the project records:

1. verified companion heartbeat,
2. one CANARY claim / lease / heartbeat,
3. real Blender result,
4. durable provider PNG SHA readback PASS,
5. automated QA PASS,
6. visual QA PASS.

Only after that may AI3D-004 evaluate promotion. `ai3d_structure_module_v1` remains separately staged and is not automatically promoted.

## Failure boundary

If the companion reports missing paired credential, wrong Windows user, Blender not found, transport failure, render failure, or SHA mismatch, keep AI3D-002 ACTIVE/HOLD, preserve the error, and do not fall back to the legacy worker.
