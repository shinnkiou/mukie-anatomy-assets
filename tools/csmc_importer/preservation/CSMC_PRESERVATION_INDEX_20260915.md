# CSMC PRESERVATION INDEX — 2026-09-15

Status: `DURABILITY_ONLY__NO_ANALYSIS_ADVANCE`

## Scope

This preservation packet covers read-only interoperability and format-analysis work on software and self-authored or authorized data. It does not authorize DRM/license/authentication bypass, credential access, process injection, memory writes, unauthorized access, persistence, malware, or redistribution of proprietary binaries/raw proprietary model bytes.

## Purpose

Reduce loss risk. This file does not advance analysis, merge independent lanes, promote semantics, enable Blender production emit, or change runtime state.

## Canonical restart boundary

Current canonical Mainline state:
- Supabase row `218`
- run key `CSMC_TARGETED_STATIC_EXTRACTION_INTAKE_GATE_V1_20260915`
- status `HANDOFF_CURRENT`
- Mainline GitHub head `db2d3c2322ce6db0a62d6bebbd68436559862579`
- pipeline `STRUCTURAL_ONLY`
- semantic gate `CLOSED`
- semantic promotion `0`
- Blender emit `BLOCKED`
- runtime dispatch `false`

Post-current independent Companion artifact:
- Supabase row `220`
- run key `CSMC_ANALYSIS_C_C069_FULL_SNAPSHOT_INDEPENDENT_20260915`
- GitHub commit `239c1a265c2b96ffa765b62b813bd7af53f356fe`
- preserve separately; explicit cross-lane reconciliation is required before any integration

Durability/restart handoff:
- Supabase row `221`
- run key `CSMC_WORK_INTERRUPTED_SEMANTIC_BINDING_HANDOFF_20260915_0041JST`
- GitHub commit `062e9aa914c4d221f919f8e8f345af792f580eb5`
- Drive handoff `1IwZlnTLSbnH7LA4Eaysi9m6tRYJkXmO2`
- Base44 `6aa81764a6cdbb9fe0387784`
- does not supersede row 218

## Major durable checkpoints

- row 207: full MODELER static snapshot reconciliation
  - snapshot ZIP SHA-256 `afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342`
  - MODELER executable SHA-256 `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`
  - static head `fa3c3a7af57342eee9178cd78a65c11a83f8c471`
- row 208: Importer Lab V11 / Mainline03 external endpoint
  - Drive MD `1gvwwhssPqWfjRKxZitjQNdVxrW23pBfs`
  - Drive JSON `1H_MWImhZoqiJQ3ZB-J4QHQBGApZNbFt2`
  - Base44 `6aa800e15ce2b9befd257127`
- row 209: earlier canonical C-069 durability record; do not double-count with later mirrors
- row 210: consumer-constrained phase, 50 proposals -> 43 unique survivors after hard rejection/deduplication
- row 211: V12 lane-current checkpoint, semantic gate still closed
- row 212: Mainline04 complete handoff
  - Drive `1nqRrIWiUP9vYcxam1lG9OFa3AH95JnQj`
  - SHA-256 `a36be2381b64ac0c759b7f959cf0653124277a64064698d575c922db7354bcca`
- rows 214-216: fail-closed discrimination, provenance-bridge, and cross-lane comparison checkpoints
- row 217: semantic-binding campaign checkpoint, fail-closed, no proof-grade semantic binding
- row 218: current targeted-static intake gate
- row 219: historical Mainline03 reconstruction only
- row 220: sealed independent Companion artifact, not silently integrated
- row 221: work-interruption durability handoff

## Row 218 Drive artifacts

- checkpoint MD `17qHMtLYyl9n2l4tqDG1CR6NzwGS0KjaL`
- checkpoint JSON `1WlGI63Ijc12Mlu1vy01MU-F0FhP3qxSK`
- campaign MD `1qh1m7910k0xHQoao-QBcmwmmrBrtiC5B`
- campaign JSON `1_58ORbnvmErfwFYSZ2uvRp8xxMAKCXw1`
- Phase-B scope MD `1QP29M2xxJDVbpGgDuNHV9ZCRHIll6bcU`
- Phase-B scope JSON `1n7sxtB8O1cSdLRUAZpKcu5DYEjeUmWgE`
- Base44 `6aa8128c6687e989beef27a4`

## Row 220 independent Companion seal

- GitHub branch `csmc-analysis-companion-c-fullsnapshot-independent-20260915`
- GitHub commit `239c1a265c2b96ffa765b62b813bd7af53f356fe`
- Drive report `1prJRYq2gsSPL0lMI-vVuNMdPMiU3pqQM`
- Drive evidence `1lRX2rkUxZdJVQxuOEh20w3uYEoAMgM7I`
- Drive questions `1dWmCZ1tulfUsZveG8c-9cNZ7t90SirxL`
- Drive seal manifest `1cQL5IyCQTN4rf8b0VUq9-FpZLmRItf2X`
- report SHA-256 `675dabb50817267fcc0c521e2457275f17e879226684c4c435efb222800dd6ee`
- evidence SHA-256 `1b04b86cb44a86fc56c35b20664e842f1d2aa96322c18be2f9a32f4e35e2362f`
- questions SHA-256 `b6d06410fcb1ed478f0bcbcd996d0bc9f5db18a13c1f1be3dea88ac63598a082`
- seal SHA-256 `2f3f0eb7bc3af47278957c3b70a5856a5291664e6197e9ab59c55e3bc1c294dd`

## Companion / oracle pins

- Companion comparison branch `csmc-analysis-companion-c-20260913`
- comparison head `fb508778733f41083f4c8a9f64041f9467659d06`
- F02 branch `csmc-f02-mutation-oracle-intake-20260914`
- F02 head `5db89bc6f0ca20dcb2646b89202ead6b8b53bde2`
- physical observations `0/30`
- status `PENDING_MANUAL_ORACLE`

## Unresolved proof gates

Still unresolved and not to be promoted from names, proximity, synthetic scores, or visual plausibility:
- `EXPLICIT_SERIALIZER_FIELD_READ`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION`
- geometry semantic binding
- index topology semantic binding
- current loader-to-serializer bridge proof
- current serializer-width proof

## Historical Mainline03 reconstruction

- Supabase row `219`
- Drive `1zm7GtQ5NatHkE16rMTQKZVXdX86G9ZAI1ZbeHhvblt8`
- GitHub archive branch `csmc-mainline03-handoff-reconstructed-20260915`
- handoff commit `06d67d564b8cae0cee1b36ef19a460d37812ce0f`
- durability index commit `940466e60d4a24b77bd257cd2dc46a0c761b4d75`
- historical only; does not supersede current Mainline state

## Preservation pins created for this stop point

- Mainline preservation branch `csmc-preservation-snapshot-20260915`, anchored from `db2d3c2322ce6db0a62d6bebbd68436559862579`
- Companion preservation branch `csmc-preservation-companion-c069-20260915`, anchored from `239c1a265c2b96ffa765b62b813bd7af53f356fe`
- Drive preservation folder `CSMC_PRESERVATION_20260915`, folder ID `1TtmR4Kiu-YbyLzcT4ZYQHHp39MSsEvbA`

## Audit-only sources

Gmail contains historical GitHub workflow failure notifications. They are useful for provenance/debug history but are not scientific proof. Google Calendar currently contributes no CSMC event/state evidence.

## Restart rule

1. Read row 218 first as canonical Mainline state.
2. Read row 221 as the durability/restart handoff; it does not supersede row 218.
3. Read row 220 separately as sealed independent Companion evidence; do not auto-merge.
4. Verify GitHub preservation branches and the Drive preservation folder.
5. Preserve `semantic_promotion = 0`, `semantic_gate = CLOSED`, Blender emit blocked, and runtime false until a separately admitted proof-grade transition exists.

This index deliberately preserves ambiguity rather than collapsing independent or duplicate records into stronger claims.
