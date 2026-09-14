# CSMC ANALYSIS COMPANION C — RUN C-057

## TYPE
Public-safe transitive structural deduction from the mainline phase-class aggregate. No raw qword values are used or published.

## QUESTION
Do the pairwise same-phase invariant runs imply any multi-fixture invariant core, or are they only independent pair phenomena?

## METHOD
Use a common anchor fixture plus suffix alignment. If A↔B and A↔C both contain exact runs that end at the same A payload boundary, then the overlapping suffix interval in A is equal to the corresponding intervals in both B and C. This transitive equality needs only published positions, lengths, qword counts, and trailing counts.

## PHASE 7
Published pairs:
- F02↔F04: counts 2212/2320, starts 402/510, exact length 1809, tails 1/1.
- F02↔R01: counts 2212/2233, starts 402/423, exact length 1809, tails 1/1.

Both pairs use the exact same F02 interval `[402,2211)` and both end one qword before payload end. Therefore the corresponding F04 `[510,2319)` and R01 `[423,2232)` intervals must also be mutually identical through F02.

Result: **phase-7 transitive invariant suffix core = 1809 qwords across F02/F04/R01**, with one trailing qword on each fixture.

## PHASE 1
Published pairs:
- F06↔F07: counts 2564/2576, starts 445/457, exact length 2118, tails 1/1.
- F06↔R03: counts 2564/2275, starts 762/473, exact length 1801, tails 1/1.

Both runs end at F06 qword boundary 2563. The 1801-qword F06↔R03 run is therefore a suffix of the larger 2118-qword F06↔F07 run. Mapping the shorter F06 interval into F07 gives start `457 + (762 - 445) = 774`.

Result: **phase-1 transitive invariant suffix core = 1801 qwords across F06/F07/R03**:
- F06 `[762,2563)`
- F07 `[774,2575)`
- R03 `[473,2274)`
all followed by one trailing qword.

F06↔F07 additionally share a pair-specific 317-qword extension before that three-fixture core (`2118 - 1801 = 317`).

## CLASSIFICATION
`PHASE_CLASS_TRANSITIVE_INVARIANT_SUFFIX_CORE_CANDIDATE`

This is stronger than treating the selected same-mod exact runs as unrelated pair coincidences: within two observed phase classes, a common exact suffix can be proven across three fixtures by transitivity. It remains limited to the tested corpus.

## WHAT THIS DOES NOT MEAN
- The common core is not identified as geometry, index, material, rig, or weight data.
- `logical_length mod 8` is not claimed globally necessary or sufficient.
- A structural invariant suffix does not prove an owner/consumer.
- No I3 semantic binding is promoted.
- Blender emit remains blocked.

## VALIDATION
Added `csmc_analysis_c_transitive_phase_core_c057.py` plus public-safe record/report/tests. Validator fails closed on broken suffix anchoring, anchor/phase mismatch, non-nested phase-1 runs, altered trailing counts, semantic promotion, Blender emit, runtime dispatch, or raw/private publication.

Synthetic self-test: **8/8 PASS**.

## NEW INFORMATION
The phase-class result now has a multi-fixture consequence rather than only a pairwise one. In the tested corpus:
- phase 7 has at least a 1809-qword exact suffix core shared across three substantially different controlled fixtures;
- phase 1 has at least a 1801-qword exact suffix core shared across three fixtures even though F06/F07 and R03 differ in the controlled model properties and render-part cardinality.

This makes those regions stronger *structural invariant* exclusion zones for later differential localization, while leaving their meaning unresolved.

## NEXT
Future controlled localization can exclude the proven phase-core region first and focus on the prefix plus terminal qword(s). Do not infer semantics from invariance alone. A genuinely new C-051 same-identity corpus or another new public-safe differential is still required for semantic progress.

## ISOLATION
`STRUCTURAL_ONLY`; semantic promotion=0; Blender emit=BLOCKED; runtime dispatch=false; runtime/MODELER/Worker/Canary/Control Gate/mainline/RIO-26 mutation=0; automatic integration=false; raw/private payload publication=false.
