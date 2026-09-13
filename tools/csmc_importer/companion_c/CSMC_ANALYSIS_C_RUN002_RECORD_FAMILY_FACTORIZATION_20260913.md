# CSMC Analysis Companion C — Run C-002 Record Family Factorization

## QUESTION
Can the 22 complete `+965` records be represented losslessly by one record-class variable, or must record length and q21..27 preservation signature remain independent axes in an importer IR?

## HYPOTHESIS
If one axis fully determines the other, either each preservation signature maps to exactly one record length or each record length maps to exactly one preservation signature.

## PROBE
`csmc_analysis_c_record_family_factorization.py` consumes only the public-safe control-zone aggregate table and computes the joint family structure and information quantities.

## SYNTHETIC TEST
`test_csmc_analysis_c_record_family_factorization.py` includes a shared-signature fixture and verifies that the two axes are not collapsed. PASS locally before persistence.

## REAL AGGREGATE RESULT
Five observed `(length_blocks, preserve_signature)` families:
- 48 / `0000110`: 7
- 48 / `0000111`: 3
- 48 / `0001110`: 3
- 49 / `0000111`: 3
- 49 / `1000111`: 6

Information summary: H(length)=0.9760206482 bits; H(signature)=1.9400715293; H(joint)=2.2127988020; I(length;signature)=0.7032933755; H(length|signature)=0.2727272727; H(signature|length)=1.2367781538.

`0000111` is shared by both 48- and 49-qword records (3 each), so length is not a function of signature. Each length has multiple signatures, so signature is not a function of length.

## INTERPRETATION
A minimal parser/IR should store `length_blocks` and `preserve_signature` independently. Do not collapse the five observed joint cells into a semantic record enum yet. Semantic record type remains unproven.

## NEW INFORMATION
- Five observed joint structural families exist in the 22-record sample.
- Record length and preservation signature are correlated but not mutually determining.
- A two-axis representation is the smallest current lossless structural model supported by aggregate evidence.

## CLOSED HYPOTHESES
- `preserve signature completely identifies the 48/49 branch` — REJECTED.
- `record length completely identifies preservation behavior` — REJECTED.

## CONFIDENCE CHANGES
- `48/49 is mere padding`: remains VERY LOW.
- `48/49 participates in a serializer branch`: HIGH, unchanged.
- `serializer branch can be represented as one categorical variable`: MEDIUM -> LOW.
- `minimal importer IR needs orthogonal structural features`: LOW -> HIGH.

## NEXT QUESTION
Can a semantics-free intermediate schema represent the current boundary classes and record-family axes while keeping geometry/index/transform/material/hierarchy semantic claims explicitly unresolved?
