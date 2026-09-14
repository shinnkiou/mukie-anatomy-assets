# CSMC MODELER Full Snapshot Reconciliation v1 — 2026-09-14

## Verdict

The delivered full static snapshot is a **new admissible private MODELER static-analysis artifact**.
Its MODELER executable SHA-256 exactly matches the V2 evidence contract identity.

- snapshot ZIP SHA-256: `afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342`
- MODELER EXE SHA-256: `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`
- extractor SHA-256: `f5ad7813efbbc6be4879eaf59fcc02e1ae33623b338e4015bc28f93357bc70cd`
- files: 196
- uncompressed total: 79,493,525 bytes
- fresh disposable Ghidra project: yes
- MODELER runtime started: no
- semantic promotion: no
- raw/private snapshot publication: no

## Evidence reconciliation

| Evidence class | New state | Proof-grade | Why |
|---|---|---:|---|
| EXPLICIT_CSMC_HANDLER_ENTRY | UNRESOLVED | no | No direct `.csmc` handler/dispatch edge is bound. |
| EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP | **CONFIRMED** | **yes** | `0x140d175d0` contains an explicit `ExternalChunk.Offset` lookup keyed by ExternalID; caller `0x1416578e0`. |
| EXPLICIT_MODELDATA_LOOKUP | **CONFIRMED** | **yes** | `0x140d45d30` explicitly binds `ModelData` to `Canvas3DModelLoader` through registration helper `0x141657140`. |
| EXPLICIT_CANVAS3D_LOAD_ENTRY | CANDIDATE | no | Loader RTTI/vftable and registry binding exist, but a concrete loader method invocation is not yet bound. |
| EXPLICIT_SERIALIZER_FIELD_READ | **UNRESOLVED** | no | Generic direct read primitive `0x1408c27c0` is concrete, but no F02-specific serializer read with width/endian/count/destination/data-flow has been proven. |
| EXPLICIT_INTERNAL_MODEL_CONSTRUCTION | CANDIDATE | no | `ODCImporterT<GADCharacter>` and many GADCharacter chunk importer types are present, but direct construction flow is not yet bound. |
| CONTROLLED_FIXTURE_TO_CONSUMER_MATCH | **UNRESOLVED** | no | No same-identity F02 fixture has been linked into the concrete consumer path. |

New proof-grade consumer edges: **2**.

The requested `EXPLICIT_SERIALIZER_FIELD_READ` edge is **not closed**.

## Direct static facts

### ModelData registry

At function `0x140d45d30`, the snapshot binds the `ModelData` key to `Canvas3DModelLoader`
and passes that pair to registration helper `0x141657140`.

Negative control: the same function independently binds `BankData` to
`Canvas3DModelBank` and `Layer3DModelData` to `ModelData3D`. This is therefore an
explicit pair, not global string proximity.

### ExternalChunk lookup

`0x140d175d0` has the exact `ExternalChunk.Offset` lookup by `ExternalID`.
The exact SELECT lookup occurs in that function, while CREATE/DELETE/INSERT operations
are located in separate functions.

Container code also provides a concrete direct byte-read primitive at `0x1408c27c0`
and explicit `CSFCHUNK` / `CHNKHead` / `CHNKExta` framing checks.

## F02 frozen questions

All five remain unresolved:

- Q-BND-01 — unresolved
- Q-BND-02 — unresolved
- Q-INV-01 — unresolved
- Q-PFX-01 — unresolved
- Q-TERM-01 — unresolved

The full snapshot proves more of the **architecture**, but does not yet tie the F02
payload-relative boundaries 3215/3216/3217, invariant offsets, prefix partitioning,
or 17687/17688 termination to an instruction-level consumer path.

## Public `.clip` prior reconciliation

Because the blind questions were frozen before this snapshot arrived, the public `.clip`
prior may now be used as **post-blind architecture corroboration only**.

It independently agrees on:

- `ExternalChunk.Offset`
- `Canvas3DModelLoader.ModelData`

This corroboration does not transfer `.clip` semantics to CSMC and does not promote
geometry/index/material/UV/bone/weight semantics.

## Project gates

Unchanged:

- MAINLINE = ACTIVE
- STRUCTURAL DEVELOPMENT = ACTIVE
- semantic gate = CLOSED
- semantic promotion = 0
- Blender emit = BLOCKED
- runtime dispatch = false
- physical oracle = 0/30 PENDING_MANUAL_ORACLE
- broad blind semantic expansion = BLOCKED

The next justified static work is **targeted direct-flow tracing** from the newly confirmed
ExternalChunk/ModelData architecture toward serializer/internal-model consumers. It is not
a new blind hypothesis family.
