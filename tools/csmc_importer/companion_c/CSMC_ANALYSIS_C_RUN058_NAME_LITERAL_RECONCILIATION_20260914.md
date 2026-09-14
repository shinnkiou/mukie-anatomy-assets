# CSMC ANALYSIS COMPANION C — RUN C-058

## TYPE
Cross-lane public-safe negative-control reconciliation. This run combines the already-localized C-056 F06/F07 prefix differential with the newer mainline controlled name-literal probe. It does not repeat the literal scan or C-050 pair analysis.

## QUESTION
Can direct plaintext copies of the known F06/F07 teacher identifiers explain the C-056 12-qword variable-prefix differential?

## SOURCE
- Controlled corpus SHA-256: `be6132ef83959167ffd19218810e099f0bd164714fbd1ec4770f9296b38643b6`
- C-056 side result: `PHASE_LOCALIZED_RESIDUAL_DIFFERENTIAL_CANDIDATE`, localized F06/F07 delta = 12 qwords before the giant invariant run.
- Mainline name-probe head: `684c210f933803b16b80f5ba6dcb56186a162223`
- Mainline findings Drive ID: `1CULtcjqzUpHyPmG9YHZSAv3y_1RfreIf`
- Mainline aggregate Drive ID: `1uPek8ajbYZBOQlGp92WM5X_5RS_sLHIA`

## MAINLINE NEGATIVE CONTROL
The preregistered name probe searched only known fixture-generator identifiers rather than arbitrary printable strings:
- fixtures: 12 scripted controlled fixtures
- teacher identifiers: 53
- encodings: ASCII / UTF-16LE / UTF-16BE
- surfaces: full SQLite bytes + `character` BLOB
- total exact searches: 318
- SQLite literal occurrences: 0
- character-BLOB literal occurrences: 0

For the C-056 pair specifically:
- F06 (`CSMC_F06_CUBE_MAT2`): 4 known teacher identifiers, 0 literal hits on both surfaces.
- F07 (`CSMC_F07_TWO_CUBES`): 5 known teacher identifiers, 0 literal hits on both surfaces.

## RECONCILIATION
C-056 already localized the complete F06/F07 12-qword differential to the variable prefix before the 2118-qword giant invariant run.

The name probe independently shows that the known F06/F07 source identifiers do not occur anywhere in either searched CSMC surface as straightforward ASCII/UTF-16LE/UTF-16BE literals.

Therefore the narrow explanation:

> `C-056 12-qword prefix delta = direct plaintext copies of known F06/F07 teacher identifiers`

is rejected within the tested encodings and search surfaces.

## CLASSIFICATION
`C056_PREFIX_PLAINTEXT_NAME_EXPLANATION_REJECTED`

This is a confounder reduction, not a semantic binding.

## STILL OPEN
- transformed/compressed/encoded/hashed/remapped identity metadata;
- Modeler-generated identities;
- unrelated non-name structural fields;
- material-related serialization;
- object-related serialization;
- other unresolved owner/consumer explanations.

The result does **not** prove that names are absent from serialization. It only rejects direct literal copies in the tested encodings/surfaces.

## NOT ESTABLISHED
- material ownership of the 12 qwords: UNRESOLVED
- object ownership of the 12 qwords: UNRESOLVED
- owner/consumer relation: UNRESOLVED
- identity/name confounder fully removed: NO
- I3_VALID: false
- semantic promotion: false
- Blender emit: BLOCKED

## VALIDATION
Added fail-closed `csmc_analysis_c_c056_name_literal_reconcile_c058.py` with public-safe record/report/tests. It rejects nonzero literal occurrences, missing F06/F07 fixture detail, altered C-056 localization, name-region overclaim, semantic promotion, Blender emit, runtime dispatch, and raw/private publication.

Synthetic self-test: **10/10 PASS**.

## NEW INFORMATION
The C-056 variable-prefix localization is now narrower: its 12-qword delta cannot be dismissed as a straightforward copy of the known Blender-side F06/F07 names in the three tested text encodings. This removes one simple identity-confounder mechanism while deliberately leaving transformed/remapped identity and semantic-owner explanations open.

## NEXT
Prefer same-identity C-051 material/object controls over further plaintext carving. The next semantic advance still requires actual C-051 source/teacher/conversion/aggregate evidence or another independent owner/consumer relation.

## ISOLATION
`STRUCTURAL_ONLY`; semantic promotion=0; Blender emit=BLOCKED; runtime dispatch=false; runtime/MODELER/Worker/Canary/Control Gate/mainline/RIO-26 mutation=0; automatic integration=false; raw/private payload publication=false.
