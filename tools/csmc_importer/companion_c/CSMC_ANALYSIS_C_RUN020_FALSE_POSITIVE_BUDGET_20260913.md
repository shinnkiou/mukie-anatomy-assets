# Companion C — Run C-020

## QUESTION
Can C-018's preregistered scan be given an explicit familywise false-positive budget before any additional data is inspected?

## HYPOTHESIS
If each trial only asks whether one predetermined 32-bit count value appears at the start of one preregistered role, a simple high-entropy null gives a conservative reference scale for single hits versus same-family recurrence.

## PROBE
Fixed trial structure from C-018:
- 22 records
- 2 serialization sides
- 3 preregistered roles
- 132 total trial cells
- 6 side+role families, each with 22 cells
- one predetermined expected count per cell from length arithmetic

Reference null for guardrail purposes only: one exact 32-bit prefix match has probability at most `2^-32` under a uniform independent prefix model.

## REAL AGGREGATE RESULT
Using union bounds:
- any single hit among 132 cells: <= `132 * 2^-32` = about `3.07e-8`
- any pair in the same preregistered family: <= `6 * C(22,2) * 2^-64` = about `7.51e-17`

These are not claims that CELSYS data are random or independent. They are a calibration showing why one isolated exact fit should remain weak while recurrent same-role fits are much stronger evidence.

## NEW INFORMATION
- The preregistered recurrence threshold has an explicit familywise reference bound.
- Same-family recurrence is about nine orders of magnitude stronger than accepting any single hit under the same simple null.
- Trial accounting is fixed before future data inspection.

## CLOSED HYPOTHESES
- One exact count fit should be enough for confirmed codec binding: REJECTED.
- Trial multiplicity can be ignored: REJECTED.
- Post-hoc regrouping after observing hits is acceptable: REJECTED.

## CONFIDENCE CHANGES
- requirement for >=2 same-family exact fits: HIGH -> VERY HIGH
- single exact fit as binding evidence: LOW -> VERY LOW
- current +965 codec binding: remains UNRESOLVED

## NEXT QUESTION
Can the evidence contract be strengthened so that recurrence must also preserve the same record-family signature, not only the same side+structural role?
