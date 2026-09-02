# CLIP 3D ParamScheme schema-map findings — 2026-09-03

## Status
`LATENT_3D_NODE_SCHEMA_RECONSTRUCTED_FROM_PARAMSCHEME`

This is a read-only structural finding from the existing authorized `.clip` file. No mesh, texture, or purchased model bytes are included here.

## Main finding
The active `.clip` internal SQLite has a `ParamScheme` table that preserves field definitions for older/latent 3D SQL tables even when those tables are not instantiated as live tables in this document.

The strongest recovered relationship is:

`ModelInfo3D.ModelNodeInfoFirstIndex -> ModelNodeInfo3D`

with:
- `ModelNodeInfoCount` (INTEGER)
- `ModelNodeInfoFirstIndex` (INTEGER, link to `ModelNodeInfo3D`)
- `ModelNodeInfo3D.NextIndex` (INTEGER)

This strongly suggests a count + first-index + linked-next representation for the historical SQL-side node list.

## ModelNodeInfo3D semantic fields
Recovered field definitions include:
- `NodeName` TEXT
- `NodeRotationR` REAL
- `NodeRotationVX` REAL
- `NodeRotationVY` REAL
- `NodeRotationVZ` REAL
- `NodeTranslationX/Y/Z` REAL
- `NodeScaleX/Y/Z` REAL
- `NodeTreeGUIOpened` INTEGER
- `NodeTreeGUIVisible` INTEGER
- `NextIndex` INTEGER

This provides an explicit semantic target for a one-bone controlled pose experiment.

## ModelInfo3D fields relevant to current research
The latent definition also includes:
- `ModelRootNodeTranslation` BLOB
- `ModelSkeletonRootNodeTranslation` BLOB
- `ModelNodeRotation` BLOB
- `ModelNodeInfo` BLOB
- `BBox` BLOB
- `PartsBody` INTEGER
- `PartsMaterial` INTEGER
- `PartsLayout` INTEGER
- `PartsTransform` INTEGER
- `DessindollShapeInfo` BLOB
- `DessindollBoneInfo` BLOB
- `ModelNodeInfoCount` INTEGER
- `ModelNodeInfoFirstIndex` -> `ModelNodeInfo3D`

## Important interpretation
Current documents use `Manager3DOd.SceneData` plus CELSYS `scene` serialization instead of live `ModelInfo3D` / `ModelNodeInfo3D` rows. Therefore these latent SQL definitions should be treated as a semantic map, not proof that the current scene blob uses an identical byte layout.

However, this map materially narrows the next runtime search:
1. rotate exactly one known bone;
2. capture before/after bounded MODELER memory neighborhoods;
3. search for node-name strings;
4. test nearby numeric changes against quaternion fields `R/VX/VY/VZ`;
5. cross-check against the already confirmed counted big-endian numeric-vector family.

## Tool
`clip_3d_schema_map.py`

SHA-256:
`8786c624b4cf30e15cc6ba16f7ca96e61ed90329d0e4a19c54b14e68f75b47bd`

The tool extracts `CHNKSQLi`, reads `ParamScheme`, maps data type codes 1/2/3/4 to INTEGER/REAL/TEXT/BLOB, and reports active vs latent 3D-related schemas.
