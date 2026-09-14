# CSMC F02 MODELER Oracle — Operator Guide v2 — 2026-09-14

Status: `READY_FOR_READ_ONLY_PHYSICAL_OBSERVATION`

## Purpose

This packet is only for the already-generated batch `CSMC_F02_SINGLE_BYTE_XOR01_30_20260914`.
It records how MODELER reacts when each preregistered variant is opened.
It does **not** assign vertex/index/material/UV/weight semantics and does not authorize any runtime mutation.

## Bound source

- base fixture: `CSMC_F02_QUAD`
- source manifest Drive ID: `15MOvvR5a8InBKPXqLN_YeqjMgZ-G50YT`
- source manifest raw SHA-256: `751f05dfff9d5308dfd96421d5bce43e6785de2cb385fb28a8c97c565c6cc891`
- private 30-variant ZIP Drive ID: `1I9Ava5ORPnSi7mWXiSf8TqFbxBq5Hycx`
- v2 observation sheet Drive ID: `1BeZia1JNp0xQibuB5FomYpVTCTLU6xEx`
- v2 observation sheet SHA-256: `c8c03fc2551d655d540b2177927eeaf2b529d6a58cd805a36004e7fe9f307d86`

The earlier observation sheet `1tQP9Zyy4UQCkqkdwX2kOonqdRDfLeH-X` is retained as history only.
It contains a legacy `save_normalization_result` column. Do not use that column and do not perform any Save/Save As/Ctrl+S action.

## Strict read-only rule

Allowed:
1. Open an already-generated variant.
2. Observe load result, visible effect, error state, and process survival.
3. Optionally measure load time and capture screenshot/viewport hashes.
4. Close/discard without saving.

Forbidden:
- Save / Save As / Ctrl+S
- serializer-trigger experiments
- model editing
- overwrite of mutation files
- new arbitrary mutation generation
- plugin injection / hook / process-memory write
- semantic promotion
- Blender emit

`save_action_performed` must remain `FALSE` for every recorded row.

## Fast sentinel order

Run these first:

`M01 → M10 → M13 → M14 → M15 → M18 → M22 → M23 → M30`

If those are recorded successfully, continue the remaining variants in ascending order:

`M02–M09, M11–M12, M16–M17, M19–M21, M24–M29`

Full completion still requires M01–M30 exactly once.

## Per-variant observation

Use a clean read-only MODELER 1.10.13 observation session.

For each variant:
1. Confirm the variant ID and filename from the v2 CSV.
2. Open the file without editing it.
3. Record exactly one `oracle_result`:
   - `LOAD_ACCEPTED`
   - `LOAD_REJECTED`
   - `PARTIAL_LOAD`
   - `ERROR_DIALOG`
   - `CRASH`
   - `UNKNOWN`
4. Record exactly one `visible_effect`:
   - `VISIBLE_MODEL_CHANGED`
   - `VISIBLE_MODEL_UNCHANGED`
   - `NOT_VISIBLE`
   - `UNKNOWN`
5. Record `process_survival`:
   - `SURVIVED`
   - `TERMINATED`
   - `UNKNOWN`
6. For a direct manual observation use `evidence_strength=DIRECT_PHYSICAL_OBSERVATION`.
7. Set an `observer_session_id`.
8. Set `observed_at` as offset-aware ISO-8601, for example `2026-09-14T18:45:00+09:00`.
9. Leave `save_action_performed=FALSE`.
10. Close/discard without saving.

A visual change is an observation only. It is not a field-semantic conclusion.

## Completion gate v2

A 30-row file is no longer enough by itself to be called a completed physical oracle.
The hardened intake requires:

- exact M01–M30 coverage;
- exact preregistered offset/region/file SHA/BLOB SHA provenance;
- no `UNKNOWN` load result for final completion;
- no `UNKNOWN` visible effect for final completion;
- no `UNKNOWN` process survival for final completion;
- `DIRECT_PHYSICAL_OBSERVATION` for every completed row;
- an offset-aware valid `observed_at` timestamp;
- zero save actions.

Partial checkpoints remain allowed with `--partial`. They are not semantic proof.

## CSV → validated JSON

From `tools/csmc_importer/oracle_intake` on branch
`csmc-f02-mutation-oracle-intake-20260914`:

```bash
python oracle_csv_to_json.py SOURCE_MANIFEST.json OBSERVATION_V2.csv observation.json --partial
python oracle_intake_cli.py SOURCE_MANIFEST.json observation.json --partial \
  --public-out public_projection.json \
  --receipt-out intake_receipt.json
```

For final 30/30 completion, remove `--partial` from both commands.
The final CLI fails closed if the raw source manifest SHA-256 differs from the preregistered digest.

## Interpretation boundary

Passing this oracle means only that physical consumer behavior was directly observed for the preregistered mutation set.
It does not, by itself, prove vertex/index/material/object/UV/bone/weight semantics.
`STRUCTURAL_ONLY`, semantic promotion `0`, Blender emit `BLOCKED`, and runtime dispatch `false` remain in force until separate proof-grade cross-evidence exists.
