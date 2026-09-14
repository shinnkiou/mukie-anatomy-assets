# CSMC Importer Lab GEN0 — Phase-8 Local Count-to-Anchor Extent Rejection

## QUESTION
Does the unseen phase-5 F05/R02 pair contain a recurrent exact local counted sub-block whose count field determines the remaining byte extent to a fixed structural anchor near the validated invariant-core boundary?

## FROZEN PROTOCOL
The protocol was fixed before inspecting the raw F05/R02 payloads:
- TRAIN: `CSMC_F05_CUBE_UV`
- VALIDATION: `CSMC_R02_CUBE_B1_W100`
- final 1024 bytes of each validated variable prefix only
- count field: u16/u32, little- or big-endian
- count field must be naturally aligned to payload start
- unit extent: 1 / 2 / 4 / 8 / 12 / 16 / 24 / 32 bytes
- candidate end anchor: invariant-core boundary minus 0 / 8 / 16 / 32 / 64 / 128 / 256 bytes
- exact relation only: `count * unit_extent == bytes_after_count_to_end_anchor`
- no alignment padding, tolerance, score bonus, visual fit, or semantic label

## RESULT
- F05 TRAIN candidate hits: **1**
- R02 VALIDATION candidate hits: **0**
- recurrent common format: **0**
- classification: `GEN0_PHASE8_LOCAL_COUNT_TO_ANCHOR_EXTENT_FAMILY_REJECTED_PHASE5`

The isolated F05 hit is retained only as a failed TRAIN-only candidate. It is not promoted or interpreted.

## SCOPE
This rejects only the exact frozen phase-5 family above. It does **not** reject:
- nested or chained counted records
- counts separated from their arrays by variable headers
- transformed/encoded counts
- padding-bearing grammars
- other structural phases
- consumer-decoded fields

## NEXT ACTION
Do not widen this family post hoc. Highest-value evidence remains:
1. the read-only 30-variant F02 MODELER mutation oracle when physical access is available;
2. a proof-grade direct serializer field read;
3. otherwise a structurally distinct nested/local-record grammar family with a fresh validation split.

## SAFETY / GATE
`STRUCTURAL_ONLY`
`semantic_promotion=0`
`blender_emit=BLOCKED`

No raw CSMC bytes, literal payload values, private file paths, or decoded proprietary content are included here.
