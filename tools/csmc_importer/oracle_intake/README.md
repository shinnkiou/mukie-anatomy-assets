# CSMC F02 Mutation Oracle Intake

Status: **intake hardened; physical MODELER oracle still pending**.

This package does not run MODELER and does not manufacture oracle observations. It only prepares and validates future read-only observations against the already-generated, provenance-bound 30-variant F02 mutation batch.

## Source binding

- batch: `CSMC_F02_SINGLE_BYTE_XOR01_30_20260914`
- base fixture: `CSMC_F02_QUAD`
- source public manifest SHA-256: `751f05dfff9d5308dfd96421d5bce43e6785de2cb385fb28a8c97c565c6cc891`
- expected variants: exactly `M01..M30`
- each source variant is already verified as one character-BLOB byte XOR `0x01`, SQLite-readable, and frame-rule preserving.

## Allowed physical operation

The physical observer may only open the already-generated variant and observe/classify behavior. This contract requires zero Save/Save As/Ctrl+S actions and rejects any observation that claims a save action occurred.

The primary load classification is one of:

- `LOAD_ACCEPTED`
- `LOAD_REJECTED`
- `PARTIAL_LOAD`
- `ERROR_DIALOG`
- `CRASH`
- `UNKNOWN`

Visible effect is tracked separately as `VISIBLE_MODEL_CHANGED`, `VISIBLE_MODEL_UNCHANGED`, `NOT_VISIBLE`, or `UNKNOWN`. A visual change is an observation, not a semantic conclusion.

## Fail-closed provenance

Every observation row must bind to the preregistered variant ID, payload-relative source offset, structural region, variant file SHA-256, and variant character-BLOB SHA-256 from the source manifest. Missing, duplicate, extra, or hash-mismatched rows are rejected.

`oracle_intake_cli.py` computes the **raw file SHA-256 of the source manifest itself** before parsing and refuses the observation if that digest is not the preregistered manifest digest.

The v2 physical-completion gate additionally prevents a 30-row placeholder sheet from being mislabeled as a completed oracle. Final completion requires all 30 variants plus resolved load/visible/process classifications, `DIRECT_PHYSICAL_OBSERVATION` evidence on every row, offset-aware ISO-8601 timestamps, and zero save actions. Partial or unresolved rows may be retained only as partial checkpoints.

## Manual-entry workflow

Use `CSMC_F02_MODELER_ORACLE_OPERATOR_GUIDE_V2_20260914.md` and the v2 CSV sheet. The older CSV containing `save_normalization_result` is legacy history only and must not be used to authorize any save action.

Convert a partially filled v2 CSV to validated JSON:

```bash
cd tools/csmc_importer/oracle_intake
python oracle_csv_to_json.py \
  /path/to/CSMC_F02_SINGLE_BYTE_XOR01_30_PUBLIC_MANIFEST_20260914.json \
  /path/to/CSMC_F02_MUTATION_ORACLE_OBSERVATION_SHEET_V2_20260914.csv \
  /path/to/observation.json \
  --partial

python oracle_intake_cli.py \
  /path/to/CSMC_F02_SINGLE_BYTE_XOR01_30_PUBLIC_MANIFEST_20260914.json \
  /path/to/observation.json \
  --partial \
  --public-out /path/to/oracle_public_projection.json \
  --receipt-out /path/to/oracle_intake_receipt.json
```

For final 30/30 completion, remove `--partial` from both commands. The tools never open MODELER, never edit CSMC, and never generate a new mutation.

## Public/private boundary

A public-safe projection may include offsets, regions, hashes, load/visual/error classifications, timing, screenshot/view hashes, and observation provenance. Raw private CSMC bytes and raw byte-before/byte-after values are removed from the public projection.

No field may assert vertex/index/material/UV/weight/etc. `semantic_promotion=false` and `blender_emit=false` are mandatory.

## Interpretation boundary

This oracle answers sensitivity/tolerance questions only. It does not assign field semantics. Proof-grade semantic binding still requires cross-evidence with controlled differential, negative control, and MODELER direct field-read/data-flow evidence.
