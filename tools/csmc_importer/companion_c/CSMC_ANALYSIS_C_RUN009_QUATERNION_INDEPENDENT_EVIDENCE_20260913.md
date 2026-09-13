# CSMC ANALYSIS COMPANION C — RUN C-009 — quaternion candidate independent evidence

Status: STATIC SIDE-LANE PASS / TWO EVIDENCE SURFACES / ZERO MODELER / ZERO RUNTIME

## QUESTION
Does the quaternion-like rotation candidate have independent evidence beyond the single active count-4 identity vector, and how far can that evidence be promoted without claiming current node byte layout?

## PROBE
Compared two distinct fixed-snapshot evidence surfaces:

A. Active SQLite BLOB observation:
- `Manager3DOd.MultiViewPresetCameraRotate`
- exact counted BE-f64 vector
- count = 4
- decoded value = `[1, 0, 0, 0]`

B. Latent ParamScheme schema observation:
- `ModelNodeInfo3D.NodeRotationR`
- `NodeRotationVX`
- `NodeRotationVY`
- `NodeRotationVZ`
- four REAL scalar fields named as one `R` plus vector `XYZ`

These are not the same storage representation: one is an active counted BLOB camera field; the other is a latent per-node REAL-field schema.

## INTERPRETATION
The candidate no longer rests on one isolated identity vector. Two distinct CELSYS surfaces independently favor a four-component scalar-plus-vector rotation representation consistent with a quaternion family. This supports a format-family convention candidate, but it still does not prove the current external scene/character node payload uses the same byte layout, component order, handedness, normalization behavior, or multiplication convention.

## NEW INFORMATION
- Quaternion consistency is supported by two different evidence surfaces: active camera serialization and latent node schema naming.
- The active surface supplies a canonical-looking four-component identity value; the latent surface supplies an explicit scalar-plus-vector field decomposition.
- The common interpretation can be retained as a codec/semantic candidate without equating their storage layouts.

## CLOSED HYPOTHESES
- Quaternion candidacy depends on only one isolated four-value observation: REJECTED.
- Active camera BLOB layout and latent node REAL fields are proven byte-identical encodings: REJECTED.
- `[1,0,0,0]` plus R/VXYZ naming alone proves the current external scene node rotation layout: REJECTED.

## CONFIDENCE CHANGES
- CELSYS rotation family is quaternion-like scalar-plus-vector: MEDIUM-HIGH -> HIGH.
- Exact node rotation byte layout in current external payload: remains UNRESOLVED / VERY LOW.
- Exact component/multiplication/handedness convention: remains UNPROVEN.
- `+965` transform/bone interpretation: remains VERY LOW / UNPROVEN.

## NEXT QUESTION
Do existing static artifacts contain direct evidence for a 4x4 matrix layout, mesh index representation, or normalized skin weights, or are similarly named SQL/index/bone fields only semantic traps?

## Guardrails
- Candidate promotion stops below `CONFIRMED_SEMANTIC`.
- No current-payload node mapping or controlled known-rotation differential exists in this side lane.
