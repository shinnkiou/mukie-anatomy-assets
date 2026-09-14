# CSMC Importer Lab GEN0 — Phase-9 Local Length-Chain Rejection

## QUESTION
Does the previously uninspected phase-2 F01/R05 pair contain a recurrent two-stage local length chain near the validated invariant-core boundary?

## FROZEN PROTOCOL
Fixed before inspecting raw F01/R05 payloads:
- TRAIN: `CSMC_F01_TRIANGLE`
- VALIDATION: `CSMC_R05_CUBE_B2_MIX50`
- final 1024 bytes of each validated variable prefix
- two adjacent self-describing stages using the same u16/u32 LE/BE header type
- natural alignment required for both headers
- scale: 1 / 2 / 4 / 8 bytes per length unit
- end anchor: invariant-core boundary minus 0 / 8 / 16 / 32 / 64 / 128 / 256 bytes
- each header value must be 1..4096
- exact two-stage chain only; no padding or tolerance

## RESULT
- F01 TRAIN chain hits: **0**
- R05 VALIDATION chain hits: **0**
- recurrent common format: **0**
- classification: `GEN0_PHASE9_LOCAL_LENGTH_CHAIN_FAMILY_REJECTED_PHASE2`

## FRONTIER DECISION
Phase-7, Phase-8, and Phase-9 are three consecutive bounded GEN0 generations without validation-frontier improvement. Per the frozen stop policy, the static GEN0 branch is now **PAUSED**, not widened.

This is not a claim that the remaining payload has no structure. It means further blind bounded enumeration has fallen below the value of obtaining a new independent evidence axis.

## NEXT ACTION
Resume only when one of the following arrives:
1. read-only F02 30-variant MODELER mutation-oracle observations;
2. proof-grade direct serializer field-read/data-flow evidence;
3. another independently justified evidence source that creates a genuinely new constraint.

Do not post-hoc widen Phase-7 raw-index windows, Phase-8 count-to-anchor grammar, or Phase-9 length-chain grammar.

## SAFETY / GATE
`STRUCTURAL_ONLY`
`semantic_promotion=0`
`blender_emit=BLOCKED`
`static_gen0_frontier=PAUSED`

No raw CSMC bytes, literal payload values, private file paths, or decoded proprietary content are included here.
