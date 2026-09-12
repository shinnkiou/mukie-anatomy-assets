# CSMC P1/P2 target evidence consolidation

Status: `TARGET_METADATA_EVIDENCE_CONSOLIDATED_P2_PARTIAL`

This report consolidates already-verified, public-safe metadata about the authorized target character. It does not contain purchased model bytes, extracted mesh/texture data, credentials, or license-bypass material.

## Target `.clip`

- File: `デッサン人形(女性160)クリップfile.clip`
- Size: `56,996,715` bytes
- SHA-256: `ed391b6fef0f425165f6dd4719ec9000966742efde5428cb2c1446f63640e933`
- Container: `CSFCHUNK`
- `CHNKSQLi` present

### Live external route 1 — character model

`Canvas3DModelLoader.ModelData`

- model UUID: `b899c059-2dd9-4da3-9758-e478e8ea7da3`
- external ref: `extrnlid984A4D1BFA5A4E098C2B1CFA44526B9B`
- external chunk offset: `3500`
- external blob size: `55,784,641`
- CELSYS magic: `CLIP_STUDIO_3D_DATA2`
- kind: `catalog_character`
- GUID: `379b70c91e544437affc00c71d52f53c`
- inner version: `2`
- logical size: `55,784,555`
- stored size: `55,784,568`
- payload offset: `73`

### Live external route 2 — scene

`Manager3DOd.SceneData`

- external ref: `extrnlid5F981AE3EE18413EA9577240E29CC242`
- external chunk offset: `55,809,278`
- external blob size: `11,781`
- CELSYS magic: `CLIP_STUDIO_3D_DATA2`
- kind: `scene`
- GUID: `276361c385924c868c8141224d27d1c8`
- inner version: `2`
- logical size: `11,709`
- stored size: `11,720`
- payload offset: `61`

## P1 — live vs schema-only status

The target document's SQLite does **not** instantiate live `Manager3D`, `ModelInfo3D`, or `ModelNodeInfo3D` tables. Their semantic definitions survive in `ParamScheme` and must therefore be treated as a schema dictionary, not as live row evidence.

High-value schema-only relationships include:

- `ModelInfo3D.ModelNodeInfoFirstIndex -> ModelNodeInfo3D`
- `ModelInfo3D.ModelNodeInfoCount`
- `ModelNodeInfo3D.NextIndex`
- `NodeName`
- `NodeRotationR / NodeRotationVX / NodeRotationVY / NodeRotationVZ`
- `NodeTranslationX / Y / Z`
- `NodeScaleX / Y / Z`
- `DessindollShapeInfo`
- `DessindollBoneInfo`
- `PartsBody / PartsMaterial / PartsLayout / PartsTransform`

This is consistent with the current active route being `Manager3DOd.SceneData` plus CELSYS `scene` serialization rather than live legacy `ModelInfo3D` / `ModelNodeInfo3D` rows.

## P2 — source and `.clip` serialization relation

The original CS3C `catalog_character` and the `.clip` embedded `catalog_character` preserve the same:

- magic
- kind
- GUID `379b70c91e544437affc00c71d52f53c`
- inner version `2`
- payload offset `73`

but they are not byte copies.

Original CS3C:

- blob size `39,485,161`
- logical size `39,485,076`
- stored size `39,485,088`

`.clip` embedded `catalog_character`:

- blob size `55,784,641`
- logical size `55,784,555`
- stored size `55,784,568`

Delta:

- blob/stored: `+16,299,480`
- logical: `+16,299,479`
- aligned 8-byte equal fraction across common length: about `0.000047`

Therefore PAINT's `.clip` representation is a reserialized/augmented payload with the same catalog-character identity, not a direct copy of the source CS3C payload.

The MODELER-saved CSMC is another serialization surface:

- file SHA-256: `388726bd12a433f36ced922077d80cf8ed3f18e543d0106d844715185b77528c`
- inner kind: `character`
- GUID: `19c1747bf2b84da197b9ead412256c5b`
- inner version: `2`
- logical size: `77,081,794`
- stored size: `77,081,808`

Do not equate the CSMC `character` GUID with the CS3C/`.clip` `catalog_character` GUID; they are distinct serialization surfaces.

## Runtime correction

An earlier one-state capture appeared to contain a serialized-looking `character` header in private writable MODELER memory. Later cross-session Observer v0.5.4 checks found the known GUID hits in `MEM_IMAGE`, unchanged across body variants, consistent with static executable constants. Therefore GUID presence alone is no longer valid dynamic payload evidence. The earlier one-state header observation remains historical until independently reproduced.

## Current gate

Evidence Probe v0.2 now enforces the required distinction between:

- schema registered only
- SQL table present but empty
- live rows
- absent

and follows `ModelInfo3D -> ModelNodeInfo3D` only when numeric indexes exactly match live `_PW_ID` values.

P2 is still **partial**. Existing target evidence resolves `Canvas3DModelLoader.ModelData` and `Manager3DOd.SceneData`. A fresh target run is still required to explicitly classify and, if live, resolve:

- `ModelData3D.Layer3DModelData`
- `Canvas3DModelBank.BankData`

Only after that should broad runtime/decompiler tracing become the mainline again.
