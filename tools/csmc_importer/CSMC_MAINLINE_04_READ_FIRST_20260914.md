# CSMC MAINLINE 04 — READ FIRST

Status: `HANDOFF_POINTER__FULL_HANDOFF_IN_DRIVE__V12_RECONCILED`

This is the public-safe pointer for the complete Mainline 04 handoff. The full handoff preserves Mainline 01→02→03 structural lineage, controlled fixtures, DATA2 envelope, phase-normalized Structural IR, 307-qword cadence, bounded rejected families, Importer Lab, F02 oracle, MODELER 1.10.13 static evidence, Companion C through C-069, Data Scout rules, plugin/store integration, immediate continuation and long-term CSMC→Blender roadmap.

## Complete handoff

- filename: `CSMC_MAINLINE_04_HANDOFF_COMPLETE_20260914.md`
- Google Drive ID: `1nqRrIWiUP9vYcxam1lG9OFa3AH95JnQj`
- SHA-256: `a36be2381b64ac0c759b7f959cf0653124277a64064698d575c922db7354bcca`
- size: `40227` bytes

## Authority rule

At restart, reconcile this handoff against the newest durable state before acting. Newest validated evidence supersedes stale pointer fields; historical evidence remains history.

Read first:
1. Supabase latest `HANDOFF_CURRENT`
2. rows 209/210/211/212 specifically
3. GitHub mainline/static/Companion/F02 branches
4. Drive current checkpoint/handoff
5. Base44 ExperimentLineage
6. Linear lane state

## Current baseline at handoff creation

- mainline branch: `csmc-importer-experimental-20260902`
- consumer implementation commit: `f7e2e69d52fa39e5eaa6074611ec4688d9773a7b`
- previous visible pointer HEAD: `caf8c93593614c53f32c56ac725932cd30c88cc2`
- static branch: `csmc-modeler-static-analysis-second-pass-20260914`
- static HEAD: `fa3c3a7af57342eee9178cd78a65c11a83f8c471`
- F02 oracle HEAD: `5db89bc6f0ca20dcb2646b89202ead6b8b53bde2`
- Companion C: C-069 durable in Supabase row `209`
- Importer Lab consumer-constrained phase: row `210`
- V12 canonical before Mainline 04: row `211`
- Mainline 04 current pointer: row `212`

V12 / row210 adds scope-aware hard falsification constraints from the two confirmed architecture edges. Synthetic proposals 50 → 3 explicit contradictions rejected → 4 behavioral duplicates removed → 43 unique survivors, no refill. `CONSUMER_COMPATIBLE != SEMANTIC_CONFIRMED`.

Next frozen discriminator: `DQ-SER-WIDTH-01` — determine whether the direct primitive on the confirmed consumer corridor consumes the bounded candidate region as 16-bit or 32-bit, with reader VA, direct primitive, effective width, count/loop source and destination required.

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

Trace narrowly from the two CONFIRMED architecture edges:

- `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP` at `0x140d175d0`
- `EXPLICIT_MODELDATA_LOOKUP` at `0x140d45d30`

Toward:
`EXPLICIT_SERIALIZER_FIELD_READ -> width/endian/count-or-length -> destination -> internal construction -> CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`.

Use C-069 row209 as an independently sealed cross-lane falsification/reference surface; do not silently promote it. Do not restart broad string/name searches. Do not use public `.clip` names to guide the sealed blind pass. Do not perform Save/Ctrl+S in the F02 physical oracle. Do not promote semantics or enable Blender emit before the mainline evidence gate closes.
