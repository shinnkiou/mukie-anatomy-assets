# CSMC Evidence Probe v0.2 — authorized real-target execution

Status: `READY_FOR_PRIVATE_TARGET_FILE`

This is the execution boundary after the public-safe synthetic regression and GitHub durability checks. It is intentionally narrow: run the read-only v0.2 probe against the already-authorized target `.clip`; do not restart generic container reverse-engineering or broad runtime scanning.

## Known target identity

Expected authorized target:

- filename historically used: `デッサン人形(女性160)クリップfile.clip`
- size: `56,996,715` bytes
- SHA-256: `ed391b6fef0f425165f6dd4719ec9000966742efde5428cb2c1446f63640e933`

`RUN_AUTHORIZED_TARGET_V02.cmd` fails closed unless both size and SHA-256 match. It does not search the PC and does not upload the input.

## Simplest private run

Keep these files together:

- `csmc_3d_evidence_probe.py`
- `RUN_AUTHORIZED_TARGET_V02.cmd`

Then drag the authorized target `.clip` onto `RUN_AUTHORIZED_TARGET_V02.cmd`.

Optional CSMC/CS3C comparison from Command Prompt:

```text
RUN_AUTHORIZED_TARGET_V02.cmd "target.clip" "target.csmc"
```

Requirements:

- Windows PowerShell (for SHA-256 and ZIP packaging)
- Python 3 available as `py -3` or `python`

No automatic software installation, privilege escalation, network upload, or filesystem scan is performed.

## Output

The runner creates:

- `PRIVATE_TARGET_RUN_<timestamp>/`
- `PRIVATE_TARGET_RUN_<timestamp>.zip`

The input `.clip` is not copied into the output bundle. Evidence Probe reports summarize BLOBs with sizes/hashes rather than publishing purchased raw model bytes.

## Acceptance questions for this run

The real run must explicitly answer:

1. `ModelData3D` state: `LIVE_ROWS`, `TABLE_EMPTY`, `SCHEMA_ONLY`, or `ABSENT`.
2. If live, whether `ModelData3D.Layer3DModelData` resolves to a concrete `CHNKExta` payload.
3. `Canvas3DModelBank` state: `LIVE_ROWS`, `TABLE_EMPTY`, `SCHEMA_ONLY`, or `ABSENT`.
4. If live, whether `Canvas3DModelBank.BankData` resolves to a concrete `CHNKExta` payload.
5. Confirm the already-known live routes still resolve:
   - `Canvas3DModelLoader.ModelData -> catalog_character`
   - `Manager3DOd.SceneData -> scene`
6. Confirm `ModelInfo3D` / `ModelNodeInfo3D` remain schema-only for this target unless fresh evidence proves otherwise.

## Gate after the run

If the fresh file-side graph exposes another useful live route, continue P3 controlled pairs using:

`A0 baseline -> C0 no-change -> B0 one-variable -> R0 return`

If it proves there is no additional useful file-side route, P4 may resume only as a narrow static/runtime/decompiler trace anchored to a specific controlled operation/payload. Known GUID hits alone are not accepted as dynamic payload evidence.

## Public/private boundary

Public GitHub may contain this runner, source code, synthetic fixtures, hashes, and reports that do not contain purchased payload bytes.

Keep the purchased `.clip` / CSMC/CS3C, extracted mesh/texture bytes, and private runtime captures out of the public repository.
