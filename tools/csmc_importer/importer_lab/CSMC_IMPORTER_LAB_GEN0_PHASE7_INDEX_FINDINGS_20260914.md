# CSMC Importer Lab GEN0 — Phase-7 Index/Reference-Domain Rejection

## QUESTION
Can a simple raw index/reference-domain stream be found immediately before the validated invariant-core boundary in the clean same-phase F02/F04/R01 triplet?

## INPUT
- F02 QUAD (TRAIN)
- F04 CUBE_SUBDIV (TRAIN)
- R01 CUBE_B1_W0 (VALIDATION)
- validated variable-prefix / invariant-core boundaries only
- private controlled CSMC bytes evaluated outside public GitHub

## METHOD
A preregistered direct-count seed screen first checked u16/u32 BE/LE values for exact `vertices`, `triangles`, or `corners` counts in the F02 validated variable prefix at width-aligned boundary-relative offsets. It generated **0** seed offsets, so no direct-count candidate entered GEN0.

GEN0 then evaluated **48** `LOCAL_INDEX_RANGE_BLOCK` hypotheses:
- boundary-relative windows: 128 / 256 / 512 / 1024 bytes
- u16 / u32
- big-endian / little-endian
- every byte shift 0..itemsize-1
- reference-domain criterion: >=90% of values in `[0, vertex_count)` and >=2 distinct in-domain values
- both TRAIN fixtures and R01 VALIDATION had to pass

## RESULT
- evaluated: 48
- hard pass: 0
- hard fail: 48
- classification: `GEN0_PHASE7_BOUNDARY_RELATIVE_RAW_INDEX_RANGE_FAMILY_REJECTED`

This is a **bounded family rejection only**. It does not reject encoded, delta-coded, indirect, compressed, transformed, differently bounded, or consumer-decoded index structures.

## CONFIDENCE
Structural negative result: HIGH for the exact preregistered family.
Semantic binding: UNRESOLVED.

## COUNTEREXAMPLE
No candidate passed TRAIN + VALIDATION.

## CLOSED HYPOTHESIS
Raw contiguous u16/u32 BE/LE reference-domain arrays occupying the tested boundary-relative windows are rejected for the phase-7 F02/F04/R01 triplet.

## OPEN HYPOTHESES
- local counted sub-blocks not occupying the entire tested window
- encoded/transformed reference domains
- local record structures with internal header/count relationships
- consumer-decoded numeric fields
- vertex/position-like stream
- other non-index structural relationships

## WHAT THIS UNLOCKS
Do not widen the same raw-index family post hoc. Highest value remains:
1. mutation oracle sensitivity when MODELER access exists;
2. direct serializer field read when the private static slice exists;
3. otherwise a distinct bounded local-counted-sub-block reseed.

## SAFETY / GATE
`STRUCTURAL_ONLY`
`semantic_promotion=0`
`blender_emit=BLOCKED`

No raw CSMC bytes or decoded proprietary content are included in this public report.
