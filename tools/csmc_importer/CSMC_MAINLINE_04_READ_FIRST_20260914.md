# CSMC MAINLINE 04 — READ FIRST

Status: `HANDOFF_POINTER__FULL_HANDOFF_IN_DRIVE`

This is the public-safe pointer for the complete Mainline 04 handoff. The complete handoff preserves the Mainline 01→02→03 structural lineage, controlled fixture corpus, DATA2 envelope, phase-normalized Structural IR, 307-qword cadence, rejected-family registry, Importer Lab state, F02 mutation-oracle packet, MODELER 1.10.13 static evidence, Companion C history through GitHub-latest C-069, Data Scout usage rules, external-store integration, safety boundaries, current unresolved gates, immediate next actions, and long-term Blender importer roadmap.

## Complete handoff

- filename: `CSMC_MAINLINE_04_HANDOFF_COMPLETE_20260914.md`
- Google Drive ID: `1nqRrIWiUP9vYcxam1lG9OFa3AH95JnQj`
- SHA-256: `72d2f81401abaec2c0979bc0c9eb9dafba06617e4021f7ee082e6674c196b988`
- size: `37424` bytes

## Authority rule

At restart, reconcile this handoff against the newest durable state before acting:

1. Supabase latest `HANDOFF_CURRENT`
2. GitHub mainline/static/Companion/F02 branches
3. Drive current checkpoint
4. Base44 ExperimentLineage
5. Linear lane state

Newest validated evidence supersedes stale pointer fields; historical evidence remains history.

## Current baseline at handoff creation

- mainline branch: `csmc-importer-experimental-20260902`
- mainline HEAD: `7f7632d1894c36d5a9802b19f7150b820a6b4601`
- static branch: `csmc-modeler-static-analysis-second-pass-20260914`
- static HEAD: `fa3c3a7af57342eee9178cd78a65c11a83f8c471`
- F02 oracle HEAD: `5db89bc6f0ca20dcb2646b89202ead6b8b53bde2`
- Companion C GitHub latest observed: `0bda454a693c8185439e7e583643c0dc9ac7f490` (`C-069` full-snapshot evidence record)
- prior canonical pointer before Mainline 04: Supabase row `208`

Current gates:

- MAINLINE = ACTIVE
- STRUCTURAL DEVELOPMENT = ACTIVE
- pipeline = STRUCTURAL_ONLY
- semantic gate = CLOSED
- semantic promotion = 0
- geometry/index = UNRESOLVED
- Blender emit = BLOCKED
- runtime dispatch = false
- physical F02 oracle = 0/30 PENDING_MANUAL_ORACLE

## Highest-value next action

Use the hash-verified MODELER 1.10.13 full static snapshot to trace narrowly from the two newly CONFIRMED architecture edges:

- `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP` at `0x140d175d0`
- `EXPLICIT_MODELDATA_LOOKUP` at `0x140d45d30`

Toward:

`EXPLICIT_SERIALIZER_FIELD_READ -> width/endian/count-or-length -> destination -> internal construction -> CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`.

Do not restart broad string/name searches. Do not use public `.clip` names to guide the sealed blind pass. Do not perform Save/Ctrl+S in the F02 physical oracle. Do not promote semantics or enable Blender emit before the mainline evidence gate closes.
