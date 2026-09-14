# CSMC Importer Hypothesis Lab — M0/M1

Status: **synthetic infrastructure only**. No private CSMC GEN0 has run.

## Mission

This lane does not decode CSMC by majority vote and does not treat a high score as truth. It creates bounded, typed structural hypotheses, applies hard constraints, deduplicates equivalent candidates, runs synthetic evaluation in isolated worker processes, and records only **next-test priority**.

The mainline remains `STRUCTURAL_ONLY`. Semantic promotion and Blender emit remain blocked.

## M0

M0 freezes the research grammar and the safety boundary:

- typed Hypothesis Manifest
- bounded region + structural anchor; no free absolute offset
- hard-constraint registry
- rejected-family registry
- V01 holdout contamination ledger (`LOCKED_AUDIT_SET`, not pristine)
- frozen scoring policy
- semantic-promotion firewall
- private evaluator boundary

Factory permissions are `execute / measure / record` only. Factory cannot decide semantic truth, change score weights, release holdout data, widen search bounds, mark Blender-ready, or adopt a hypothesis into mainline.

## M1

M1 is deliberately synthetic:

- logical batch <= 50
- concurrency limited to 1 or 2
- genotype dedupe
- behavioral phenotype hashing
- subprocess timeout isolation
- subprocess crash isolation
- deterministic replay fingerprint
- negative-control support
- artifact lineage fields

The synthetic worker never reads CSMC files.

## GEN0 design — not executed

GEN0 does **not** declare `geometry` or `index`. It searches grammar inside already-bounded variable-prefix regions.

| Candidate family | Planned upper allocation |
|---|---:|
| Local boundary / length | 14 |
| Count scalar codec | 10 |
| Local record layout | 10 |
| Cross-block relationship | 6 |
| Reference-domain relationship | 5 |
| Negative / adversarial control | 5 |

50 is an upper logical population, not a quota. Hard-prune and dedupe may reduce it; candidates are never fabricated just to reach 50.

Material, UV, weight, texture, morph, and bone semantics are out of scope for GEN0.

## Rejected families stay rejected

The generator must not reintroduce:

- whole-payload simple fixed-stride
- whole-phase-prefix simple fixed-stride
- plaintext-name carving
- exact-qword brute-force repetition
- old owner-edge rescans

A rejected family can only re-enter after a separately versioned external evidence change, never because the search score is low.

## Scoring

Parse success is a gate and receives **0 points**. Visual similarity and generic numeric plausibility also receive **0 direct points**.

After hard gates:

- controlled differential: 30
- withheld validation: 25
- negative controls: 20
- structural consistency: 10
- consumer evidence: 10
- simplicity: 5

Score means **NEXT_TEST_PRIORITY_ONLY**.

## Private evaluator boundary

Future private GEN0, if authorized after M1 acceptance, must use:

`public-safe manifest -> private evaluator -> aggregate public-safe observation`

Raw/private CSMC bytes never enter Factory or public GitHub.

## Diagnostic visualization

If a future hypothesis is visualized, it must be labeled:

- `DIAGNOSTIC_ONLY`
- `NOT_SEMANTIC_PROOF`
- `NOT_IMPORT_RESULT`

Visual resemblance contributes zero score.

## Acceptance gate

M1 acceptance requires synthetic tests proving fail-closed semantic fields, batch cap, dedupe, scoring isolation, holdout ledger, timeout/crash isolation, and deterministic replay. Passing M1 only permits consideration of a separately authorized private GEN0; it does **not** permit semantic promotion, Blender emit, MODELER runtime, Worker, Canary, Control Gate, or mainline mutation.
