# CSMC Mainline Canonical Reconciliation — 2026-09-14

## Canonical controlled-fixture state

Current C050 mainline reconciliation remains authoritative for controlled fixtures:

- fixture corpus: 13, hashes verified
- accepted structural candidate: `TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE`
- confidence: Level 4
- mode: `STRUCTURAL_ONLY`
- semantic promotion count: 0
- geometry/index/UV/material/bone/weight semantics: unresolved
- `semantic_projection=false`
- `blender_emit_ready=false`
- no general new-fixture collection unless a clean single-variable test has proven information value

## MODELER 1.10.13 FIRST PASS evidence intake

The following consumer-side facts are now CONFIRMED supporting evidence:

1. `EXPLICIT_PARENT_LENGTH_FIELD`
2. `EXPLICIT_PARENT_RECORD_BOUNDARY`
3. `EXPLICIT_CONSUMER_CROSSREF` (`ModelData -> Canvas3DModelLoader`)

They strengthen parent framing and consumer routing only. They do **not** promote any payload field to geometry, topology, UV, material, bone, or weight semantics.

`CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`

SECOND PASS A-G remain reference-only and are not a mandatory mainline queue.

## Engineering continuation

The outer character envelope parser already exists and is fail-closed. The public-safe 307-qword cadence detector also exists. The next importer-facing integration is therefore a structural intake sidecar which composes those existing components without duplicating their logic.

Added:

- `csmc_structural_importer_intake.py`
- `test_csmc_structural_importer_intake_synthetic.py`

The sidecar records:

- validated container frame
- public-safe cadence result
- Level-4 2456-byte/307-qword cardinality candidate when detected
- three MODELER FIRST PASS supporting evidence IDs
- all semantic domains unresolved
- zero semantic promotions
- runtime disabled
- Blender emit disabled

This advances parser/importer integration while preserving the current semantic gate.
