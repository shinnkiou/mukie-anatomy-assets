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

Focused archive expected:
`CSMC_FULL_SNAPSHOT_FOCUSED_20260914_232435.zip`
SHA-256: `b07a02ac3fd15198288588f15092c1bd94bbd17512e05353a712d0333a76d678`
Prior handoff reports checksum recalculation MATCH, archive size 12,235,062 bytes, and 244 contained files.
Status remains: `RECEIVED_CHECKSUM_VERIFIED_NOT_YET_SCIENTIFICALLY_ADMITTED`.

## Structural continuation after row223 — archive-integrity hardening

The connected Drive/File Library views expose the handoff and checksum sidecar but not the focused ZIP bytes themselves. Therefore no claim is made that the real focused archive has been re-read or scientifically reviewed in this session.

A second fail-closed package-integrity layer was added before static evidence review:

- archive verifier: `tools/csmc_importer/semantic_binding_campaign/csmc_targeted_static_archive_integrity.py`
- package CLI: `tools/csmc_importer/semantic_binding_campaign/validate_csmc_targeted_static_package.py`
- synthetic tests: `tools/csmc_importer/semantic_binding_campaign/test_csmc_targeted_static_archive_integrity.py`
- CI head: `a350ae83842860075f3c2efe64f524236da618ff`
- CI run: `34950979467` = **SUCCESS**

The new layer verifies the actual ZIP SHA-256, safe member paths, duplicate paths, symlinks, encrypted entries, size bounds, executable/PE-like embedding guards, optional exact member count, and that every decompile/instruction SHA declared by the manifest is backed by real archive bytes. It never extracts the archive to disk.

Even after package-integrity success:
- `bridge_admitted = false`
- `proof_grade = false`
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- semantic promotion = false
- Blender emit = false
- runtime dispatch = false

This structural hardening does not change row223's scientific state and does not close any proof gate.

Restart procedure:
1. read Supabase row223;
2. read the full handoff above;
3. retain row220 as supplemental C-069 evidence without double-counting the run ID;
4. obtain the exact focused ZIP bytes and re-check SHA-256 plus the expected 244-member inventory through the archive-integrity gate;
5. validate the targeted extraction manifest and bind all declared decompile/listing SHA values to real archive members;
6. only then perform static review for `DQ-BRIDGE-LOADER-SER-01`;
7. attempt `DQ-SER-WIDTH-01` only after a provenance-bound bridge is admitted;
8. do not mutate RIO-26 state, MODELER runtime/save, Worker/Canary/Production/STABLE, semantic promotion, or Blender emit.
