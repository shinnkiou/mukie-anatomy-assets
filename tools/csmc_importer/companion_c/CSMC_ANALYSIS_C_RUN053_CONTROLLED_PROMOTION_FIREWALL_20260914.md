# CSMC ANALYSIS COMPANION C — RUN C-053

## QUESTION
Can the new controlled-evidence path remain mechanically fail-closed while C-050 has a Level-4 render-part candidate, C-051 contains seven preregistered predictions, C-052 has only a validator-ready teacher-manifest gate, and mainline has 10 partial I3 pairs but zero valid pairs?

## HYPOTHESIS
A dedicated promotion firewall can prevent candidate/prediction/partial evidence from silently crossing into observation, CONFIRMED semantics, Blender emit, or runtime state while still preserving the next legitimate static action.

## SOURCE
Reference-only durable state:
- mainline controlled-evidence head: `e486b99a69a1a7a89de15af4dcfc6d64c8209c46`
- C-050: `dd58c29c504c54f00e3d2506204b8097d5b5aef9`
- C-051: `915367cf83f7b096591d18ac5cf9010851df96e0`
- C-052: `68a7e0d8311de3ef7f89d6b1a876ae485a26f99b`
- Supabase rows >140 at intake check: none

Current admissible facts are unchanged:
- pipeline = `STRUCTURAL_ONLY`
- render-part-cardinality = Level 4 / HIGH candidate, not confirmed
- I3 partial pairs = 10
- I3 valid pairs = 0
- C-051 predictions = 7; observations admitted = 0
- C-052 teacher manifest = validator ready, not acquired
- semantic promotion = 0
- Blender emit = false
- runtime dispatch = false

## IMPLEMENTATION
Added `csmc_analysis_c_controlled_promotion_firewall_c053.py`.

The firewall rejects:
- raw/private CSMC payload fields, including nested occurrences;
- `prediction_as_observation=true`;
- `candidate_as_confirmed=true`;
- C-051 observation claims before a validated teacher manifest;
- semantic-promotion count/request;
- Blender emit;
- runtime dispatch;
- render-part level above 4 or CONFIRMED confidence on the current evidence object;
- I3 valid-pair count larger than partial count;
- I3 unlock claim with zero valid pairs;
- owner/consumer evidence injected into this object instead of the dedicated C-040/C-045 unlock route.

Accepted current-state input emits only:
- `ACTIVE_FAIL_CLOSED`
- render-part claim ceiling = `LEVEL_4_CANDIDATE_ONLY`
- semantic promotion allowed = false
- Blender emit = false
- runtime dispatch = false
- next action = `WAIT_FOR_C051_TEACHER_MANIFEST`

## SYNTHETIC TEST
15/15 cases are preregistered in the module self-test: one accepted current state plus 14 fail-closed negative cases.

## NEW INFORMATION
The controlled-evidence lane now has an explicit boundary between evidence *admission* and evidence *promotion*. The presence of genuinely new C-050 controlled evidence reopened static analysis, but it did not grant a generic promotion path. C-051 predictions and C-052 validation readiness remain process state, not observations.

## CLOSED HYPOTHESES
- Level-4 render-part evidence may be treated as CONFIRMED because it matches 13/13 fixtures: REJECTED.
- Ten I3 partial pairs may be counted as valid pairs: REJECTED.
- C-051 preregistered predictions may be logged as observations before the teacher-manifest gate: REJECTED.
- A future owner/consumer edge may silently upgrade this controlled-evidence object: REJECTED; it must use the dedicated unlock route.
- New controlled evidence implicitly enables Blender emit/runtime: REJECTED.

## CONFIDENCE / STATE
- promotion-boundary enforcement: VERY HIGH after synthetic verification, pending execution readback
- semantic state: unchanged `STRUCTURAL_ONLY`
- semantic promotion count: 0
- Blender emit: BLOCKED
- runtime dispatch: false

## NEXT
Wait for an actual public-safe C-051 teacher manifest. Validate it with C-052 first. Only after teacher-manifest PASS may an externally produced C-051 aggregate be evaluated through the preregistered C-051 contract. Do not manufacture observations, reacquire private bytes, dispatch MODELER/runtime, mutate RIO-26, or mutate mainline.
