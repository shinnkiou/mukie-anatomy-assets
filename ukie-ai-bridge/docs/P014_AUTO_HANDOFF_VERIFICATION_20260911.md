# P0.14 Auto Handoff Verification — 2026-09-11

## Result

P0.14 automatic handoff foundation passed Windows CI.

- Workflow: `UKIE AI Bridge P0.14 Auto Handoff CI`
- Workflow run: `34599731024`
- Head commit: `39999fa4f23fdbe22981a02c096a1f5bf5e08410`
- Artifact ID: `10262974677`
- Artifact name: `UKIE_AI_BRIDGE-P0.14-windows`
- Artifact archive size: `8,461,481` bytes
- Artifact SHA-256: `4f1c2930326d4d79e60871d21ff911dec6ad17576da885383de6adc50ac2c887`
- GitHub artifact expiry: `2026-09-25T12:36:31Z`
- BP3D production Blender pin: `4.2.23`

The downloaded workflow artifact was independently re-hashed after download and matched the GitHub artifact digest exactly.

## P0.14 behavior

Normal first-run no longer requires a Google Drive folder picker.

Resolution order:

1. Reuse a valid saved handoff configuration when available.
2. Check the explicit `UKIE_DRIVE_SYNC_ROOT` override when supplied.
3. Check only bounded common Google Drive for desktop locations.
4. Do not recursively crawl the user's disks.
5. If no safe Drive candidate is found, preserve evidence in `LOCAL_OUTBOX_ONLY` and continue the local research run.

The local-outbox fallback must keep all of these false:

- `sync_folder_copy_proven`
- `drive_cloud_presence_proven`
- `drive_readback_proven`
- `ready_for_ai`
- `promotion_performed`

## CI evidence

The P0.14 Windows CI passed all of the following:

- Python compile
- full historical regression suite
- P0.12 cloud recovery regressions
- P0.14 auto-handoff regressions
- source self-test
- bounded Drive candidate test
- one-file PyInstaller Windows EXE build
- packaged EXE self-test
- packaged EXE job validation
- packaged EXE device status
- packaged EXE no-picker handoff configuration
- one-click package staging
- artifact upload

The earlier P0 foundation and P0.12 workflows also passed on the same corrected head.

## Base44

`SyncOps Hub` Acceptance UI was updated to describe P0.14 automatic handoff and local-outbox fallback. Base44 `npm run build` passed.

Checkpoint:

- checkpoint id: `6aa3f6f0ed0dff7ffa4ba2a0`
- checkpoint commit: `d8e847cd3b0857cd7b81c0694611051adf79bc18`

## Durability note

Uploading the P0.14 ZIP to Google Drive from the current chat connector was blocked by the connector safety layer. Therefore the P0.14 binary is currently GitHub-artifact verified, but Drive durability for this binary has not been proven.

Do not label the P0.14 release `DRIVE_VERIFIED`, `READY_FOR_AI`, `CANARY_PASS`, or `STABLE` on the basis of this CI result alone.

## Next physical gate

Run the P0.14 package on the real Windows machine and require:

`UKIE_AI_BRIDGE.exe -> Blender 4.2.23 detection -> physical acceptance -> automatic handoff or local outbox -> Google Drive provider discovery -> raw readback -> SHA match -> offline acceptance verification`

Only after physical provider readback should release-promotion evaluation continue.
