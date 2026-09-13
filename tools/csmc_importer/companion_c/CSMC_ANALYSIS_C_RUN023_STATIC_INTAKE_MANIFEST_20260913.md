# Companion C — Run C-023

## QUESTION
Can future static evidence be accepted into Companion C with a machine-checkable contract that prevents runtime/mainline contact, public leakage of private bytes, automatic semantic promotion, and automatic Blender emission?

## HYPOTHESIS
Artifact intake should be a separate validation step from codec/semantic evidence evaluation.

## PROBE
Added `csmc_analysis_c_static_intake_manifest.py`.

Allowed artifact classes:
- `PUBLIC_SAFE_AGGREGATE`
- `PUBLIC_SAFE_METADATA`
- `PRIVATE_AUTHORIZED_ISOLATED_REF`
- `LATENT_SCHEMA_SNAPSHOT`

Explicitly forbidden acquisition modes:
- `MODELER_ACTION`
- `RUNTIME_JOB`
- `WINDOWS_WORKER`
- `CONTROL_GATE`
- `MAINLINE_CANONICAL_MUTATION`

Accepted inputs must have a source id, provenance hash, storage reference, side-lane isolation flag, no automatic semantic promotion, no automatic Blender emit, and no private bytes committed to the public repository.

## SYNTHETIC TEST
4/4 PASS:
- valid pre-existing isolated private reference accepted
- runtime-job acquisition rejected
- automatic semantic promotion rejected
- private bytes in public repository rejected

## REAL AGGREGATE RESULT
No new private artifact was imported in this run. This run defines the intake boundary only.

## NEW INFORMATION
- Evidence intake, codec binding, semantic binding, and Blender emission can now be four distinct gates.
- A future already-existing isolated private reference can be accepted without relaxing the no-runtime/no-mainline rule.
- Public-safe code/metadata can remain in GitHub while private data stay outside it.

## CLOSED HYPOTHESES
- Accepting an input artifact should implicitly promote its interpretation: REJECTED.
- Companion C needs runtime access in order to accept future evidence: REJECTED.
- Private payload bytes must be copied to GitHub for reproducibility: REJECTED.

## CONFIDENCE CHANGES
- side-lane isolation enforceability: HIGH -> VERY HIGH
- future static-evidence intake path: MEDIUM -> VERY HIGH
- semantic promotion remains controlled solely by the separate evidence contract.

## NEXT QUESTION
Can C-012, C-014, C-018, C-022, and C-023 be composed into one end-to-end static pipeline contract with explicit gate ordering and no implicit transitions?
