# CSMC real target P1/P2 + P4 checkpoint — 2026-09-12

Status: `REAL_P1_P2_COMPLETE__P4_GATE_OPEN`

This checkpoint records metadata/statistical findings only. It does **not** contain purchased `.clip` / `.csmc` bytes, extracted mesh/texture data, credentials, or any bypass material.

## Exact authorized input identity

Fresh Evidence Probe v0.2 was run against the exact authorized target `.clip`:

- size: `56,996,715` bytes
- SHA-256: `ed391b6fef0f425165f6dd4719ec9000966742efde5428cb2c1446f63640e933`
- identity gate: **MATCH**

Matching comparison CSMC:

- size: `77,168,640` bytes
- SHA-256: `388726bd12a433f36ced922077d80cf8ed3f18e543d0106d844715185b77528c`
- CELSYS kind: `character`
- character BLOB size: `77,081,873`
- character BLOB SHA-256: `5a67b18b645840ee27d358e02ab6acdde001bc8faa301bdde97365c28831c605`

The source files were read only and are not committed here.

## Fresh P1/P2 classification

### Already-resolved routes remain confirmed

1. `Canvas3DModelLoader.ModelData`
   - state: `LIVE_ROWS`
   - row count: `1`
   - resolves to CELSYS `catalog_character`
   - BLOB size: `55,784,641`
   - BLOB SHA-256: `e154dd913e9f8cd4d3a1f1f05def9fedfc671e47b5f3cee5027bfc9b5cd52d30`

2. `Manager3DOd.SceneData`
   - state: `LIVE_ROWS`
   - row count: `1`
   - resolves to CELSYS `scene`
   - BLOB size: `11,781`
   - BLOB SHA-256: `8f393e1c6beb7f9b6cccaab9aeb51f64fc183ce75eb84b0f416d27a4f471d7fc`

### Formerly unresolved route A

`ModelData3D.Layer3DModelData`

- `ModelData3D` is registered in `ParamScheme`
- physical SQL table: **absent**
- row count: `0`
- classification: **`SCHEMA_ONLY`**
- `Layer3DModelData` therefore has no live value and no resolvable external reference in this target

Conclusion: **no live Layer3DModelData route exists in this document.**

### Formerly unresolved route B

`Canvas3DModelBank.BankData`

- `Canvas3DModelBank` physical table: **present**
- row count: `1`
- state: **`LIVE_ROWS`**
- `BankData` is registered in `ParamScheme`
- actual physical columns are only:
  - `_PW_ID`
  - `MainId`
  - `BankId`
  - `FirstLoaderIndex`
- `BankData` physical column: **absent**
- row value: `FirstLoaderIndex = 1`

`FirstLoaderIndex = 1` points to the existing `Canvas3DModelLoader` row that carries the already-known `ModelData -> catalog_character` route.

Conclusion: **BankData is not an independent live payload route in this target.**

### Other schema-only families

- `ModelInfo3D`: `SCHEMA_ONLY`
- `ModelNodeInfo3D`: `SCHEMA_ONLY`

No live node-chain claim is made.

## P1/P2 decision

Fresh P1/P2 is now complete for the exact target. The two candidate routes that had remained unresolved do not expose another independent CELSYS 3D payload.

Therefore the documented gate condition is satisfied:

`P4_GATE = OPEN`

This does **not** mean geometry is recovered. It means broad file-route discovery is exhausted enough to move to a narrow serializer/runtime trace anchored on the known real payload boundary.

## P4 static opaque-block anchor map

The saved CSMC `character` and `.clip` `catalog_character` payloads both obey the established 8-byte stored-size invariant but are not byte copies.

Exact 8-byte block comparison on the stored payload regions:

- `.clip catalog_character`: `6,973,071` blocks; `6,815,164` unique
- saved CSMC `character`: `9,635,226` blocks; `8,341,353` unique
- shared unique 8-byte values: **`5,183`**
- shared occurrences in `.clip`: **`31,603`** (`0.4532%`)
- shared occurrences in CSMC: **`39,479`** (`0.4097%`)
- common values occurring exactly once in each payload: **`2,558`**

Strong unique-anchor displacement modes include:

- `+197` blocks = `+1,576` bytes: `685` unique-once anchors
- `+965` blocks = `+7,720` bytes: `476` unique-once anchors
- `+195` blocks = `+1,560` bytes: `187` unique-once anchors
- `+4,693,615` blocks = `+37,548,920` bytes: `30` unique-once anchors

Direct equality checks at high-frequency displacement modes also found exact consecutive opaque-block runs, including runs on the order of `1.4–1.8 KiB` and a separate moved region tens of MiB away.

Interpretation boundary: these are structural fingerprints only. They do **not** identify a cipher/transform/compressor, and they do not establish that any block is a vertex, index, UV, bone, weight, material, or texture record.

## New narrow P4 hypothesis

Do not return to generic GUID scanning.

Use the exact `character` / `catalog_character` read/decode path as the anchor and trace toward the first geometry-bearing object or buffer. The shifted exact 8-byte runs provide reproducible structural landmarks for validating that a candidate decoder path is consuming the expected CELSYS payload rather than unrelated executable constants.

First acceptable P4 success remains one of:

- concrete vertex count / index count,
- reproducible XYZ buffer,
- reproducible triangle/index buffer,
- vertex-buffer creation tied to the authorized target,
- or a target-specific static mesh extraction path.

Rig/weights do not block first static-mesh recovery.
