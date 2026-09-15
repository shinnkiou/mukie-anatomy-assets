# DURABLE POINTER AFTER HANDOFF PERSISTENCE

- Supabase `HANDOFF_CURRENT`: row **223**
- Base44 handoff: `6aa8912945eb8a9401f3a27d`
- Drive handoff MD: `19J-LKcD_-igTdevd00Yot8wEKODI3kB-`
- GitHub full handoff: branch `csmc-next-chat-handoff-20260915-0924`, commit `c542567c7068c6c99f3f902184f63055480099d4`
- GitHub mainline READ_FIRST pointer: commit `d8f88e7fe5a7b86314b49a37dbe07c08c98f4d4`
- mainline pointer smoke: run `34913401235` = **SUCCESS**
- prior row218 is superseded as the global current pointer; its targeted-static intake contract remains valid historical input.

# CSMC NEXT CHAT HANDOFF — 2026-09-15 09:24 JST

## READ FIRST

This is the restart handoff for the active CSMC / Importer Lab / MODELER static-analysis work.

### Canonical state before this handoff
- Supabase `HANDOFF_CURRENT`: row **218**
- Importer Lab lane current: row **211**
- latest durability-only preservation: row **222**
- GitHub mainline branch: `csmc-importer-experimental-20260902`
- GitHub HEAD: `15478f7476945b26a1a329a852110c5f1d785779`
- importer smoke `34865687512`: **SUCCESS**

### Scientific/proof state
- pipeline = `STRUCTURAL_ONLY`
- MAINLINE = ACTIVE
- STRUCTURAL DEVELOPMENT = ACTIVE
- semantic gate = CLOSED
- semantic promotion = **0**
- Blender emit = BLOCKED
- runtime dispatch = false
- F02 physical oracle = `0/30 PENDING_MANUAL_ORACLE`
- frozen F02 questions = `0/5 resolved`
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION = UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`
- geometry/index topology = UNRESOLVED

## Scope-aware consumer constraints

Confirmed and admissible only inside their own scopes:

- C01 `EXTERNALCHUNK_OFFSET_LOOKUP_CONFIRMED`
- C02 `MODELDATA_CANVAS3D_LOADER_BINDING_CONFIRMED`
- C03 `CONTAINER_16B_FIELD_READ_CONFIRMED`
- C04 `CHNKSQLI_LENGTH_BOUNDED_STREAM_COPY_CONFIRMED`

C03/C04 came from the separately sealed row220 packet. They are container/database-layer structural facts, **not** ModelData serializer semantics.

### Run-ID collision
Supabase row209 and row220 both use logical name `C-069` but have different sealed hashes/provenance. Do not count row220 as a second numbered run. Refer to it as the **row220 supplemental C-069 packet**.

## Current question order

1. `DQ-BRIDGE-LOADER-SER-01 = WAIT_FOR_BRIDGE_PROOF`
2. `DQ-SER-WIDTH-01 = WAIT_FOR_PROOF`

Do not reverse this order. Width/endian/count evidence is useful only after a provenance-bound bridge from C02 / Canvas3DModelLoader to a concrete serializer/importer reader is admitted.

## Targeted static intake

Intake infrastructure is already ready and fail-closed.

Primary requested functions:
- `0x140f62d20`
- `0x140f64600`
- `0x140f650c0`
- `0x140f622f0`
- `0x140f63200`
- `0x140f635d0`

Phase-B conditional ancestry:
- `0x140f5ac20`
- `0x140f5e510`
- `0x140e7c270`
- `0x140e78810`

Factory trace root:
- `0x141656a80`

Passing intake means only `STATIC_REVIEW_REQUIRED`; it does not auto-admit the bridge or serializer field read.

## Newly received focused snapshot

`CSMC_FULL_SNAPSHOT_FOCUSED_20260914_232435.zip`

Checksum provided:
`b07a02ac3fd15198288588f15092c1bd94bbd17512e05353a712d0333a76d678`

Checksum recalculated:
`b07a02ac3fd15198288588f15092c1bd94bbd17512e05353a712d0333a76d678`

**MATCH**

- archive size: 12,235,062 bytes
- contained files: 244
- status: `RECEIVED_CHECKSUM_VERIFIED_NOT_YET_SCIENTIFICALLY_ADMITTED`

The next chat should analyze this archive only through the existing fail-closed targeted intake / static evidence gates. Do not promote anything merely because the archive is focused.

## F02

Frozen Sentinel-9 remains:

`M01 -> M10 -> M13 -> M14 -> M15 -> M18 -> M22 -> M23 -> M30`

Next physical operation remains `M01`. Do not reorder automatically.

## Latest durable refs

- GitHub reconciliation: `3f28c584578ba46c16e3871609ec0fbc9e425a43`
- GitHub consumer constraint pack V2: `cd67bbcfb5fab6c120c16fee24c34e37ddc88b08`
- GitHub READ_FIRST/current HEAD: `15478f7476945b26a1a329a852110c5f1d785779`
- Drive reconciliation Doc: `1Pu8o__Jl7gjPNfXTKWVByKkLC9NkvDoE2PtDIF8PpAc`
- Base44 reconciliation: `6aa81967dcd48ddc72ee893f`
- Linear RIO-48 comment: `81a75f8d-a874-44c2-a88b-fcfcbe494728`
- Linear RIO-58 comment: `0d959f35-3593-4a96-afd9-a0b0bb37d1eb`
- Linear RIO-56 comment: `69fb99fd-3de1-4760-b9d2-b2244f3bc921`
- Linear RIO-59 comment: `1bfab1ff-21fd-49ea-8efc-160c2227063b`

## Restart order

1. Read this handoff.
2. Read GitHub `tools/csmc_importer/CSMC_MAINLINE_04_READ_FIRST_20260914.md`.
3. Read newest Supabase `HANDOFF_CURRENT`.
4. Read the Base44 handoff/current record.
5. Validate and inspect the focused snapshot.
6. Try to close/falsify `DQ-BRIDGE-LOADER-SER-01`.
7. Only after the bridge is provenance-bound, continue to `DQ-SER-WIDTH-01`.
8. Keep F02 and semantic gates frozen unless independent evidence actually closes them.

## Hard prohibitions

- no semantic promotion from C01-C04 alone
- no Blender production emit
- no MODELER Save/Save As/Ctrl+S/serialization trigger
- no runtime hook/patch
- no Worker/Canary/STABLE/Production mutation
- no RIO-26 state mutation
- no double-counting row220 as a second numbered C-069
- no visual similarity as proof
- no reuse of container 16B/u64 evidence as ModelData serializer width evidence
