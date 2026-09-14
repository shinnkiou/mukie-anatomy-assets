# CSMC IMPORTER HYPOTHESIS LAB — CURRENT STATE

Date: 2026-09-14 JST
Project: `csmc_importer_lab`
Status: `M1_PASS__M2_ELIGIBLE_NOT_STARTED`

## CURRENT STATE

M0 specification and isolation contracts are frozen. M1 synthetic/public-safe Factory MVP is implemented and the 16-item acceptance suite passed 16/16 locally.

Spec SHA-256: `63e285de67df9c2a9feaad1345d24c9ac12db9c8cd35fe74350b47cd02346964`
Acceptance report content SHA-256: `93e22ae333c4e0cf8e7608476d1e1a2fd1e0cc26792fcb401dcd09715a804afa`
Acceptance semantic report SHA-256: `6ab31b9428ddd39153e23295bd89e1b28ce9c521e421c7049188bd655e41130d`

No private CSMC bytes were used or copied into this public-safe implementation.

## COMPLETED

- all attached DESIGN REVIEW positions reconciled into v0.1
- isolated project/queue/capability/artifact naming defined
- Hypothesis Manifest v0.1 schema
- six immutable versioned registries
- canonical genotype/phenotype dedupe
- frozen Factory execution envelope
- synthetic evaluator and public-safe result fingerprinting
- negative-control rejection
- concurrency 1 and 2 paths
- timeout/crash isolation
- artifact SHA readback and corruption rejection
- frozen-context drift STOP
- three-run deterministic replay
- production queue/artifact non-interference counters
- all sixteen M1 acceptance gates PASS

## FAILED

None in M1 acceptance.

## OPEN RISKS

- This public M1 does not prove any CSMC semantic interpretation.
- Private controlled CSMC is not present in this synthetic execution context.
- M2 private evaluator transport/storage boundary still requires a private execution surface before any GEN0 real-corpus run.
- Provider-side durability mirrors must retain Lab isolation and must never copy raw payload bytes into public metadata stores.

## NEXT ACTION

Persist and read back this M0/M1 state independently in GitHub, Google Drive, Base44, Supabase, and Linear. After all mirrors verify, M2 remains eligible but must stay NOT STARTED until the explicitly authorized private controlled corpus is present in a private evaluator context.

## REGISTRY FILE SHA-256

- `FROZEN_SCORING_SPEC`: `c969d9ddf142fa6f94a3fa9e461cee4e74acf7ada06ef50f20c1cffaa0e65402`
- `HOLDOUT_EXPOSURE_LEDGER`: `623ef0ab5feb039a7d8c8568148c8b5af6a91fe9751348f8fff3bd13afaf763c`
- `IMMUTABLE_HARD_CONSTRAINT_REGISTRY`: `d6056a3ea66ddbdcd5f4a95bb0cbbc42a425ca6145d68b5cf44bfd7b0c6f394f`
- `PRIVATE_EVALUATOR_BOUNDARY`: `4263c5b02d97633eaa0ac6a7afe91dc4017df1cc10db2a215968c6820542c3a8`
- `REJECTED_FAMILY_REGISTRY`: `ac13d93154845ef865d00a0c4fda51c18ac6e0f2f0e0e68bc113e4c3b5a68c0e`
- `SEMANTIC_PROMOTION_FIREWALL`: `9a3de9b3c27668ab71c99252040acb65e0ab2085fcb244be529468bba8c2716a`

## PROOF FIREWALL

`semantic_promotion=false`; `blender_emit=false`; `m2_started=false`.
