# CSMC Analysis Companion C — Integration Review

This directory is a deliberately small, public-safe review surface extracted from the isolated `csmc-analysis-companion-c-20260913` side lane.

## Purpose

Provide reusable guardrails without importing the side lane's full historical research tree or enabling runtime behavior.

Included:
- `csmc_analysis_c_handoff_contract.py` — rejects handoff states that imply automatic merge, semantic promotion, Blender emit, runtime/MODELER/Worker actions, RIO-26 mutation, or private payload publication.
- `csmc_analysis_c_pipeline_contract.py` — separates intake, structural state, codec binding, semantic confirmation, mesh readiness, and scene readiness.
- `csmc_analysis_c_parser_skeleton.py` — structural parser state builder that keeps codec catalog entries separate from semantic bindings and blocks Blender geometry output until geometry and index are independently confirmed with evidence IDs.
- `test_companion_c_review_contracts.py` — regression tests for the non-mutation and semantic-gate invariants.

## Explicit non-goals

This review package does **not**:
- decode private CSMC payload bytes;
- identify Mesh/Index/Transform/Material/Hierarchy semantics;
- dispatch runtime work;
- control MODELER, Windows Worker, Base44 Control Gate, or Blender;
- mutate RIO-26;
- enable Blender output;
- merge itself.

## Current evidence state

- Research state: `EXHAUSTED_FOR_NON_DUPLICATIVE_STATIC_ANALYSIS`
- Handoff state: `REFERENCE_ONLY_PREPARED`
- Pipeline stage: `STRUCTURAL_ONLY`
- Semantic promotions: `0`
- Blender mesh emit: blocked
- Blender scene emit: blocked

Static research should resume only after one of the declared unlock inputs exists:
1. `I1_ISOLATED_PLUS965_STATIC_REF`
2. `I2_PUBLIC_SAFE_POSITIONAL_AGGREGATE`
3. `I3_INTERPRETABLE_CONTROLLED_PAIR_OR_LABELED_DIFFERENTIAL`
4. `I4_CURRENT_MODEL_NODE_MAPPING_ARTIFACT`

## Verification

The integration-review contract suite was executed independently before opening the draft PR:

```text
Ran 4 tests
OK
```

This branch is intended for review only. Do not enable auto-merge.
