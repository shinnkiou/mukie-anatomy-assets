# CELSYS counted-vector serialization findings — 2026-09-03

## Status
`COUNTED_BIG_ENDIAN_VECTOR_ENCODING_CONFIRMED_FOR_MANAGER3DOD`

The active `.clip` internal SQLite contains several `Manager3DOd` BLOB columns that decode consistently as:

`u32 big-endian element_count` + `element_count × big-endian numeric value`

Two observed payload element encodings occur:
- big-endian float64
- big-endian float32

## Confirmed decoded fields

- `MultiViewTargetPosition`: count 3, BE float64
  - approximately `[0, 78.4026426546, 2.14490015283]`
- `MultiViewPresetCameraFrustum`: count 6, BE float64
- `MultiViewPresetCameraPosition`: count 3, BE float64
  - approximately `[0, 78.4026426546, 409.482655011]`
- `MultiViewPresetCameraRotate`: count 4, BE float64
  - `[1.0, 0.0, 0.0, 0.0]`
- `MultiViewPresetCameraUpGuide`: count 3, BE float64
  - `[0.0, 1.0, 0.0]`
- `MultiViewNearClipEnable`: count 6, BE float32
  - all zeros in this file
- `MultiViewNearClipPosition`: count 6, BE float64

All seven matches are exact length fits; no trailing bytes are needed to explain them.

## Rotation inference

The four-value `MultiViewPresetCameraRotate = [1,0,0,0]` is strongly consistent with an identity quaternion representation.

Separately, the CLIP `ParamScheme` latent `ModelNodeInfo3D` schema names rotation fields:

- `NodeRotationR`
- `NodeRotationVX`
- `NodeRotationVY`
- `NodeRotationVZ`

The naming `R + vector XYZ` together with a four-component identity value `[1,0,0,0]` makes a scalar-plus-vector quaternion interpretation a strong working hypothesis for CELSYS node rotations.

This is **not yet a direct proof** that `ModelNodeInfo3D.NodeRotationR/VXYZ` uses the exact same serialized byte layout or component convention. A controlled one-bone rotation is still required.

## Why this matters

The investigation no longer has to treat every CLIP SQLite BLOB as opaque. At least one active 3D-state family has a simple numeric encoding that can be decoded without MODELER-memory extraction.

For a controlled pose pair, the next search can look for:

1. four-component counted BE-f64 sequences near an identity rotation,
2. components that change while translation/scale remain fixed,
3. node-name / ParamScheme semantic clues,
4. correspondence to the user-applied known bone rotation.

If the same representation appears in runtime scene/node data, Bone transform recovery can begin independently of Mesh/Texture extraction.

## Tool

`celsys_counted_vector_probe.py`
SHA-256: `7590102f25d9157d15004898b12c3b0c7ef468a1a621b9888251f629acb36b3d`

The tool scans SQLite BLOB cells and only reports values where the leading BE count exactly explains the remaining byte length as all-f64 or all-f32 data.