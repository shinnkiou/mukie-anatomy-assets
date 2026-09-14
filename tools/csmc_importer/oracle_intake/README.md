# CSMC F02 Mutation Oracle Intake

Status: **intake contract ready; physical MODELER oracle pending**.

This package does not run MODELER and does not manufacture oracle observations. It only validates future read-only observations against the already-generated, provenance-bound 30-variant F02 mutation batch.

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

A full oracle is exactly 30 observations. Partial checkpoints may be validated only when explicitly requested and remain classified as partial.

`oracle_intake_cli.py` is the recommended intake path because it computes the **raw file SHA-256 of the source manifest itself** before parsing and refuses the observation if that digest is not the preregistered manifest digest. This closes the gap where a caller could otherwise pass an unverified manifest object together with a separately supplied digest string.

Example after observations exist:

```bash
cd tools/csmc_importer/oracle_intake
python oracle_intake_cli.py \
  /path/to/CSMC_F02_SINGLE_BYTE_XOR01_30_PUBLIC_MANIFEST_20260914.json \
  /path/to/CSMC_F02_MUTATION_ORACLE_30_V1_OBSERVED.json \
  --public-out /path/to/oracle_public_projection.json \
  --receipt-out /path/to/oracle_intake_receipt.json
```

For an explicitly incomplete checkpoint only, add `--partial`. The CLI never opens MODELER, never edits CSMC, and never generates a new mutation.

## Public/private boundary

A public-safe projection may include offsets, regions, hashes, load/visual/error classifications, timing, screenshot/view hashes, and observation provenance. Raw private CSMC bytes and raw byte-before/byte-after values are removed from the public projection.

No field may assert vertex/index/material/UV/weight/etc. `semantic_promotion=false` and `blender_emit=false` are mandatory.

## Interpretation boundary

This oracle answers sensitivity/tolerance questions only. It does not assign field semantics. Proof-grade semantic binding still requires cross-evidence with controlled differential, negative control, and MODELER direct field-read/data-flow evidence.
