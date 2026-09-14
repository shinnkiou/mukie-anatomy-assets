# CSMC Analysis Companion C — Scout toolbox/state update — 2026-09-14

Status: `STATE_UPDATE_NOT_A_C_RUN`

## Purpose

This note registers CSMC DATA SCOUT output as a subordinate toolbox/reference for Companion C. It does **not** change Companion C's research purpose and does not create C-064.

Priority remains:

1. Companion C canonical research state.
2. Genuinely new validated evidence.
3. Scout reference/toolbox.

Source package SHA-256: `22c392e37f6b05666ee74e53f955e3e659c22057361ae2e743e8968c41515233`
Scout branch/head: `csmc-data-scout-20260914` / `212a44851c8161a54209af081b003deedc70e178`.

## State correction accepted

The following old owner-edge gaps are historical CLOSED items after the MODELER 1.10.13 static-analysis first pass and must not be re-searched on the C-045 surface:

- `EXPLICIT_PARENT_RECORD_BOUNDARY`
- `EXPLICIT_PARENT_LENGTH_FIELD`
- `EXPLICIT_CONSUMER_CROSSREF`

This is a state correction only, not a new research result.

## Consumer-side reference gaps

The following are reference opportunities only, not a fixed Companion C task list:

- `EXPLICIT_CSMC_HANDLER_ENTRY`
- `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP`
- `EXPLICIT_MODELDATA_LOOKUP`
- `EXPLICIT_CANVAS3D_LOAD_ENTRY`
- `EXPLICIT_SERIALIZER_FIELD_READ`
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`

Companion C uses one only when it directly intersects the current controlled differential, competing hypothesis, or negative control.

## Scout numeric probe registered as toolbox

Reusable candidate detector:

`research/csmc_data_scout/csmc_numeric_candidate_probe.py`

Hard guardrails:

- candidate narrowing only;
- `semantic_promotion=false`;
- no semantic confirmation from numeric plausibility alone;
- no proprietary offsets/private byte signatures embedded in public code;
- a semantic claim still requires controlled relationship + negative control + relevant consumer-side evidence + independent validation when needed.

Using the probe is not itself NEW INFORMATION and cannot by itself justify a new C-run.

## Current Companion C evaluation

C-063 remains the latest numbered run. Its next structural question remains internal sub-block boundary/length/repetition relationships inside the masked variable surface, or a genuinely new same-identity controlled relationship.

The current controlled-fixture evidence does **not** yet support a proof-grade `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`. Existing consumer-route/state evidence does not bind a specific C-050/C-056/C-063 candidate sub-block to an explicit consumer field read and downstream construction site.

The next single consumer-side prerequisite, if a new external MODELER static-analysis artifact arrives, is therefore:

`EXPLICIT_SERIALIZER_FIELD_READ`

It must identify a concrete read/parse operation over a controlled candidate region strongly enough to cross-check against fixture behavior. `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION` may then strengthen the semantic relation, but is not inferred in advance.

No C-064 is opened for this diagnosis because no new proof-grade consumer artifact or fixture observation is present.

## Concurrent mainline evidence noted but not consumed as a Companion run

Mainline has prepared `CSMC_F02_SINGLE_BYTE_XOR01_30_20260914`, a 30-variant controlled mutation batch. Modeler oracle observations remain pending. Generation/readback alone does not establish sensitivity, ownership, consumer semantics, or a controlled fixture-to-consumer match. Companion C will evaluate only future public-safe observed outcomes if they arrive externally.

## Isolation

- pipeline: `STRUCTURAL_ONLY`
- semantic promotion: `0`
- Blender emit: `BLOCKED`
- runtime dispatch: `false`
- MODELER actions: `0`
- Worker / Canary / Control Gate / Production / STABLE actions: `0`
- RIO-26 mutations: `0`
- mainline mutations: `0`
- automatic integration: `false`
- raw/private CSMC publication: `false`

## Resume condition

Open a new numbered C-run only when one of the following actually appears and changes the evidence state:

- genuinely new fixture evidence;
- new consumer-side static evidence;
- a new independent relationship;
- a new negative control;
- a result that actually rejects an existing competing hypothesis.

Do not create a run merely to exercise Scout tooling.
