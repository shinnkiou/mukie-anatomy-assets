# CSMC P4 explicit parent-edge static inventory — 2026-09-13

Status: **CURRENT DURABLE-METADATA SEARCH COMPLETE / AGGREGATE STATIC WORK CONTINUES / ZERO RUNTIME**

This pass checks whether the current public-safe/durable mainline evidence already contains an explicit parent boundary, parent length field, or consumer cross-reference for `BND_197_TO_195`. It does not rescan target bytes.

## Sources rechecked

- `CSMC_REAL_TARGET_P1_P2_P4_CHECKPOINT_20260912.md`
- `CSMC_P1_P2_TARGET_EVIDENCE_CONSOLIDATION_20260912.md`
- `CLIP_3D_PARAMSCHEME_FINDINGS_20260903.md`
- `CELSYS_VECTOR_SERIALIZATION_FINDINGS_20260903.md`
- `CSMC_P4_RECORD_SECTION_BOUNDARY_20260912.md`
- `CSMC_P4_REFINED_STATIC_ANCHOR_MAP_20260912.md`
- `CSMC_P4_197_195_BOUNDARY_BRACKETING_20260913.md`
- `CSMC_P4_197_195_OWNER_CONSUME_BRACKET_20260913.md`
- `CSMC_STRUCTURAL_IR_V01_CURRENT_EXAMPLE_20260913.json`
- `CSMC_P4_TRANSITION_OBJECT_197_195_FINDINGS_20260913.md`
- `CSMC_P4_OWNER_SCOPE_MATRIX_20260913.md`

## Explicit edge inventory

### `EXPLICIT_PARENT_RECORD_BOUNDARY`

**NOT PRESENT in the current durable metadata.**

The exact-qword extinction island is sharply bracketed by reused endpoints and the +197/+195 phase switch, but no saved static report identifies those endpoints as the start/end of a named parent record. The +965 48/49-qword record lattice is a different child grammar and cannot exactly tile the 378–382-qword barrier window.

### `EXPLICIT_PARENT_LENGTH_FIELD`

**NOT PRESENT in the current durable metadata.**

Earlier bounded checks found no obvious LE/BE 32-bit literal for selected candidate sizes in checked ±512-byte windows. This is only a negative for obvious literal fields; it does not prove that no encoded/indirect length exists.

### `EXPLICIT_CONSUMER_CROSSREF`

**NOT PRESENT in the current durable metadata.**

P1/P2 resolves the outer live path to `Canvas3DModelLoader.ModelData -> catalog_character` and CSMC `character`, but there is no static cross-reference from `BND_197_TO_195` to a named inner consumer function.

`ModelInfo3D` / `ModelNodeInfo3D` provide a useful latent semantic dictionary but are schema-only in this target and do not supply a live inner route. `Manager3D`/`ModelInfoFirstIndex` similarly does not establish an inner `character` record boundary for this document.

## Important correction / evidence weighting

The longest raw exact runs at `+197` and `+195` are low-complexity repeated-block spans and must not be treated as semantic owner evidence. The boundary ranking instead relies on:

- unique-once anchor populations,
- reused immediate endpoints,
- complete cross-serialization qword extinction inside the bridge,
- clean `+197 -> none -> +195` phase switch,
- later recurrence of +195 unique-once islands,
- near-conserved 380/378-qword gap size.

## Gate consequence

The correct status is **not** `STATIC_FULLY_EXHAUSTED`.

It is:

`EXPLICIT_EDGE_NOT_FOUND_IN_CURRENT_DURABLE_METADATA__AGGREGATE_STATIC_CONTINUES`

Why:
- the exact authorized raw pair is not currently available in the execution environment for new direct file-side probes;
- aggregate-only deductions remain possible, including structural-family compatibility and owner-scope constraints;
- therefore V4.4/no-change Save remains inert.

A later runtime trace becomes eligible only when the remaining question is specifically a consumer cross-reference that static/aggregate evidence cannot reduce further. Even then the pre-existing fail-closed `BOUNDARY_TRANSITION_EVENT` contract requires exactly one serialization trigger and one narrow diagnostic, never a return to broad memory/GUID scanning.

## Claim boundary

No parent record has been decoded. No parent length encoding has been decoded. No consumer function has been named. No vertex/index/UV/material/bone/weight, codec/encryption/DRM, or real Blender-import claim is made.
