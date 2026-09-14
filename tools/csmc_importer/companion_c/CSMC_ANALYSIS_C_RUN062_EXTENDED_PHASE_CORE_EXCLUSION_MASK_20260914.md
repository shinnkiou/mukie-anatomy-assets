# CSMC Analysis Companion C — C-062 — Extended Phase-Core Exclusion Mask — 2026-09-14

## Question
Can the new phase-3 R04/V01 holdout be added to the C-060 search mask without pretending it has the same transitive or semantic evidence class as the phase-1/7 cores?

## Result
Yes. The existing C-060 six-fixture mask is preserved unchanged and the new R04/V01 phase-3 pair is added as a separately tagged independent holdout mask.

- phase 7 transitive: F02 / F04 / R01, core length 1809 qwords
- phase 1 transitive: F06 / F07 / R03, core length 1801 qwords
- phase 3 independent holdout pair: R04 / V01, core length 1800 qwords

R04 mask: prefix [0,480), excluded core [480,2280), terminal [2280,2282).
V01 mask: prefix [0,533940), excluded core [533940,535740), terminal [535740,535742).

Across all eight represented fixtures: total 552,204 qwords; excluded validated-core surface 14,430 qwords; remaining search surface 537,774 qwords. The low aggregate exclusion percentage is dominated by the very large VRoid variable prefix and does not weaken the exact 1,800-qword holdout-core observation.

## Evidence-class guard
R04/V01 is not relabeled as a three-fixture transitive core and is not treated as a same-identity semantic control. It remains `INDEPENDENT_PHASE3_HOLDOUT_PAIR`.

## Validation
- fail-closed self-test: 13/13 PASS
- pytest: 2/2 PASS

## Gate state
`STRUCTURAL_ONLY`; semantic binding unresolved; semantic promotion=0; Blender emit blocked; runtime dispatch=false; raw/private CSMC publication=false; runtime/MODELER/Worker/Canary/Control Gate/mainline/RIO-26 mutations=0; automatic integration=false.

## Next
Apply bounded preregistered size/stride/count relationship probes only to remaining variable-prefix/terminal surfaces. Do not repeat exact-qword reuse scans and do not infer owner/geometry/material/rig semantics from mask membership.
