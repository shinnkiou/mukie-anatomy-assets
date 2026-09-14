# CSMC Scout Reference Integration — Mainline State Correction
Date: 2026-09-14

## Authority order

This document records a subordinate Scout reference only.

`mainline canonical state > validated new evidence > Scout handoff/reference`

The Scout handoff does not change the mainline mission. Mainline remains responsible for validated evidence intake, Structural IR integration, parser/importer implementation, semantic gate management, and the shortest safe path to a minimal CSMC→Blender importer.

## Accepted state correction

The following former Scout gaps are historical CLOSED / CONFIRMED consumer-side evidence and are no longer search targets:

- `EXPLICIT_PARENT_RECORD_BOUNDARY`
- `EXPLICIT_PARENT_LENGTH_FIELD`
- `EXPLICIT_CONSUMER_CROSSREF`

Mainline must not re-run their old search surface.

Current consumer-side candidates are reference-only, not a mandatory seven-step mainline queue:

1. `EXPLICIT_CSMC_HANDLER_ENTRY`
2. `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP`
3. `EXPLICIT_MODELDATA_LOOKUP`
4. `EXPLICIT_CANVAS3D_LOAD_ENTRY`
5. `EXPLICIT_SERIALIZER_FIELD_READ`
6. `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION`
7. `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`

Only separately validated CONFIRMED/STRONG evidence from the consumer/static lane should be admitted through the mainline evidence gate.

## Scout numeric toolbox policy

Reference implementation:
`research/csmc_data_scout/csmc_numeric_candidate_probe.py`
Scout head:
`212a44851c8161a54209af081b003deedc70e178`

The probe is candidate-only and permanently `semantic_promotion=false`.

For the current mainline checkpoint it is **not invoked yet**. Reason: the known bounded variable prefixes show phase-dependent high-entropy rewriting and the strongest rig pair R04→R05 changes both assignment cardinality and weight values. A raw numeric plausibility pass would not currently separate the competing hypotheses and therefore would not directly advance the semantic gate.

It becomes admissible when a bounded region or a cleaner one-variable differential exists such that dtype/endian/stride plausibility can actually discriminate hypotheses.

## Fixture policy

General 3D fixture collection remains stopped. Additional fixtures are requested only when a single-variable control is proven to have positive information value for the current competing hypotheses.

## Runtime policy

This integration performs:
- MODELER actions: 0
- runtime jobs: 0
- Worker actions: 0
- Canary/STABLE/Production mutations: 0
- automatic semantic promotions: 0
- Blender emits: 0

Scout handoff package SHA-256: `22c392e37f6b05666ee74e53f955e3e659c22057361ae2e743e8968c41515233`.
