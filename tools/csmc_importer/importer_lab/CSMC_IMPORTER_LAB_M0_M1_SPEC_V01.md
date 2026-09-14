# CSMC IMPORTER LAB M0/M1 SPEC v0.1

Status: SYNTHETIC INFRASTRUCTURE ONLY. No private GEN0. No semantic promotion.

## Purpose
Provide a fixed Engine whose only research variable is a typed Hypothesis Manifest. The Lab ranks candidates for further falsification; it never decides truth.

## Hard firewalls
- logical batch <= 50
- concurrency only 1 or 2
- `semantic_promotion=false`
- `diagnostic_only=true`
- `blender_emit=false`
- no per-fixture best offsets
- no candidate-specific score formula
- no holdout override
- no private raw CSMC in public GitHub
- parse success is a prerequisite worth 0 points
- holdout is excluded from selection score
- candidate semantic is limited to STRUCTURAL_ONLY / GEOMETRY_OR_TOPOLOGY_TARGET / NULL_DECOY

## M0
- typed manifest
- canonical dedupe key
- one-locus parent->child mutation validator
- rejected-family registry is external input; engine does not reopen a family automatically
- frozen score weights
- holdout exposure state is explicit
- semantic promotion firewall

## M1
- synthetic worker subprocess per candidate
- candidate crash isolation
- candidate timeout
- deterministic canonical ordering
- logical batch <= 50
- concurrency 1 or 2
- negative-control scoring
- behavioral result lineage by manifest hash + canonical key
- private evaluator boundary remains separate

## Frozen score v0.1
- controlled TRAIN relationship: 35
- VALIDATION generalization: 25
- negative-control resistance: 20
- cross-fixture parse stability: 10
- parsimony: 10
- parse success itself: 0

Scores mean only "worth testing next". They are not evidence confidence and cannot promote semantics.

## GEN0 gate
Private CSMC GEN0 is forbidden until this synthetic M1 acceptance suite passes in CI and a separate private-evaluator admission record is created. GEN0 scope remains local sub-block/count/length/numeric codec/reference relationships inside the validated variable-prefix search mask. Material/UV/Weight/Texture/Morph/Bone semantics are not mixed into GEN0.
