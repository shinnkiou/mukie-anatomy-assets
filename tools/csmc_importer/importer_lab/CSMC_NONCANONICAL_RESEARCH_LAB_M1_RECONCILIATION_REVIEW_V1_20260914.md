# CSMC Importer Lab — Noncanonical `research-lab-m1-20260914` reconciliation review v1

Status: `REVIEW_COMPLETE_NO_MERGE_GOVERNANCE_REFERENCE_ONLY`

This review resolves the known duplicate/noncanonical branch risk without merging it into the canonical Importer Lab. It is governance/provenance work only and creates no new CSMC semantic or consumer evidence.

## Compared state

Canonical:
- branch `csmc-importer-experimental-20260902`
- head before review `1d0659ce14e85644fc778e2e1fe3f5011f93279e`
- M1 acceptance v2 `20/20 PASS`
- private GEN0 already completed at Supabase row `191`
- targeted consumer-static packet at row `192`

Noncanonical:
- branch `research-lab-m1-20260914`
- head `bc9f104a4b5f2876d8b6b6becd93b522068fbb38`
- merge base `b32e9b9acfaa199838e3b948e74bb1e4c127fa94`
- compare: `ahead 2 / behind 39`
- its own current-state document still says `M1_PASS__M2_ELIGIBLE_NOT_STARTED` and `16/16` local acceptance.

## Decision

**NO MERGE. NO CODE CHERRY-PICK. NO REGISTRY SNAPSHOT IS IMPORTED AS CURRENT AUTHORITY.**

The noncanonical branch contains useful governance *ideas*, but canonical already implements and tests the important ones:

| Noncanonical asset | Review result |
| --- | --- |
| `FROZEN_SCORING_SPEC` | Concept already represented by canonical frozen scoring policy + M1 v2 acceptance. |
| `HOLDOUT_EXPOSURE_LEDGER` | Ledger concept already implemented dynamically in canonical policy. The static fixture snapshot is stale. |
| `PRIVATE_EVALUATOR_BOUNDARY` | Boundary is already directly tested by canonical M1 v2. |
| `SEMANTIC_PROMOTION_FIREWALL` | Firewall is already directly tested by canonical M1 v2. |
| `REJECTED_FAMILY_REGISTRY` | Stale/incomplete relative to later Phase-7/8/9, simple96 and bounded-stride closures. |
| `IMMUTABLE_HARD_CONSTRAINT_REGISTRY` | Mostly overlaps current canonical hard constraints; reference-only. |

## Why the snapshot must not be copied

The noncanonical branch is not just behind in commits; some of its research-state declarations are now historical. Most importantly:

- it says M2/private progression is not started, but canonical has already completed the bounded private GEN0 generation;
- its static holdout ledger marks `F04` as audit-only validation, while the later canonical private GEN0 frozen scope used `F04 CUBE_SUBDIV` as a TRAIN fixture;
- its rejected-family registry predates multiple later bounded closures.

Copying those JSON registries as current truth would therefore reintroduce stale experimental state and could corrupt future exposure accounting.

## Canonical governance source of truth

Keep the canonical implementation as authority:
- `CSMC_IMPORTER_LAB_M0_M1_SPEC_V01.md`
- `csmc_importer_lab_policy.py`
- `csmc_importer_lab_m1_acceptance_v2.py`
- current append-only result/checkpoint artifacts.

A future dedicated registry export is allowed only if generated from the **current canonical policy and current exposure history**, never copied from this noncanonical branch.

## Evidence state after review

Unchanged:
- new proof-grade consumer edges: `0`
- physical MODELER oracle: `0/30 PENDING_MANUAL_ORACLE`
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`
- broad static hypothesis expansion: `false`
- semantic promotion: `0`
- Blender emit: `BLOCKED`
- runtime dispatch: `false`

No MODELER execution, Save/serialization trigger, Worker/Canary/Control Gate action, Production/STABLE mutation, RIO-26 mutation, or raw private-byte publication was performed.

This review does **not** supersede external current checkpoint v5.
