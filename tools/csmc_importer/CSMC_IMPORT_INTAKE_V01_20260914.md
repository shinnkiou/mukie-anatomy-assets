# CSMC Mainline — Import Intake v0.1 — 2026-09-14

## Question

Can the validated controlled-fixture DATA2 outer envelope be connected to the existing CSMC importer entry path without changing Structural IR meanings or prematurely enabling content semantics / Blender emit?

## Result

YES, at the structural intake layer only.

`csmc_import_intake.py` joins two independently existing mainline components:

1. `csmc_core.probe()` — SQLite/container route and legacy public-safe metadata.
2. `csmc_controlled_envelope.parse_csmc_file()` — the 13-fixture validated DATA2 envelope contract.

The adapter accepts a CSMC only when both parsers agree on:

- source file SHA-256
- `character.character` route
- outer version
- magic/kind
- GUID field
- inner version
- logical length
- stored length
- payload offset
- available payload size

It additionally requires the controlled-corpus frame rule:

`stored_length = align8(logical_length) + 8`

## Fail-closed behavior

The public output contains hashes and structural metadata only.

It does NOT expose payload bytes, source/private paths, literal qwords, geometry/index values, or decoded content.

The intake result is hard-gated to:

- `pipeline_stage = STRUCTURAL_ONLY`
- `semantic_promotion_count = 0`
- `geometry = unresolved`
- `index_topology = unresolved`
- `blender_emit_ready = false`

Rejected conditions include:

- wrong SQLite route/column for this controlled contract
- envelope/core disagreement
- wrong frame-length relationship
- truncated payload

## Synthetic regression

`test_csmc_import_intake_synthetic.py` covers:

1. valid controlled-route intake
2. wrong route rejection
3. wrong `align8+8` rule rejection
4. truncated payload rejection
5. no raw payload/source path in public output
6. Blender emit and semantic promotion remain closed

## Companion C C-051 / C-052 reconciliation

Newer Companion C runs were checked reference-only after the previous C-050 reconciliation.

- C-051: preregisters seven stricter same-identity controls for material/object/UV/weight discrimination.
- C-052: adds a Blender teacher-manifest realization validator.
- Both explicitly report that the new source manifest / CSMC evidence has NOT yet been acquired.
- Therefore these runs do not add new CSMC semantic evidence and do not change the current Level-4 render-part candidate or any semantic gate.

Mainline does not copy the side-branch implementation and does not treat predictions as observations.

## Current importer boundary

Implemented now:

`SQLite container -> character route -> DATA2 envelope -> public-safe structural intake`

Still blocked:

`opaque payload -> geometry/index semantic streams -> Blender mesh emit`

The next content-level importer slot remains geometry/index localization under controlled evidence. No runtime/MODELER/Worker action is authorized by this intake integration.
