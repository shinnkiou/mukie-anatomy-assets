# CSMC ANALYSIS COMPANION C — Run C-018

## QUESTION
Can the nearest binding candidate (`COUNTED_BE_TO_PLUS965`) be tested later with a preregistered, non-post-hoc static scan protocol that controls the number of roles/trials and refuses semantic promotion?

## HYPOTHESIS
A fixed scan over the 22 known complete +965 records can test counted-BE codec binding without sliding windows, runtime interaction, or post-hoc role creation.

## PROBE
Added `csmc_analysis_c_preregistered_counted_be_scan.py` on the Companion C branch. The scan is fixed before any private binary is supplied:
- 22 complete records per serialization side
- 2 sides
- 3 roles per record only: `stable_prefix`, `control_zone`, `rewritten_tail`
- no sliding windows
- no post-hoc role subdivision
- exact-fit counted BE-f32 only for these whole roles
- recurrence requires >=2 exact fits in distinct records for the same side+role

## SYNTHETIC TEST
PASS. Arithmetic invariants and recurrence logic were tested independently.

## REAL AGGREGATE RESULT
The protocol is READY but the current private-payload scan was not executed. The dedicated Companion C Drive namespace contains only the runlog; no isolated +965 binary is present. This lane is prohibited from acquiring one through MODELER/runtime/Worker/mainline.

Preregistered trial surface: 132 cells = 22 records × 2 sides × 3 roles.

Role arithmetic:
- stable_prefix: 168 B -> expected BE-f32 count 41
- control_zone: 56 B -> expected BE-f32 count 13
- rewritten_tail for 48-qword record: 160 B -> expected count 39
- rewritten_tail for 49-qword record: 168 B -> expected count 41
- counted BE-f64 whole-role fit is impossible for all preregistered roles because each role length is 0 mod 8 while `4 + 8*n` is 4 mod 8.

## INTERPRETATION
The scan question is now preregistered before data availability, reducing post-hoc fitting risk. Absence of the isolated binary is an input boundary, not an analysis failure. The protocol can be run unchanged if an already-existing authorized isolated payload is later placed in the Companion C lane.

## NEW INFORMATION
- The counted-BE binding test can be reduced to a fixed 132-cell trial surface.
- BE-f64 can be eliminated from whole-role candidates by length congruence alone.
- BE-f32 expected counts are fixed in advance as 41 / 13 / 39-or-41 depending on role/record length.
- Current Companion C storage has no binary input for the real scan.

## CLOSED HYPOTHESES
- The scan needs sliding-window discovery: REJECTED.
- f64 and f32 both need testing on whole preregistered roles: REJECTED.
- A current-payload scan can be executed from Companion C's own stored artifacts right now: REJECTED.
- A codec hit would justify geometry/index semantics: REJECTED.

## CONFIDENCE CHANGES
- preregistered counted-BE binding protocol: HIGH -> VERY HIGH
- f64 whole-role candidacy on the 3 preregistered roles: LOW -> ZERO by arithmetic
- f32 exact-fit target counts: HIGH -> VERY HIGH
- current +965 codec binding: remains UNRESOLVED
- geometry/index semantics: remains UNRESOLVED/BLOCKED

## NEXT QUESTION
Can alignment/length arithmetic further shrink the future +965 scan surface without reading any new payload bytes, especially at whole-record and subrole boundaries?
