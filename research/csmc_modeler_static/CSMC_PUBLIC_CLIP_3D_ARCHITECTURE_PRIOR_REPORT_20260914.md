# CSMC public `.clip` 3D architecture prior — 2026-09-14

Status: `PUBLIC_PRIOR_NOT_CSMC_PROOF`

This is a deliberately separate evidence lane from the preregistered blind MODELER field-read search. It records public `.clip` ecosystem architecture that may later corroborate an independently discovered MODELER data-flow edge. It must not retroactively guide or score the blind preregistration, and it is not proof that `.csmc` uses the same structures.

## Public sources reviewed

### Aodaruma/clipfile-rs

Pinned commit: `bd88467fa80e63ad48c6c713fbfb5a8a116d798a`.
License: MIT.

Its public format-analysis report says it compared five local `.clip` files read-only and then revalidated with anonymous minimal-difference files. For the outer external-data index it reports 5,889 `ExternalChunk` rows, unique IDs, and zero offset mismatches against the physical `CHNKExta` positions.

The same report says `ExternalTableAndColumnName` declared, among others:

- `Canvas3DModelBank.BankData`
- `Canvas3DModelLoader.ModelData`
- `Manager3DOd.SceneData`
- `ModelData3D.Layer3DModelData`

It explicitly warns that some declared tables are absent from individual sample databases, so a fixed table set must not be assumed.

### youichi-uda/clip-clai

Pinned commit: `76edfbf393868687107c2cdfdb750a70ca9ba7fe`.
License: MIT.

Its public `.clip` format document independently records `Canvas.Canvas3DModelDataLoaderIndex` and the same four 3D-related external columns listed above. It also describes the generic `ExternalChunk.ExternalID -> ExternalChunk.Offset -> CHNKExta` indirection pattern for external payloads.

The document states that it combines community reverse engineering with real-file analysis. Therefore agreement with other public projects is corroboration, but it is not treated as statistically independent experimental replication.

### LavenderSnek/clipdecode

Pinned commit: `e5347a65202bc399bdd730d13187bc32aabdd4fa`.
License: LGPL-2.1.

Its incomplete public spec separately states that `ExternalTableAndColumnName` lists table/column locations that contain external chunk IDs and that `ExternalChunk` provides the offsets for those chunks. It does not provide the same 3D-specific list, so it is used only as generic external-indirection corroboration.

## New information admitted

For `.clip`, there is now a public, multi-source architecture prior that 3D-related payloads can be externalized through a generic external-ID / offset indirection layer instead of being assumed inline in one SQLite record.

The strongest public names are:

- `ExternalChunk`
- `ExternalTableAndColumnName`
- `Canvas3DModelBank` / `BankData`
- `Canvas3DModelLoader` / `ModelData`
- `ModelData3D` / `Layer3DModelData`
- `Manager3DOd` / `SceneData`
- `Canvas3DModelDataLoaderIndex`

Classification: `STRONG_PUBLIC_ARCHITECTURE_PRIOR_NOT_CSMC_PROOF`.

## What this does *not* prove

The controlled CSMC fixtures currently use a SQLite database with one `character` row whose BLOB has a `CLIP_STUDIO_3D_DATA2` envelope. That is structurally different from the public `.clip` container architecture described above.

Therefore none of the following are promoted:

- `.csmc` has `ExternalChunk` or `ExternalTableAndColumnName` tables;
- `.csmc` contains `Canvas3DModelLoader`, `ModelData3D`, or the other public table names;
- the CSMC 2456-byte cadence is a `.clip` external chunk;
- any CSMC prefix bytes are vertex, index, material, UV, bone, or weight data;
- a string or RTTI hit for a public name inside MODELER would by itself prove a consumer edge.

No `.clip` outer-container rule is transferred to `.csmc`.

## Interaction with the blind static lane

The existing blind preregistration asks which direct input-read primitive consumes the bounded F02 DATA2 variable prefix, without semantic labels and without oracle results. That preregistration remains sealed and unchanged.

Public names from this report are **not allowed to guide the blind pass**. They may be used only after a blind result is sealed, as non-proof corroboration. A future CONFIRMED claim must still satisfy the v2 static evidence validator: direct edge kind, provenance-bound address, width/endian/count-or-length source, destination/downstream data flow, and negative control as applicable.

If the blind pass independently reaches an external-ID, model-data, or scene-data path, agreement with this public prior would become useful cross-evidence. If the blind pass reaches a completely different path, this public prior must not be used to force the result back toward these names.

## Search-space consequence

This report creates one new independent *architectural constraint axis*, but not a new semantic field binding:

- high-value post-blind question: does MODELER 1.10.13 contain a direct data-flow bridge from CSMC `DATA2` input toward an externalized model/scene-data abstraction?
- low-value/rejected shortcut: search public 3D names and infer that nearby code parses the bounded F02 prefix.

The safe sequence is therefore:

1. keep the blind F02 direct-read/data-flow pass unchanged;
2. seal its result;
3. only then compare any discovered consumer path with the public `.clip` architecture prior;
4. require the existing proof-grade validator before closing `EXPLICIT_SERIALIZER_FIELD_READ`, `EXPLICIT_MODELDATA_LOOKUP`, `EXPLICIT_CANVAS3D_LOAD_ENTRY`, or `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`.

## Isolation

- MODELER process execution: 0
- MODELER process mutation: 0
- Save / Save As / Ctrl+S: 0
- runtime / Worker / Canary / Control Gate: 0
- mainline mutation: 0
- RIO-26 mutation: 0
- semantic promotion: 0
- Blender emit: BLOCKED
- raw private CSMC bytes published: false
- raw proprietary MODELER bytes published: false

This lane is research guidance only.
