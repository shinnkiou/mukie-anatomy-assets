# CSMC NEXT CHAT — READ FIRST — 2026-09-15

Newest canonical restart pointer:

- Supabase `HANDOFF_CURRENT`: row **223**
- run key: `CSMC_NEXT_CHAT_HANDOFF_20260915_0924_JST`
- Drive handoff MD: `19J-LKcD_-igTdevd00Yot8wEKODI3kB-`
- Base44 handoff: `6aa8912945eb8a9401f3a27d`
- full GitHub handoff branch: `csmc-next-chat-handoff-20260915-0924`
- full GitHub handoff commit: `c542567c7068c6c99f3f902184f63055480099d4`
- prior row218 is superseded as current pointer only; its targeted-static intake contract remains valid historical input.

Current scientific state remains fail-closed:
- `STRUCTURAL_ONLY`
- semantic promotion = 0
- Blender emit = BLOCKED
- runtime dispatch = false
- F02 = `0/30 PENDING_MANUAL_ORACLE`
- `DQ-BRIDGE-LOADER-SER-01 = WAIT_FOR_BRIDGE_PROOF`
- `DQ-SER-WIDTH-01 = WAIT_FOR_PROOF`
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION = UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`

Scope-aware constraints:
- C01 ExternalChunk keyed Offset lookup
- C02 ModelData -> Canvas3DModelLoader registration/binding
- C03 exact 16-byte container field read
- C04 CHNKSQLi decoded-length bounded stream copy

C03/C04 are container-scope only and cannot answer the ModelData serializer width question.

New focused archive received:
`CSMC_FULL_SNAPSHOT_FOCUSED_20260914_232435.zip`
SHA-256: `b07a02ac3fd15198288588f15092c1bd94bbd17512e05353a712d0333a76d678` (recalculation MATCH)
Status: `RECEIVED_CHECKSUM_VERIFIED_NOT_YET_SCIENTIFICALLY_ADMITTED`.

Restart procedure:
1. read Supabase row223;
2. read the full handoff above;
3. retain row220 as supplemental C-069 evidence without double-counting the run ID;
4. run the focused archive through the existing fail-closed targeted-static intake/review;
5. attempt `DQ-BRIDGE-LOADER-SER-01` before `DQ-SER-WIDTH-01`;
6. do not mutate RIO-26 state, MODELER runtime/save, Worker/Canary/Production/STABLE, semantic promotion, or Blender emit.
