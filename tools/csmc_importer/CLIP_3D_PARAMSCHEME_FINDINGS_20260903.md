# CLIP `.clip` 3D ParamScheme findings — 2026-09-03

## New finding

The `.clip` internal SQLite does not expose live `Manager3D`, `ModelInfo3D` or `ModelNodeInfo3D` tables for this document, but its built-in `ParamScheme` metadata still preserves a detailed CELSYS 3D semantic schema for those table families.

`ProjectInternalVersion = 1.1.0`.

The `DataType` mapping can be confirmed by cross-checking fields that also exist in live tables:

- `1 -> INTEGER`
- `2 -> REAL`
- `3 -> TEXT`
- `4 -> BLOB`

## Hidden / latent 3D schema clues

### `ModelNodeInfo3D`

16 semantic fields are defined, including:

- `NodeName` (TEXT)
- `NodeRotationR` (REAL)
- `NodeRotationVX/VY/VZ` (REAL)
- `NodeTranslationX/Y/Z` (REAL)
- `NodeScaleX/Y/Z` (REAL)
- GUI visibility/open state
- linked-list `NextIndex`

This is a strong clue that CELSYS has/had a per-node transform representation using a scalar rotation component plus vector XYZ, translation XYZ and scale XYZ. The exact mathematical convention of `NodeRotationR + VXYZ` is not yet proven.

### `ModelInfo3D`

48 fields are defined, including:

- `ModelRootNodeTranslation`
- `ModelSkeletonRootNodeTranslation`
- `ModelNodeRotation`
- `ModelNodeInfo`
- `BBox`
- `PartsHair / PartsFace / PartsBody / PartsAc`
- `PartsMaterial / PartsLayout / PartsMovable / PartsTransform`
- `DessindollShapeInfo`
- `DessindollBoneInfo`
- `ModelNameForGUI`
- `ModelNodeInfoCount / ModelNodeInfoFirstIndex`
- `ModelNnbNodeInfoCount / ModelNnbNodeInfoFirstIndex`

This is directly relevant to Body variants, Bone data, model transforms and node hierarchy recovery.

### `Manager3D`

46 fields are defined for camera/frustum/light/model-list state, including a link from:

`ModelInfoFirstIndex -> ModelInfo3D`.

### `ModelData3D`

Two fields:
- `CanvasId`
- `Layer3DModelData` (BLOB)

### `DessinDollInfo`

Links a layer object to `DessindollUUID`.

## Interpretation

The current document stores active 3D state through `Manager3DOd.SceneData` plus external CELSYS `scene` data rather than live rows in the older `Manager3D/ModelInfo3D/ModelNodeInfo3D` tables. However, the semantic names remain in the file format's schema registry.

This gives a concrete reverse-engineering dictionary for future runtime / scene differential work:

- Bone/node name search -> `NodeName`
- Pose change -> `NodeRotationR/VX/VY/VZ`
- Translation -> `NodeTranslationX/Y/Z`
- Scale -> `NodeScaleX/Y/Z`
- Body variant / parts -> `PartsBody`, `PartsMaterial`, `PartsLayout`, `PartsTransform`
- Bone-specific blob candidate -> `DessindollBoneInfo`

The next controlled pose experiment should therefore not only compare opaque bytes. It should also search MODELER/PAINT runtime memory for node-name strings and nearby float patterns that change with exactly one known bone rotation.

## Related `.clip` serialization comparison

The original CS3C `catalog_character` and the `.clip`-embedded `catalog_character` use the same:

- magic
- kind
- GUID `379b70c91e544437affc00c71d52f53c`
- inner version `2`
- payload offset `73`

but are not byte copies.

Original CS3C:
- blob size `39,485,161`
- logical `39,485,076`
- stored `39,485,088`

`.clip` embedded catalog_character:
- blob size `55,784,641`
- logical `55,784,555`
- stored `55,784,568`

Delta:
- blob/stored `+16,299,480`
- logical `+16,299,479`
- first byte difference is at header logical-size field offset `65`
- aligned 8-byte equal fraction across common length is only about `0.000047`

Therefore PAINT's `.clip` representation is a reserialized/augmented character payload with the same character identity, not a simple byte-for-byte copy of the source CS3C.

This reinforces the strategy of observing multiple CELSYS serialization surfaces rather than assuming one canonical opaque payload.