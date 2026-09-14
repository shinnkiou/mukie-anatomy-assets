# CSMC Importer Hypothesis Lab v0.1 — Public Contract

Status: `FROZEN_M0_SPEC_PUBLIC`
Date: 2026-09-14 JST

This branch defines an isolated, deterministic hypothesis-testing lab for structural interoperability research. It does not change mainline, Companion C, Data Scout, production queues, production workers, runtime gates, or semantic promotion policy.

## Frozen design

- project key: `csmc_importer_lab`
- queue: `csmc_importer_lab_jobs_v0_1`
- worker capability: `csmc_hypothesis_runner_v1`
- one generation: at most 50 logical candidates
- concurrency progression: 1 canary -> 2 MVP -> 5 after soak
- search core: typed bounded grammar -> hard prune -> canonical dedupe -> negative controls -> validation -> Pareto/lexicographic ranking
- default mutation: one independent axis; at most two only when pre-registered as coupled
- semantic labels are display-only
- parse success is eligibility, never fitness
- visual similarity is not evidence
- V01 is a reused external benchmark, not a pristine holdout

## GEN0 allocation

- Local Structural Boundary: 20
- Counted Numeric Codec: 10
- Geometry/Index Relationship: 5
- Falsification Controls: 5
- Exploration: 10

## Frozen fixture roles

- TRAIN: F01-F03
- VALIDATION: F04
- ADVERSARIAL: R01-R05
- SEALED SIDE-DOMAIN: F05-F07
- EXTERNAL AUDIT: V01

## Ranking and stop policy

Hard contradictions are rejected before ranking. Survivors carry a metric vector for controlled differential consistency, cross-fixture structural consistency, negative-control specificity, validation generalization, consumer compatibility, and parsimony.

A branch closes after three consecutive generations without validation-frontier improvement. A family is paused after roughly five generations without new independent evidence.

## M1 acceptance

M1 requires all of the following: 50-candidate logical batch, concurrency 1 and 2, canonical dedupe, manifest guardrails, isolated timeout and crash handling, negative-control rejection, artifact integrity verification, frozen-context drift rejection, three-run deterministic replay, public-safe results, zero semantic promotion, zero render/export emission, and zero production queue/artifact mutation.

## Proof firewall

A Lab ranking is never semantic truth. Adoption into mainline requires independent evidence under existing mainline proof gates. M2 may start only after M1 is 16/16 PASS and an explicitly authorized private evaluation context exists.

## Durable mirrors

The same public-safe checkpoint is mirrored to GitHub, Google Drive, Base44, Supabase, and Linear. Every mirror records CURRENT STATE, COMPLETED, FAILED, OPEN RISKS, and NEXT ACTION.
