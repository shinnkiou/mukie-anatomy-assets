# Companion C — Run C-022

## QUESTION
Can codec-binding scope be represented in the importer IR without changing any semantic slot or Blender emission gate?

## HYPOTHESIS
Record-family locality/generalization is structural evidence and should be encoded as a separate axis from semantic meaning.

## PROBE
Added `csmc_analysis_c_binding_scope.py` with four scope states:
- `UNCONFIRMED`
- `ROLE_LEVEL_UNSCOPED`
- `FAMILY_LOCAL`
- `CROSS_FAMILY_GENERALIZED`

The classifier consumes an already-established binding level plus family keys observed among recurrent hits. It does not assign geometry/index/transform/material/hierarchy semantics.

## SYNTHETIC TEST
4/4 PASS:
- candidate binding -> `UNCONFIRMED`
- confirmed binding with no family metadata -> `ROLE_LEVEL_UNSCOPED`
- confirmed binding with one repeated family -> `FAMILY_LOCAL`
- confirmed binding spanning multiple families -> `CROSS_FAMILY_GENERALIZED`

## REAL AGGREGATE RESULT
No real +965 codec binding exists yet, so no real scope state is promoted. The result is an IR capability and evidence-policy refinement only.

## NEW INFORMATION
- Structural binding scope can be represented independently of semantic meaning.
- Family locality and cross-family generalization can be preserved without changing semantic confidence.
- The parser can later accept codec evidence while keeping Blender geometry emission blocked.

## CLOSED HYPOTHESES
- Codec-binding scope must be encoded as a semantic record type: REJECTED.
- Cross-family generalization should automatically increase semantic confidence: REJECTED.
- Adding binding-scope metadata requires changing the Blender emission gate: REJECTED.

## CONFIDENCE CHANGES
- binding-scope axis as part of minimal IR: MEDIUM -> VERY HIGH
- semantic independence of binding scope: HIGH -> VERY HIGH
- real +965 binding scope: remains UNCONFIRMED

## NEXT QUESTION
Can a static-analysis handoff manifest define exactly what future isolated evidence may be imported into Companion C while guaranteeing no mainline/runtime contact and no automatic semantic promotion?
