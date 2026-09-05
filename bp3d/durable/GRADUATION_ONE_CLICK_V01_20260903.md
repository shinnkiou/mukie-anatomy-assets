# BP3D Graduation One-Click V0.1 — Durable Record

Status: `DURABLE_ONE_CLICK_PIPELINE_READBACK_PASS`

This bundle joins the current graduation mainline into one fail-closed Windows/Blender execution path:

1. Graduation Deadline Build V0.2 assembly
2. real Blender 8-view QA
3. hard PASS gate
4. recovered H1–H5 capture
5. capture-output ZIP packaging

## Durable package

- Drive ZIP ID: `1HFwXao5kWq4j6eA0PYTNdYxmq5JT4TpQ`
- SHA sidecar ID: `1BHYjFx6gbONscyvm0HHCc7bMh4bSFkqQ`
- one-click BAT ID: `1Xy70bUQzHxAj8JZBX5OEwXV6S1LJcCH0`
- README ID: `1OxPmEi6jrLPvEYNXhxhQM8J9vYuy5c7_`
- ZIP size: 4,400,833 bytes
- SHA-256: `8a2cfc9a9f89dcb4161bf86a23222bf4db464bb590601f2984c055650d02098e`
- Drive exact-byte readback: PASS
- ZIP CRC: PASS
- Python syntax: PASS

## Default execution

- QA: 8 renders
- capture: 26 views × 4 modes = 104 renders
- modes: `FULL`, `ARM_ISOLATED`, `LEG_ISOLATED`, `TORSO_ISOLATED`
- capture starts only when QA JSON status is exactly `PASS`
- a QA or capture failure preserves outputs and exits non-zero

## Safety

- MASTER writes: 0
- R7 writes: 0
- Production13: FORBIDDEN
- Production14: HOLD
- pre-V45 rollback: FORBIDDEN
- source mesh mutation: 0
- semantic mutation: 0

The Windows Relay node remains offline, so actual Blender execution is still pending. The package is nevertheless ready for manual double-click or future Windows Relay execution. Draft PR #8 remains unmerged until real-Blender QA succeeds.
