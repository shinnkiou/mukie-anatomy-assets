# Companion C — Run C-031

## QUESTION
Do the seven confirmed active counted-numeric fields contain any semantics-free name/arity/width relationship not already captured by C-007/C-009?

## PROBE
Re-audited only the fixed side-branch finding `CELSYS_VECTOR_SERIALIZATION_FINDINGS_20260903.md`. No new byte scan was performed.

Confirmed active fields:
- `MultiViewTargetPosition`: count 3, BE-f64
- `MultiViewPresetCameraFrustum`: count 6, BE-f64
- `MultiViewPresetCameraPosition`: count 3, BE-f64
- `MultiViewPresetCameraRotate`: count 4, BE-f64
- `MultiViewPresetCameraUpGuide`: count 3, BE-f64
- `MultiViewNearClipEnable`: count 6, BE-f32
- `MultiViewNearClipPosition`: count 6, BE-f64

## REAL AGGREGATE RESULT
A stronger structural negative rule is available:

`MultiViewNearClipEnable` and `MultiViewNearClipPosition` share the `MultiViewNearClip` lexical prefix and both have count=6, yet use different element widths (BE-f32 vs BE-f64). Therefore neither arity alone nor shared lexical prefix + arity determines numeric element width.

Also, fields ending in `Position` occur with counts 3 and 6, so the `Position` suffix does not determine arity.

The only BE-f32 field in this seven-field sample is `MultiViewNearClipEnable`, and it is all zero in this file. This is insufficient to establish a general `Enable -> f32`, boolean-vector, or flag-array serializer rule.

## NEW INFORMATION
- Same prefix + same count can still use different numeric widths.
- `Position` lexical suffix does not determine array arity.
- The single `Enable` f32 observation is a field-local fact only, not a serializer-wide rule.

## CLOSED HYPOTHESES
- arity determines numeric width: REJECTED
- lexical prefix plus arity determines numeric width: REJECTED
- `Position` suffix determines arity: REJECTED
- `Enable` universally implies BE-f32: NOT SUPPORTED / must remain unconfirmed
- all-zero counted vector implies boolean/flag semantics: REJECTED as an inference rule

## CONFIDENCE CHANGES
- count and element width as independent codec axes: VERY HIGH -> EXTREMELY HIGH within this seven-field active sample
- name-prefix-based width prediction: LOW -> VERY LOW
- `Enable` f32 generalization: remains VERY LOW
- quaternion-like rotation candidate: unchanged HIGH candidate only

## NEXT QUESTION
Has the fixed snapshot now become exhausted across every non-duplicative static-analysis axis, such that further progress requires one of the already-defined new static evidence inputs rather than another reinterpretation of the same aggregates?
