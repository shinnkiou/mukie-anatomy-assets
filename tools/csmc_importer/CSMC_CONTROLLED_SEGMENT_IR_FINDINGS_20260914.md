# CSMC Controlled Segment IR Findings — 2026-09-14

## Question

Can the already-validated phase-normalized pair invariants be connected to the importer as explicit structural ranges without promoting any payload content semantics?

## Result

Yes. The mainline now represents each validated same-phase pair as three qword ranges per fixture:

1. `VARIABLE_PREFIX_CANDIDATE_REGION`
2. `EXACT_INVARIANT_CORE`
3. `TERMINAL_REMAINDER_CANDIDATE_REGION`

The segmentation is derived only from existing validated pair-invariant coordinates. It contains no qword values or private payload bytes.

Seven already-published same-phase pairs are materialized in the aggregate sidecar. The VRoid holdout R04↔V01 is included and retains its independent 1800-qword invariant core.

## Importer consequence

The importer/research pipeline can now carry a structural search domain instead of treating the full protected payload as one undifferentiated region.

The exact invariant core is excluded from content-candidate searches for the associated pair; the variable prefix and terminal remainder remain eligible structural candidate regions.

This is an IR/search-space advance only. It does **not** mean the variable prefix is geometry, index, UV, material, bone, or weight data.

## Scout toolbox decision

The Scout numeric candidate probe was reviewed but not invoked for this phase. Current bounded prefixes are phase-dependent/high-entropy, and R04→R05 is not a one-variable weight-value pair because assignment cardinality also changes. Numeric plausibility would not yet separate the competing hypotheses.

## Semantic gate

- geometry: UNRESOLVED
- index/topology: UNRESOLVED
- UV/material/bone/weight: candidate-only as before
- semantic promotion: 0
- Blender emit: BLOCKED
- runtime/MODELER/Worker actions: 0

## Next action

Use the structural segment ranges to test **local sub-block growth / boundary relations inside the candidate regions**, not whole-prefix affine size laws and not whole-prefix exact-qword reuse. If a bounded region with a clean controlled relationship emerges, the Scout numeric probe may then be applied once as a candidate reducer.
