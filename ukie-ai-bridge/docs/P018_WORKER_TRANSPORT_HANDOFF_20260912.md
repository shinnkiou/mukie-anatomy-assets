# P0.18 Worker Transport — Cloud-ready handoff

Generated: 2026-09-12 JST

## Verified release

- Release: `BRIDGE_P018_RUN_34611508747`
- Bridge: `0.18.0-p0.18`
- CI run: `34611508747` — SUCCESS
- CI artifact: `10268606902`
- Artifact bytes: `9,049,000`
- Artifact SHA-256: `9d67c6be0fd3566f4d99477e462df5000af3d97ee32f24a4de0c08ba583b2fb3`
- Drive durable copy: `1IV-AwCi_jRlmcn1xdZD5O-_Lf4D0ozLJ`
- Drive provider readback: size + SHA-256 verified
- BP3D production Blender pin remains `4.2.23`

## Control plane

- Base44 app: `SyncOps Hub` (`6aa2743da37b11162682c01f`)
- Base44 P0.18 checkpoint: `6aa47c8250d2ebd45a37d6e0`
- Supabase project: `vbuokbwglauibabinaqs`
- Worker endpoint: `ukie-worker-transport`
- Pair-preview endpoint: `ukie-worker-pair-preview`
- Worker protocol: `ukie_worker_v1`

The pairing UI now requires a server-verified preview before the human approval button becomes active. The preview verifies the signed-in Google owner, registered device, one-time pairing code, expiry, release and worker protocol. It does not return the device secret.

## P0.18 safety boundary

Cloud execution allowlist is exactly:

- `device_status`

Still denied:

- arbitrary shell / PowerShell
- arbitrary executable invocation
- registry writes
- cloud-supplied filesystem paths
- source `.blend` modification

The Windows device secret is generated locally and DPAPI-protected. The cloud stores only its SHA-256 hash. Jobs use a short lease and stale completion is rejected.

## Current hard gate

`P017_SOAK_DEVICE_STATUS_001` is still `QUEUED` with attempt `0`.

Not yet proven:

1. real Windows pairing
2. real worker heartbeat
3. cloud job transition `QUEUED → CLAIMED`
4. worker completion `CLAIMED → COMPLETED`

Therefore:

- `READY FOR AI = false`
- do not unlock `analyze_blend`
- do not promote P0.18 to STABLE
- keep PR #9 draft / do not merge

## Next physical step

Use the exact P0.18 ZIP above. Extract all four files together and double-click `RUN_WORKER.cmd`. The launcher opens the Base44 pairing page. Approve only if the server-verified preview shows the expected Windows device, release `BRIDGE_P018_RUN_34611508747`, worker protocol `ukie_worker_v1`, and allowlist `device_status`.

Keep the console open. The control plane can then verify the queued job transition and result.