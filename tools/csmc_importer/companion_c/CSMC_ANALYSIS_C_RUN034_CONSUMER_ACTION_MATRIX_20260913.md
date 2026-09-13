# Companion C — Run C-034

## QUESTION
What exact actions are safe, review-gated, or forbidden for a mainline consumer inspecting the Companion C package?

## PROBE
Added `CSMC_ANALYSIS_C_CONSUMER_ACTION_MATRIX_20260913.json` with three action states:
- `SAFE_REFERENCE_ONLY`
- `REVIEW_REQUIRED`
- `FORBIDDEN_WITHOUT_NEW_EVIDENCE_OR_EXPLICIT_USER_AUTHORIZATION`

## REAL AGGREGATE RESULT
### SAFE_REFERENCE_ONLY
- read side-branch findings
- inspect public-safe parser/evidence code
- reference the package from documentation
- run side-lane validators on future isolated static inputs

### REVIEW_REQUIRED
- selectively copy/cherry-pick an individual public-safe utility
- create a mainline PR from selected side-lane changes

These require explicit user/human authorization, target-diff review, preservation of semantic gates, and no private bytes. PR creation must remain review-only with no auto-merge.

### FORBIDDEN IN CURRENT STATE
- merge the side branch
- mark any semantic slot confirmed without slot-specific evidence
- enable Blender mesh/scene emission before C-024 readiness conditions are satisfied
- dispatch runtime/MODELER/Worker/Control Gate work
- publish private payload bytes to the public repository

## NEW INFORMATION
- Integration can proceed incrementally at the reference/review layer without changing evidence truth.
- Code reuse and semantic promotion are explicitly separated: reusable utility code may be reviewable even while all current semantic slots remain unresolved.
- A future PR can be prepared only after explicit authorization and still remain non-merging by default.

## CLOSED HYPOTHESES
- Any side-branch reuse is equivalent to merging the whole research branch: REJECTED.
- Utility-code review requires semantic confirmation first: REJECTED.
- Documentation/reference use can alter parser readiness: REJECTED.

## CONFIDENCE CHANGES
- consumer action safety classification: VERY HIGH
- selective integration feasibility without evidence promotion: HIGH -> VERY HIGH
- current recommendation: `SAFE_REFERENCE_ONLY`

## NEXT QUESTION
Can the final package index be extended from C-032 to C-034 while preserving the original exhaustion result and clearly separating “research exhausted” from “handoff prepared”?
