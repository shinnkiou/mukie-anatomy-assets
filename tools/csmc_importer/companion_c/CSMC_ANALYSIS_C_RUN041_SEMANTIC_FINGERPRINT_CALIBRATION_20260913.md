# Companion C — Run C-041 — CC0 semantic fingerprint calibration

## QUESTION
Can known public ground-truth fixtures strengthen heuristic/negative-control evaluation without treating fixture similarity as CSMC semantic proof?

## INPUTS
Drive `SEMANTIC_FINGERPRINTS_20260913.md` and the CSMC research resource index.
The current calibrated fixtures are:
- Khronos SimpleSkin / CC0
- Khronos SimpleMorph / CC0
- Khronos SimpleTexture / CC0

The resource index retains exact hashes for the acquired fixture files. No private CSMC bytes are used.

## IMPLEMENTATION
Added `csmc_analysis_c_semantic_fingerprint_calibration.py`.

Rules cover:
- vertex
- index
- UV
- normal
- tangent
- joints
- weights
- matrix
- quaternion
- morph
- material routing

Confidence policy:
- HIGH: >=3 independent signals and at least one relationship constraint;
- MEDIUM: >=2 independent signals;
- LOW: one signal only;
- NONE: no signal.

For all outputs, `csmc_semantic_promotion` is hard-coded false.

The current three CC0 fixtures directly exercise vertex/index/UV/joints/weights/matrix/quaternion/morph/material-routing rules. Normal/tangent remain available rule slots but are not claimed calibrated by those three fixtures.

## SYNTHETIC / KNOWN-FIXTURE TEST
11/11 PASS:
- nine known-fixture high-confidence calibration cases;
- one CSMC-lookalike negative control remains LOW and unpromoted;
- one unknown semantic is rejected.

## NEW INFORMATION
Relationship constraints, not numeric appearance alone, are now executable calibration policy. The evaluator can distinguish detector quality on known formats from semantic evidence about CSMC.

## CLOSED HYPOTHESES
- glTF fixture similarity can confirm a CSMC semantic: REJECTED.
- three numeric-looking signals with no source/relationship discipline are sufficient for CSMC promotion: REJECTED.
- calibration code needs private payload bytes: REJECTED.

## CONFIDENCE CHANGES
- calibration/negative-control framework: MEDIUM -> VERY HIGH.
- current CSMC mesh/index/bone/weight/material semantics: unchanged UNRESOLVED.
- semantic promotions: 0.
