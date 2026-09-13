# Companion C — Run C-033

## QUESTION
Can the finished Companion C package be handed to a mainline consumer as a reference-only artifact while mechanically preventing automatic merge, semantic promotion, Blender emission enablement, runtime dispatch, and mainline mutation?

## HYPOTHESIS
A handoff should validate the current evidence state and allowed effects independently from the research package contents.

## PROBE
Added `csmc_analysis_c_handoff_contract.py`.

The validator requires:
- `pipeline_stage = STRUCTURAL_ONLY`
- semantic promotion count = 0
- Blender mesh/scene emission remain blocked
- runtime/MODELER/Worker/RIO-26/mainline mutation counts remain 0
- no public private-payload bytes
- no automatic merge
- all four future unlock input classes I1-I4 remain explicit

## SYNTHETIC TEST
5/5 PASS:
- valid reference-only handoff accepted
- nonzero semantic promotion rejected
- mesh emission enabled rejected
- automatic merge policy rejected
- runtime job present rejected

## REAL AGGREGATE RESULT
The current `CSMC_ANALYSIS_C_FINAL_PACKAGE_20260913.json` is compatible with `HANDOFF_REFERENCE_SAFE`.

Allowed handoff effects are limited to:
- read
- review
- reference public-safe findings

Forbidden effects remain:
- automatic merge
- semantic promotion
- Blender emission enablement
- runtime dispatch
- MODELER/Worker action
- RIO-26 mutation
- private payload publication

## NEW INFORMATION
- The side-lane package can be consumed by another lane without changing its evidence truth state.
- Handoff safety is now machine-checkable rather than being only prose policy.
- The user can later authorize integration explicitly without weakening the current no-auto-merge rule.

## CLOSED HYPOTHESES
- A useful handoff requires merging the side branch: REJECTED.
- Reading the package should promote current semantic slots: REJECTED.
- Integration readiness requires Blender emission to be enabled first: REJECTED.

## CONFIDENCE CHANGES
- reference-only handoff safety: HIGH -> VERY HIGH
- accidental mainline mutation risk from package consumption: materially reduced
- current semantic readiness: unchanged / unresolved

## NEXT QUESTION
What exact consumer actions are safe, review-gated, or forbidden if a mainline maintainer chooses to inspect or selectively reuse the package?
