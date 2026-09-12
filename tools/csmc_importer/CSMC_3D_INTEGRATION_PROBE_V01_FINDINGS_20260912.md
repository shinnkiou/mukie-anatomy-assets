# CSMC 3D Integration Probe v0.1 — Findings — 2026-09-12

## Status

`SYNTHETIC_REFERENCE_GRAPH_PASS`

This is a public-safe checkpoint. It contains no purchased model bytes, extracted mesh/texture data, private runtime captures, credentials, or DRM/auth material.

## What was added

`tools/csmc_importer/csmc_3d_integration_probe.py` is a read-only integration probe for the P0/P1/P2 CSMC research sequence.

The probe:

- parses CLIP `CSFCHUNK` and indexes every `CHNKExta` payload by external ID, offset, size, SHA-256, and optional `CLIP_STUDIO_3D_DATA2` metadata;
- extracts `CHNKSQLi` and distinguishes registered schema from live SQL tables/rows;
- snapshots live/present state for `Canvas3DModelLoader`, `Manager3DOd`, `ModelData3D`, `Canvas3DModelBank`, `ModelInfo3D`, `ModelNodeInfo3D`, `CharacterInfo`, `CameraInfo`, `LayerObject`, `CanvasItem`, and `Canvas`;
- resolves the major external 3D routes:
  - `Canvas3DModelLoader.ModelData`
  - `Manager3DOd.SceneData`
  - `ModelData3D.Layer3DModelData`
  - `Canvas3DModelBank.BankData`
- records `ModelInfo3D` fields relevant to `ModelNodeInfoCount`, `ModelNodeInfoFirstIndex`, `DessindollShapeInfo`, `DessindollBoneInfo`, and Parts BLOBs when live;
- records `ModelNodeInfo3D` node name, rotation, translation, scale, and `NextIndex` fields when live;
- summarizes BLOBs by length/hash rather than publishing payload bytes;
- optionally compares a saved CSMC/CS3C character BLOB against resolved CLIP external payload metadata;
- emits six bounded artifacts:
  - `CSMC_3D_INTEGRATION_REPORT.json`
  - `CSMC_3D_REFERENCE_GRAPH.json`
  - `CSMC_EXTERNAL_PAYLOAD_INDEX.json`
  - `CSMC_SQLITE_3D_TABLES.json`
  - `CSMC_BINARY_REGION_MAP.json`
  - `CSMC_PROBE_REPORT.md`

## Synthetic validation

A synthetic CLIP fixture with four external references was generated entirely from public-safe test data.

Expected and observed:

- external payloads: 4
- reference edges: 4
- resolved references: 4
- unresolved references: 0
- live `ModelInfo3D`: present
- live `ModelNodeInfo3D`: 1 row
- node name roundtrip: `BP3D_TEST_ROOT`
- six expected output artifacts: produced

Synthetic CLIP SHA-256:

`8a76e5e02552f1f573933cf6216aad2d40285fd34239ad8a2711866c6600e7f7`

## GitHub evidence

- probe commit: `833fec1be4ac232293b644a8ee836b9093950593`
- synthetic test commit: `33ba17e889bf71d549e2a9af3cde8de6c73b947a`
- CI integration commit: `4660281f42dcf4bf48c33384da476785f52bfb56`
- GitHub Actions run: `34675428296`
- workflow: `CSMC importer smoke`
- conclusion: `success`

## Interpretation boundary

This checkpoint proves the integration scanner and reference-graph machinery, not CSMC geometry semantics.

It does **not** prove vertex positions, index buffers, UVs, materials, textures, bone hierarchy encoding, bind pose, bone indices, or skin weights.

Schema registration is never treated as live usage. The evidence levels remain separate:

1. schema registered;
2. SQL table exists;
3. row exists;
4. target row/column contains an external reference;
5. that external reference resolves to an actual `CHNKExta` payload.

## Runtime-GUID correction

An older checkpoint described the target GUID as a useful dynamic runtime anchor. Later Observer v0.5.4 cross-session work showed the known GUID hits were in `MEM_IMAGE` and unchanged across variants, consistent with static executable constants. GUID presence by itself is therefore no longer accepted as dynamic character-payload evidence.

An earlier one-state observation of a structured serialized-looking header remains historical evidence, but it must not be generalized into a persistent runtime-BLOB claim without a fresh reproducible capture.

## Next gate

Run this exact probe against the authorized target `.clip` and, where available, the matching saved CSMC. The first real-data success condition is a complete P1/P2 reference graph showing which 3D tables/rows are live and which external IDs resolve to which `CLIP_STUDIO_3D_DATA2` payloads.

Only after that result should controlled one-variable teacher pairs or a narrow runtime/x64dbg validation be selected.
