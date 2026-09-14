# CSMC MAINLINE 04 — READ FIRST

Status: `HANDOFF_POINTER__POST_MAINLINE04_DQ_GATE__ROW214_CURRENT`

This is the public-safe pointer for the complete Mainline 04 handoff plus its latest validated incremental checkpoint. The full handoff preserves Mainline 01→02→03 structural lineage, controlled fixtures, DATA2 envelope, phase-normalized Structural IR, 307-qword cadence, bounded rejected families, Importer Lab, F02 oracle, MODELER 1.10.13 static evidence, Companion C through C-069, Data Scout rules, plugin/store integration, immediate continuation and long-term CSMC→Blender roadmap.

## Complete handoff

- filename: `CSMC_MAINLINE_04_HANDOFF_COMPLETE_20260914.md`
- Google Drive ID: `1nqRrIWiUP9vYcxam1lG9OFa3AH95JnQj`
- SHA-256: `a36be2381b64ac0c759b7f959cf0653124277a64064698d575c922db7354bcca`
- size: `40227` bytes

## Post-handoff incremental current

- checkpoint: `CSMC_MAINLINE_04_DQ_SER_WIDTH_GATE_CHECKPOINT_20260914.md`
- Supabase: row `214` = `HANDOFF_CURRENT`
- previous Mainline04 row `212` = `HANDOFF_SUPERSEDED`
- concurrent row `213` = C-069 duplicate durability mirror, explicitly superseded by canonical row `209`; do not count it as new evidence
- Base44: `6aa809f72e72c2eeacd8a008`
- Drive checkpoint: `1alSc76KRZj_GoLV8yGZr62xDFh-Z28xC`
- Drive checkpoint SHA-256: `855e2609c87666b75cb78dca4d59f7743740279c0b995b6af7f7cc2736c651f4`
- Drive checkpoint size: `5305` bytes
- tested gate code head: `e7cb837dce73a726d0e800b54940d5ba7d262f03`
- gate CI: `34858073131` = `SUCCESS`
- checkpoint commit: `f3a43ca6f76048a8c01a2f35c83c5a8c0830d369`

The new gate does **not** answer 16-bit vs 32-bit. `DQ-SER-WIDTH-01` remains `WAIT_FOR_PROOF`. It only makes future proof intake fail-closed:

- no/incomplete/CANDIDATE/STRONG-only/wrong-binary evidence => no hard width pruning;
- a complete CONFIRMED serializer field-read may structurally answer DQ-SER-WIDTH-01;
- actual F02 candidate pruning additionally requires explicit binding to controlled fixture `F02` and `F02_DATA2_VARIABLE_PREFIX`;
- pruning is scope-aware and only rejects width contradictions inside `MODELDATA_CONSUMER_PATH`;
- unrelated record-family candidates remain negative controls;
- semantic promotion / Blender emit / runtime dispatch remain false.

Synthetic gate tests only: baseline 43 survivor; hypothetical F02-bound 16-bit proof -> 25 survivor; hypothetical F02-bound 32-bit proof -> 27 survivor. These counts are not evidence of the real width.

## Authority rule

At restart, reconcile this pointer against the newest durable state before acting. Newest validated evidence supersedes stale pointer fields; historical evidence remains history.

Read first:
1. Supabase latest `HANDOFF_CURRENT` (currently row 214)
2. rows 209/210/211/212/213/214 specifically
3. GitHub mainline/static/Companion/F02 branches
4. Drive current checkpoint/handoff
5. Base44 ExperimentLineage
6. Linear lane state

## Current baseline lineage

- mainline branch: `csmc-importer-experimental-20260902`
- consumer implementation commit: `f7e2e69d52fa39e5eaa6074611ec4688d9773a7b`
- original Mainline04 pointer commit: `43efa387e9ddf390bf5366e461155cdf1e2aef55`
- static branch: `csmc-modeler-static-analysis-second-pass-20260914`
- static HEAD: `fa3c3a7af57342eee9178cd78a65c11a83f8c471`
- F02 oracle HEAD: `5db89bc6f0ca20dcb2646b89202ead6b8b53bde2`
- Companion C: C-069 canonical durable row `209`
- Importer Lab consumer-constrained phase: row `210`
- V12 canonical before Mainline 04: row `211`
- original Mainline 04 pointer: row `212` (now superseded)
- duplicate C-069 mirror: row `213` (audit only; canonical is row209)
- current incremental pointer: row `214`

V12 / row210 adds scope-aware hard falsification constraints from the two confirmed architecture edges. Synthetic proposals 50 → 3 explicit contradictions rejected → 4 behavioral duplicates removed → 43 unique survivors, no refill. `CONSUMER_COMPATIBLE != SEMANTIC_CONFIRMED`.

Next frozen discriminator remains `DQ-SER-WIDTH-01` — determine whether the direct primitive on the confirmed consumer corridor consumes the bounded candidate region as 16-bit or 32-bit, with reader VA, direct primitive, effective width, count/loop source and destination required.

Current gates:
- MAINLINE = ACTIVE
- STRUCTURAL DEVELOPMENT = ACTIVE
- pipeline = STRUCTURAL_ONLY
- semantic gate = CLOSED
- semantic promotion = 0
- geometry/index = UNRESOLVED
- `EXPLICIT_SERIALIZER_FIELD_READ` = UNRESOLVED
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH` = UNRESOLVED
- DQ width gate = WAIT_FOR_PROOF
- Blender emit = BLOCKED
- runtime dispatch = false
- physical F02 oracle = 0/30 PENDING_MANUAL_ORACLE

## Highest-value next action

Do not broaden mainline into a static reverse-engineering lane. Receive the next validated static slice from the dedicated MODELER lane and pass it through the fail-closed width gate.

Existing CONFIRMED architecture anchors remain:

- `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP` at `0x140d175d0`
- `EXPLICIT_MODELDATA_LOOKUP` at `0x140d45d30`

Target chain remains:
`EXPLICIT_SERIALIZER_FIELD_READ -> width/endian/count-or-length -> destination -> internal construction -> CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`.

Use C-069 row209 as an independently sealed cross-lane falsification/reference surface; do not silently promote it. Do not count row213 as another C-069 evidence event. Do not restart broad string/name searches. Do not use public `.clip` names to guide the sealed blind pass. Do not perform Save/Ctrl+S in the F02 physical oracle. Do not promote semantics or enable Blender emit before the mainline evidence gate closes.
