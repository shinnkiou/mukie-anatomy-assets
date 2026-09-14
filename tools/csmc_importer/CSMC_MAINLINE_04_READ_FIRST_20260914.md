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

Supabase writes were unavailable during the latest reconciliation because the connector safety layer blocked SQL execution. Therefore row218 remains the canonical pointer; this is intentional and not evidence loss.

## Supplemental row220 reconciliation — 2026-09-15

A later independently sealed Companion packet exists at Supabase row `220` / Base44 `6aa814d1558760c2d7131e48` / GitHub `239c1a265c2b96ffa765b62b813bd7af53f356fe`.

Important identity rule:
- row209 and row220 both use logical run name `C-069`;
- their sealed hashes differ;
- preserve both provenance chains;
- do **not** count row220 as a second numbered run;
- disambiguate by Supabase row/date/hash and do not silently merge them.

Two additional direct structural facts are admitted as scope-aware falsification constraints only:

- C03 `CONTAINER_16B_FIELD_READ_CONFIRMED`: at `0x140d15a90`, object-relative `param_1+0x1e` is ensured/resized to exactly 16 bytes by `0x1408c0d40` and `0x1408c27c0` transfers exactly 16 bytes into it. Scope: `CSFCHUNK_CONTAINER_FIELD`. Meaning remains unresolved.
- C04 `CHNKSQLI_LENGTH_BOUNDED_STREAM_COPY_CONFIRMED`: after CHNKSQLi validation, a decoded u64 byte length drives `remaining -> min(remaining,capacity) -> exact transfer -> remaining decrement`. Scope: `CHNKSQLI_CONTAINER_TRANSFER`.

Scope firewall:
- C03/C04 do not prove ExternalID, UUID, checksum, ModelData serializer width/endian/count, geometry, index, UV, material, bone, weight, or internal construction;
- the 16-byte read cannot answer `DQ-SER-WIDTH-01`;
- the CHNKSQLi BE-u64 length cannot answer ModelData serializer width/endian/count;
- typed `ODCChunkCellImporterT` RTTI remains architecture-only until loader reachability is proven.

Question alignment only:
- Companion row220 DQ-02 aligns with `DQ-BRIDGE-LOADER-SER-01`;
- Companion row220 DQ-03 aligns only after bridge admission with `DQ-SER-WIDTH-01`;
- alignment does not import an answer or change semantic confidence.

Durability:
- GitHub reconciliation commit `3f28c584578ba46c16e3871609ec0fbc9e425a43`
- GitHub `CSMC_CONSUMER_CONSTRAINT_PACK_V2.json` commit `cd67bbcfb5fab6c120c16fee24c34e37ddc88b08`
- Drive reconciliation Doc `1Pu8o__Jl7gjPNfXTKWVByKkLC9NkvDoE2PtDIF8PpAc`
- Base44 reconciliation `6aa81967dcd48ddc72ee893f`
- Linear RIO-48 `81a75f8d-a874-44c2-a88b-fcfcbe494728`
- Linear RIO-58 `0d959f35-3593-4a96-afd9-a0b0bb37d1eb`
- Linear RIO-56 `69fb99fd-3de1-4760-b9d2-b2244f3bc921`
- Linear RIO-59 `1bfab1ff-21fd-49ea-8efc-160c2227063b`

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
- older sealed C-069: Supabase row `209`; duplicate row213 is audit-only
- supplemental sealed C-069 packet: row `220`, explicitly reconciled above, not a second numbered run
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

C-069 container BE-u64 reads remain scoped to the CHNKSQLi/ExternalChunk/container corridor and are not ModelData serializer width evidence without the provenance bridge.

## Next action

Receive the exact private targeted static extraction package, run it through the intake validator, and then conduct a separate static proof review for `DQ-BRIDGE-LOADER-SER-01`.

Do not broaden into blind string/name search. Do not use public `.clip` names to select/score the sealed target. Do not launch or save in MODELER from this lane. Do not mutate Worker/Canary/Control Gate/Production/STABLE or RIO-26. Do not promote semantics or enable Blender emit before the evidence gate closes.
