# CLIP 3D differential analyzer — durable test report
Date: 2026-09-03 JST

## Status
`CLIP_MODEL_SCENE_DIFF_TOOL_SYNTHETIC_PASS`

## Tool
`clip_3d_diff.py`

SHA-256:
`abe6f1ee68bde8afc5a45df32e04c1f780b152ca6cc1bb4172d3ba8ba433a944`

Purpose: compare two `.clip` files while keeping model/catalog-character, scene and SQLite-visible camera/identity state separate.

The analyzer reads:
- `CSFCHUNK`
- `CHNKExta`
- `CHNKSQLi`
- `Canvas3DModelLoader`
- `Manager3DOd.SceneData`
- `CharacterInfo`
- `Project`
- `CameraInfo`

It reports model and scene SHA/metadata separately and calculates exact equality, first changed byte, changed byte count/ranges and aligned 8-byte block equality.

## Synthetic public-safe test

`test_clip_3d_diff_synthetic.py`
SHA-256:
`7f06570ee807ecb0e3031e49ec04879a7140db54c44f4d6adaecf19e6489bf1c`

The test creates two fully synthetic CSFCHUNK documents with the same model/identity/camera and a one-byte-only change in the synthetic scene payload.

Measured result:
- PASS: `synthetic .clip scene-only differential fixture`
- same model UUID: true
- same character UUID: true
- same model GUID: true
- camera equal: true
- model exact equal: true
- scene exact equal: false
- scene different bytes: 1
- scene first difference: 87

This proves the tool can classify a scene-only change without falsely reporting model or camera changes.

## Private real-file sanity test

Self-compare of the authorized local `.clip` returned:
- model exact equal: true
- scene exact equal: true
- camera equal: true
- identity same: true

A private one-byte mutation inside the real scene external chunk was also detected as:
- model exact equal: true
- camera equal: true
- scene different bytes: 1
- scene first difference: 161

The mutated purchased-derived file is local-only and must not be uploaded to public GitHub.

## Next controlled experiment

When the user creates a second `.clip` with exactly one pose or body-variant change, run:

`python clip_3d_diff.py baseline.clip changed.clip`

Interpretation gate:
- scene-only change -> pose/camera/runtime state likely lives in scene path
- model-only change -> character/catalog state modified
- both -> cross-layer serialization or save normalization

Pair this with ParamScheme field names (`NodeRotation*`, `NodeTranslation*`, `PartsBody`, `DessindollBoneInfo`) and the MODELER v0.5 runtime character dump.