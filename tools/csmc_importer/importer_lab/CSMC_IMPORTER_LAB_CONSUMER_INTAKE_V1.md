# CSMC IMPORTER LAB CONSUMER INTAKE V1 — 2026-09-14

## Classification

`MAJOR STRUCTURAL / CONSUMER-SIDE PROGRESS — NO SEMANTIC PROMOTION`

Canonical external input:

- V11
- Supabase row 208
- MODELER 1.10.13 binary SHA-256 `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`
- Full Snapshot SHA-256 `afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342`

New proof-grade consumer evidence admitted:

- `C01 EXTERNALCHUNK_OFFSET_LOOKUP_CONFIRMED`
- `C02 MODELDATA_CANVAS3D_LOADER_BINDING_CONFIRMED`

These are **scope-aware falsification constraints**. They define a confirmed consumer corridor.
They do not bind geometry/index/UV/material/bone/weight semantics.

## Constraint behavior

C01 applies only when a candidate explicitly traverses the `ExternalChunk` corridor.
C02 applies only when a candidate is explicitly scoped to `MODELDATA_CONSUMER_PATH`.

Outcomes:

- `CONSUMER_CONTRADICTED` → hard reject
- `CONSUMER_COMPATIBLE` → survives, **no winner bonus**
- `CONSUMER_UNRESOLVED` → survives as unresolved unless another hard rule rejects it

`CONSUMER_COMPATIBLE != SEMANTIC_CONFIRMED`.

Visual similarity / Virtual Importer appearance contributes **0** score and cannot affect
constraint classification.

## Search method

Continue with:

`Constraint-Guided Beam Search + Falsification`

Classic GA remains forbidden.

Preferred next-generation budget:

| family | max proposals |
|---|---:|
| READER_WIDTH_ENDIAN | 15 |
| COUNT_LENGTH_RELATION | 10 |
| LOCAL_BLOCK_LAYOUT | 10 |
| DESTINATION_CONTAINER_RELATION | 10 |
| NEGATIVE_DECOY | 5 |

The total is a ceiling, not a quota. After hard prune and behavioral dedupe, do **not** refill
to 50.

The current public-safe synthetic contract test deliberately generates 50 proposals, then
applies scope-aware consumer contradiction pruning plus semantic-insensitive behavioral
dedupe:

- input = 50
- hard reject = 3
- duplicate = 4
- surviving unique candidates = 43

This is infrastructure validation only; it is not evidence that any surviving reader hypothesis
matches private CSMC bytes.

## Search-space corridor

Do not return to unconstrained whole-payload or broad variable-prefix exploration.

Use:

`Structural IR -> bounded candidate region -> consumer-compatible candidate -> reader hypothesis -> destination hypothesis -> controlled test`

The Full Snapshot is not re-searched wholesale by Importer Lab. It is used only to formulate
minimal discriminating questions around the confirmed `ExternalChunk` and
`ModelData -> Canvas3DModelLoader` corridor.

## Next static target

Priority 1 remains:

`EXPLICIT_SERIALIZER_FIELD_READ`

Priority 2:

`EXPLICIT_INTERNAL_MODEL_CONSTRUCTION`

The Lab does not decide competing hypotheses from score alone. It emits a
`DISCRIMINATING_QUESTION_PACKET` with the minimum static evidence needed to falsify one side.

Highest-priority current question:

> On the confirmed consumer corridor, is the direct primitive consuming the bounded candidate
> region a 16-bit or 32-bit read?

Required static evidence:

- reader VA
- direct read primitive
- effective width
- loop/count bound source
- destination write/container

## Frozen F02 questions

The existing five questions remain **0/5 resolved**:

- Q-BND-01
- Q-BND-02
- Q-INV-01
- Q-PFX-01
- Q-TERM-01

New discriminating questions may be related to these questions, but may not mark them resolved
without observation.

F02 physical oracle remains `0/30 PENDING_MANUAL_ORACLE`.

Frozen Sentinel-9 order remains:

`M01 -> M10 -> M13 -> M14 -> M15 -> M18 -> M22 -> M23 -> M30`

Importer Lab may update an information-gain map only as `PROPOSAL_ONLY`; it may not overwrite
the canonical oracle order.

## M1 / M2 gate interpretation

The canonical M1 v2 matrix contains 20 gates and sets `private_gen0_eligible=true` only when
all 20 pass. Consumer-constrained CI re-runs that M1 acceptance alongside the new tests.

A synthetic smoke pass is not treated as M1 completion by itself.

If the current 20-item M1 matrix remains PASS, private structural next-generation work is
eligible without waiting for the physical oracle.

## Mainline handoff

Do not return a raw leaderboard.

Return only:

- non-dominated hypotheses
- nearest competing hypotheses
- constraint results
- negative controls
- discriminating questions
- unexplained residuals
- consumer compatibility class

No semantic promotion request is emitted by the Lab.

## Guards

- semantic_promotion = false
- Blender emit = blocked
- runtime dispatch = false
- visual output = `HYPOTHESIS_VISUALIZATION / DIAGNOSTIC_ONLY / NOT_SEMANTIC_PROOF / NOT_IMPORT_RESULT`
- physical oracle = unchanged
- no broad blind Phase-10 expansion
