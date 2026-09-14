# CSMC public `.clip` 3D architecture prior v2 — 2026-09-14

Status: `PUBLIC_PRIOR_V2_NOT_CSMC_PROOF`

This v2 strengthens the public architecture lane with two explicit negative controls: schema/name presence is not instance/data presence, and matching names from a dependent parser are not independent replication. The sealed F02 blind MODELER field-read preregistration remains unchanged.

## Pinned public sources

- `Aodaruma/clipfile-rs` @ `bd88467fa80e63ad48c6c713fbfb5a8a116d798a` — MIT. Its public read-only format analysis reports 5,889 `ExternalChunk` rows and zero physical-offset mismatches across its stated corpus, and lists the 3D-related external columns `Canvas3DModelBank.BankData`, `Canvas3DModelLoader.ModelData`, `Manager3DOd.SceneData`, and `ModelData3D.Layer3DModelData`.
- `youichi-uda/clip-clai` @ `76edfbf393868687107c2cdfdb750a70ca9ba7fe` — MIT. Its public format document records the same 3D external columns plus `Canvas.Canvas3DModelDataLoaderIndex` and the generic external-ID → `ExternalChunk.Offset` → external payload chain.
- `LavenderSnek/clipdecode` @ `e5347a65202bc399bdd730d13187bc32aabdd4fa` — LGPL-2.1. Its public incomplete spec independently documents the generic `ExternalTableAndColumnName` / `ExternalChunk` indirection architecture.
- `wamsoft/clipparse` @ `322a273c0e059d1dee9132af78289efa12a59522` — MIT. Its report explicitly states an independent re-derivation against four files, walking 164,562 block sub-records. Its measured `test000.clip` external declaration list contains the same four 3D-related table/column names.
- `al3ks1s/clip-tools` @ `e1d3d7ed4701ac84e9220127daa73c2cf90dd803` — MIT. Its typed schema view exposes `Canvas.Canvas3DModelDataLoaderIndex`, `Canvas3DModelLoader` fields (`BankId`, `ModelData`, `ModelUuid`, `ModelType`, `NextIndex`), `Canvas3DModelBank` fields (`BankId`, `BankData`, `FirstLoaderIndex`), `CanvasItemBank.ModelBankMainIndex`, and `ModelData3D.Layer3DModelData`. Its README also credits `clip-to-psd` for much parsing information and logic, so this source is dependency-tagged and is not counted as independent replication.

## Structural prior refined

For `.clip`, public evidence supports an architecture in which external payload references are mapped through `ExternalTableAndColumnName` and `ExternalChunk`, and the schema has explicit 3D model/bank/loader/scene fields. The typed view further suggests a bank/loader organization with `FirstLoaderIndex` / `NextIndex` and a `CanvasItemBank.ModelBankMainIndex` reference.

This is a **public schema/architecture prior only**. It does not prove the same relationship exists in `.csmc` or in MODELER 1.10.13's consumer path.

## Negative control 1 — declaration/name presence is not instance presence

`wamsoft/clipparse` reports for `test000.clip`:

- 10 `ExternalTableAndColumnName` declarations;
- 9 of the referenced tables are absent in that concrete file.

Therefore a declaration or semantic-looking name can describe format capability without proving that a specific file contains that table, payload, or live data path.

This directly strengthens the CSMC static-analysis firewall: a string, RTTI label, schema name, or public-name match cannot close `EXPLICIT_MODELDATA_LOOKUP`, `EXPLICIT_CANVAS3D_LOAD_ENTRY`, `EXPLICIT_SERIALIZER_FIELD_READ`, or `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH` without a direct provenance-bound edge/data-flow bridge.

## Negative control 2 — matching typed names are not independent replication

`al3ks1s/clip-tools` exposes detailed typed 3D schema fields, but its README credits `clip-to-psd` for much parsing information and logic and `cliputils` for file splitting. Matching names are useful corroboration but do not increase the count of independent experiments.

V2 therefore sets `independence_not_assumed=true` and records source roles explicitly.

## CSMC non-transfer boundary

The controlled CSMC corpus remains SQLite `character.character` with a `CLIP_STUDIO_3D_DATA2` envelope. No public GitHub source found in this pass contained the exact `CLIP_STUDIO_3D_DATA2` or `CLIP_STUDIO_3D_DATA` string.

Do not infer:

- `.csmc` has `ExternalChunk` or the public `.clip` 3D tables;
- `.csmc` uses `FirstLoaderIndex` / `NextIndex` bank chains;
- the CSMC 2456-byte cadence is an external payload unit;
- any CSMC prefix field is geometry/topology/material/UV/bone/weight data;
- a MODELER public-name hit is a direct consumer read.

## Blind/post-blind protocol

1. Preserve the existing blind F02 direct-read/data-flow target exactly as preregistered.
2. Seal the blind result before consulting public 3D names.
3. Use v2 public names only as post-blind non-proof corroboration.
4. If the sealed blind route independently reaches an external/model/bank/scene abstraction, require the v2 static evidence validator before any confirmed edge claim.
5. Treat a name/schema match with no direct edge as candidate-only even if multiple public projects use the same name.

## Current impact

Classification remains:
`STRONG_PUBLIC_ARCHITECTURE_PRIOR_NOT_CSMC_PROOF`

The improvement in v2 is epistemic quality, not semantic confidence: public source dependency and declaration-vs-instance confounders are now explicit machine-checked negative controls.

Unchanged:
- `STRUCTURAL_ONLY`
- semantic promotion = 0
- Blender emit = BLOCKED
- runtime dispatch = false
- physical F02 oracle = 0/30
- `EXPLICIT_SERIALIZER_FIELD_READ` = UNRESOLVED
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH` = UNRESOLVED
- mainline / RIO-26 / MODELER runtime / Worker / Canary / Control Gate mutation = 0
