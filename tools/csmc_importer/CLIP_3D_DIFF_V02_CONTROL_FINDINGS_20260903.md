# CLIP 3D differential analyzer v0.2 — controlled-state hardening
Date: 2026-09-03 JST

## Status
`CLIP_DIFF_CONTROL_INVARIANTS_ADDED_AND_SYNTHETIC_PASS`

## Change
The `.clip` differential analyzer now separates expected scene/model payload changes from accidental changes to surrounding SQL-visible state.

In addition to model/scene BLOB byte diffs and camera comparison, v0.2 snapshots these control groups:
- Canvas size/unit/resolution/model-loader index
- CanvasItem identity/type/caption/3D data ID
- LayerObject object chain: camera, character, environment light, parallel lights, selection/visibility/links
- CharacterInfo UUID/link
- Manager3DOd non-SceneData state, including MultiView camera numeric BLOBs and zoom/distance/clip values

It reports:
- `sql_controls_equal`
- `sql_control_table_equal` per group

## Why it matters
A controlled pose/variant experiment is only interpretable when the model identity, camera, canvas, object chain and non-scene controls remain stable. This turns that requirement into an automatic assertion rather than a manual assumption.

## Tests
Synthetic pair: same model/camera/controls, one changed scene byte.

PASS:
- same model UUID = true
- same character UUID = true
- same model GUID = true
- camera equal = true
- SQL controls equal = true
- every SQL control table equal = true
- model BLOB exact equal = true
- scene different bytes = 1

## Hashes
- `clip_3d_diff.py` SHA-256: `427f409136fefbc160e2aa6808070d278cb3955ba415201a6f705eaa335ed7c3b`
- `test_clip_3d_diff_synthetic.py` SHA-256: `d0d6b63c0187275cc8726caa5ee588390e9a955cf5e6a2bbdc9205f20582c9be`

## GitHub
- analyzer update commit: `12ade676bb6d0e794995088744875fa8a8d6b8af`
- synthetic assertion update: `7a0199af9abbe2f162498ee786ad0299843c56da`

## Next
When a real one-variable `.clip` pair is supplied, reject/flag the experiment if any unintended SQL control group changes. If controls stay equal, classify the semantic change by model BLOB vs scene BLOB delta.
