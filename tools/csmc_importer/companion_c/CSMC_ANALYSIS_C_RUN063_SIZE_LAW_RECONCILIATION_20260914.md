# CSMC Analysis Companion C — RUN C-063 — Bounded Size-Law Negative-Control Reconciliation — 2026-09-14

## PURPOSE

Consume only the new public-safe mainline size/stride aggregate and C-062 structural mask metadata. Do not reacquire or rescan raw/private CSMC bytes.

## SOURCE DELTA

Mainline `csmc-importer-experimental-20260902` advanced to `09e94e541fa9c061d4d62c077c3f773764c17e18` with a preregistered bounded size-law screen.

Source classification:

`WHOLE_STORED_AND_PHASE_PREFIX_SIZE_NOT_SINGLE_SIMPLE_FIXED_STRIDE_ARRAY`

The candidate family was fixed before evaluation:

- single strides: 4 / 8 / 12 / 16 bytes
- vertex strides: 12 / 16 bytes
- index widths: 2 / 4 bytes
- triangle strides: 4 / 8 / 12 / 16 bytes
- no arbitrary coefficient search
- no post-hoc widening

## OBSERVED NEGATIVE CONTROL

Geometry F01/F02/F03/F04 whole-stored length has no exact single-count fixed-stride model in the bounded family.

Same-phase F02↔F04 remains the strongest bounded geometry relationship surface:

- prefix delta = 864 bytes
- teacher delta vertices = 22
- teacher delta triangles = 46
- teacher delta corners = 138
- pure single-count exact models = 0
- vertex + corner/index exact models = 0
- vertex + triangle exact models = 0

Rig R01-R05 likewise has:

- whole-stored single-count exact models = 0
- bone + weight two-factor exact models = 0

## COMPANION-C INTERPRETATION

Classification:

`BOUNDED_SIMPLE_FIXED_STRIDE_SIZE_LAW_REJECTED`

This closes only the preregistered naive whole-region family. It does not establish absence of vertex/index/bone/weight data, and it does not justify codec, cipher, compression, or owner semantics.

C-062's mask is unchanged: the size-law result rejects hypotheses but does not prove a new invariant region. Remaining public-safe search surface remains 537,774 qwords for the eight-fixture C-062 accounting.

## NEXT SEARCH BOUNDARY

Do not repeat whole-prefix exact-qword reuse search.
Do not fit the entire prefix as one fixed-stride array.
Do not widen stride coefficients post hoc.

The next admissible file-side question is internal segmentation: bounded sub-block boundaries whose individual sizes, repetition counts, or local growth obey preregistered teacher relationships.

## VALIDATION

- Companion C local pytest: 12/12 PASS
- source controlled fixture workflow 34805004049: SUCCESS
- source importer workflow 34805004059: SUCCESS

## ISOLATION

- pipeline: `STRUCTURAL_ONLY`
- semantic promotion count: 0
- Blender emit: BLOCKED
- runtime dispatch: false
- MODELER actions: 0
- Worker actions: 0
- Canary actions: 0
- Control Gate actions: 0
- RIO-26 mutations: 0
- mainline mutations: 0
- automatic integration: false
- raw/private CSMC publication: false
