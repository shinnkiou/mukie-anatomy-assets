# CSMC ANALYSIS COMPANION C — RUN C-007 — repeated count+array grammar distribution

Status: STATIC SIDE-LANE PASS / ZERO MODELER / ZERO RUNTIME / ZERO MAINLINE MUTATION

## QUESTION
How broadly does the already-confirmed `u32be count + BE numeric array` grammar distribute across the active Manager3DOd fields, and which structural axes must a semantics-free codec retain?

## PROBE
Reused only the seven exact-fit active fields already established by `CELSYS_VECTOR_SERIALIZATION_FINDINGS_20260903`. No target payload rescan and no repeated +197/+195 or +965 fitting.

Observed fields:
- count 3 / BE-f64: 3 fields
- count 4 / BE-f64: 1 field
- count 6 / BE-f64: 2 fields
- count 6 / BE-f32: 1 field

Derived distributions:
- count: `3 -> 3`, `4 -> 1`, `6 -> 3`
- numeric encoding: `BE-f64 -> 6`, `BE-f32 -> 1`
- serialized total size including count prefix: `28 B -> 4`, `36 B -> 1`, `52 B -> 2`

Two ambiguity results matter:
1. `count=6` occurs with both BE-f64 and BE-f32, so count does not determine numeric width.
2. `28 B` occurs for both `(count=3, BE-f64)` and `(count=6, BE-f32)`, so total BLOB size does not determine the count/width tuple.

## INTERPRETATION
The confirmed CELSYS counted numeric family is a reusable grammar, not a single fixed-arity field encoding. A generic codec descriptor must retain at least the independent axes `count` and `numeric_encoding/element_width`, plus exact-length validation. Vector arity must not be promoted to transform/position/rotation semantics by itself.

## NEW INFORMATION
- The same counted prefix grammar spans at least three observed counts: 3, 4, and 6.
- The same grammar spans two numeric widths: BE-f64 and BE-f32.
- Count and numeric width are not functionally dependent in the observed sample.
- Serialized byte length alone is insufficient to recover the `(count, width)` tuple because 28-byte encodings collide.

## CLOSED HYPOTHESES
- The counted numeric grammar has one fixed arity: REJECTED.
- The count uniquely determines f32 vs f64 width: REJECTED.
- Total serialized BLOB size uniquely determines count and numeric width: REJECTED.
- Exact-fit counted numeric form identifies semantic role such as transform: REJECTED.

## CONFIDENCE CHANGES
- Generic reusable counted-numeric codec family: VERY HIGH -> VERY HIGH, with broader cross-field support.
- `count` and `numeric_encoding` as independent codec axes: MEDIUM -> VERY HIGH.
- Size-only typed decoding: LOW -> VERY LOW.
- Semantic interpretation from arity alone: remains UNPROVEN / VERY LOW.

## NEXT QUESTION
What structural relation is actually supported among `NodeName`, `ModelNodeInfoCount`, `ModelNodeInfoFirstIndex`, and `ModelNodeInfo3D.NextIndex` without treating latent ParamScheme schema as current payload layout?

## Guardrails
- No raw proprietary payload bytes recorded.
- No geometry/index/material/bone/weight semantic promotion.
- Mainline canonical was not re-polled.
