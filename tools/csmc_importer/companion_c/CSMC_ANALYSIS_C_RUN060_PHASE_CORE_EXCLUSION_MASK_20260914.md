# CSMC ANALYSIS COMPANION C — RUN C-060

## QUESTION
Can the C-057 transitive invariant suffix cores become a fail-closed search mask so future controlled localization skips regions already proven invariant?

## RESULT
Yes, for the current six fixtures only.

- phase 7: F02/F04/R01 share 1809 exact suffix qwords + one terminal qword.
- phase 1: F06/F07/R03 share 1801 exact suffix qwords + one terminal qword.

Across the six fixtures:
- total surface = **14,180 qwords**
- proven invariant core excluded = **10,830 qwords** (~76.4%)
- remaining search surface = **3,350 qwords** (~23.6%)

The remaining surface is the variable prefix plus each one-qword terminal. This is structural search-space reduction only.

## IMPLEMENTATION
`csmc_analysis_c_phase_core_exclusion_mask_c060.py` validates the exact C-057 ranges and emits per-fixture prefix/core/terminal intervals. Altered ranges/totals, missing fixtures, semantic promotion, runtime dispatch, Blender emit, or raw/private publication fail closed.

Local self-test: **10/10 PASS**.

## NEW INFORMATION
For these six fixtures, later public-safe differential work can skip more than three quarters of the qword surface without losing any currently observed pair-specific change, because those suffix ranges are proven exact invariant cores by transitivity.

## LIMITS
Invariant does not mean geometry/material/rig/owner. Scope is only the six C-057 fixtures. C-058/C-059 identity/name confounders remain open except for direct plaintext teacher-name copies in the tested encodings and surfaces.

## ISOLATION
`STRUCTURAL_ONLY`; semantic promotion=0; Blender emit=BLOCKED; runtime dispatch=false; runtime/MODELER/Worker/Canary/Control Gate/mainline/RIO-26 mutation=0; automatic integration=false; raw/private payload publication=false.

## NEXT
Apply this mask only to genuinely new public-safe differentials. Do not re-scan proven cores and do not infer semantics from invariance.
