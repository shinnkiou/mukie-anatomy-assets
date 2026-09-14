# CSMC MAINLINE 04 — READ FIRST

Status: `HANDOFF_POINTER__ROW218__TARGETED_STATIC_INTAKE_READY`

This file is the public-safe restart pointer. Historical detail remains in the complete Mainline 04 handoff, prior checkpoints, and Git history. At restart, newest validated durable state wins over stale chat memory.

## Current canonical pointer

- Supabase `HANDOFF_CURRENT`: row **218**
- run key: `CSMC_TARGETED_STATIC_EXTRACTION_INTAKE_GATE_V1_20260915`
- classification: `TARGETED_STATIC_INTAKE_GATE_VERIFIED_NO_NEW_EVIDENCE`
- predecessor row 217: `HANDOFF_SUPERSEDED`
- Base44 ExperimentLineage: `6aa8128c6687e989beef27a4`
- GitHub gate commit: `77415f789a6c3a9fa33c044bb2574eeab459b4d2`
- targeted intake CI `34862082867`: **SUCCESS**
- importer smoke `34862082732`: **SUCCESS**
- Drive checkpoint MD: `17qHMtLYyl9n2l4tqDG1CR6NzwGS0KjaL`
- Drive checkpoint JSON: `1WlGI63Ijc12Mlu1vy01MU-F0FhP3qxSK`
- checkpoint MD SHA-256: `025dd8ccb2b783f8119a4c937db0228a7e44f0b54989b2ccf5a25116c876866c`
- checkpoint JSON SHA-256: `c6d335a09acc1594a0244645833450d7c8adab0e1ed9ef5ef4d6f3c4863873cb`

## Campaign state retained from row217

The semantic-binding campaign localized the next proof gap but did not close it.

- C02 confirmed registration anchor: `0x140d45d30` (`ModelData -> Canvas3DModelLoader`)
- bounded reader lead: `0x140f62d20`
- bounded transfer lead: `0x140f650c0`
- `modeldata` string VA: `0x14195fb88`
- `PW3DModelDataLoader` vftable label: `0x14195fad0`
- `PWCanvas3DModelLoader` vftable label: `0x1417f6d30`
- direct-call bridge paths from C02/registry helper to candidate set: 0; this is a negative control, not a rejection of factory/vtable/indirect dispatch

Campaign durability repair:
- raw Drive MD: `1qh1m7910k0xHQoao-QBcmwmmrBrtiC5B`
- raw Drive JSON: `1_58ORbnvmErfwFYSZ2uvRp8xxMAKCXw1`
- the old native Doc `1ujbhlFwR7OamWCReQxlsT0cxYH4iuphI-6MDtFUhUZ0` is explicitly quarantined as `SUPERSEDED_EMPTY_RATE_LIMITED__...` and must not be treated as the checkpoint body.

## Fail-closed targeted static intake

The private static extension request is frozen at:
`tools/csmc_importer/semantic_binding_campaign/CSMC_TARGETED_STATIC_EXTRACTION_REQUEST_V1_20260914.md`

The intake contract is:
`tools/csmc_importer/semantic_binding_campaign/CSMC_TARGETED_STATIC_EXTRACTION_INTAKE_CONTRACT_V1.json`

Validator:
`tools/csmc_importer/semantic_binding_campaign/csmc_targeted_static_extraction_intake.py`

Required exact source identity:
- MODELER 1.10.13 SHA-256 `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`
- baseline Full Snapshot SHA-256 `afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342`

Required function exports:
- `0x140f62d20`
- `0x140f64600`
- `0x140f650c0`
- `0x140f622f0`
- `0x140f63200`
- `0x140f635d0`

Also require both 9-slot candidate vtable interval dumps, factory trace rooted at `0x141656a80`, and conditional exports for `0x141658300` / `0x1416586f0` only when resolution points to them.

A package that passes intake receives only:
`INTAKE_COMPLETE_STATIC_REVIEW_REQUIRED`

Passing intake does **not** automatically admit the bridge, proof-grade status, `EXPLICIT_SERIALIZER_FIELD_READ`, semantic promotion, or Blender emit.

## Current proof gates

- MAINLINE = ACTIVE
- STRUCTURAL DEVELOPMENT = ACTIVE
- pipeline = `STRUCTURAL_ONLY`
- semantic gate = CLOSED
- semantic promotion = 0
- `DQ-BRIDGE-LOADER-SER-01 = WAIT_FOR_BRIDGE_PROOF`
- `DQ-SER-WIDTH-01 = WAIT_FOR_PROOF`
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION = UNRESOLVED`
- geometry/index = UNRESOLVED
- Blender emit = BLOCKED
- runtime dispatch = false
- F02 physical oracle = `0/30 PENDING_MANUAL_ORACLE`
- frozen F02 questions resolved = `0/5`

F02 Sentinel-9 remains:
`M01, M10, M13, M14, M15, M18, M22, M23, M30`.
`M14` is information-gain proposal only; next physical operation remains `M01`.

## Important historical anchors

- complete Mainline 04 handoff Drive: `1nqRrIWiUP9vYcxam1lG9OFa3AH95JnQj`
- complete handoff SHA-256: `a36be2381b64ac0c759b7f959cf0653124277a64064698d575c922db7354bcca`
- canonical C-069: Supabase row `209`; duplicate row213 is audit-only
- consumer-constrained phase: row `210`
- V12: row `211`
- Mainline04 complete pointer: row `212`
- width-gate pointer: row `214`
- bridge-gate durability: row `215`
- sealed cross-lane compare: row `216`
- semantic-binding campaign: row `217`
- targeted static intake gate: row `218`

Confirmed architecture anchors remain:
- `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP` at `0x140d175d0`
- `EXPLICIT_MODELDATA_LOOKUP` / C02 at `0x140d45d30`

C-069 BE-u64 reads remain scoped to the CHNKSQLi/ExternalChunk corridor and are not ModelData serializer width evidence without the provenance bridge.

## Next action

Receive the exact private targeted static extraction package, run it through the intake validator, and then conduct a separate static proof review for `DQ-BRIDGE-LOADER-SER-01`.

Do not broaden into blind string/name search. Do not use public `.clip` names to select/score the sealed target. Do not launch or save in MODELER from this lane. Do not mutate Worker/Canary/Control Gate/Production/STABLE or RIO-26. Do not promote semantics or enable Blender emit before the evidence gate closes.
