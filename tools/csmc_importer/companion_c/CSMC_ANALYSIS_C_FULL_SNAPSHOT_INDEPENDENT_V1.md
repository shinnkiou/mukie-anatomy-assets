# CSMC ANALYSIS COMPANION C — FULL STATIC SNAPSHOT INDEPENDENT DEEP PASS V1

- Run: **C-069**
- Date: 2026-09-14T23:16:18+09:00
- Status: **READY_FOR_CROSS_LANE_COMPARE**
- Classification: `FULL_SNAPSHOT_DIRECT_CHUNK_SQLITE_CONSUMER_CHAIN_CONFIRMED_SEMANTICS_UNPROMOTED`
- Pipeline: `STRUCTURAL_ONLY`
- Semantic promotion: **0**
- Blender emit: **BLOCKED**
- MODELER runtime actions: **0**
- Mainline mutation / RIO-26 mutation / Worker / Canary: **0**

## Independence boundary

This report was produced from the user-supplied Full Static Snapshot plus **pre-C-069** frozen context only. Companion C did **not** read Mainline's new Full Snapshot result before sealing this report. The only cross-lane artifact used beyond the snapshot itself was the already-existing F02 structural map (`1ylpWtRvGUVP2AHcelhZay7uH73Yo6GAL`), whose canonical Sentinel-9 remains unchanged.

## PROVENANCE

- Snapshot: `CSMC_FULL_SNAPSHOT_20260914_214659.zip`
- Snapshot SHA-256: `afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342`
- Target: CLIP STUDIO MODELER 1.10.13
- Target EXE SHA-256: `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`
- Ghidra: 12.1.3
- Extractor SHA-256: `f5ad7813efbbc6be4879eaf59fcc02e1ae33623b338e4015bc28f93357bc70cd`
- fresh disposable project: true
- original Ghidra project used: false
- MODELER runtime started: false
- private output: true
- inventory listed: 195
- inventory verified: 195
- missing: 0
- bad hash: 0
- summary function count: 76,803
- direct call edges: 267,088
- strings: 29,883
- string xrefs: 34,232
- symbols: 669,282
- target keyword hits: 1,715
- targeted decompiles: 180

The Full Snapshot is therefore admitted as a new independent static-evidence input. Raw private binary/payload bytes are not reproduced in this report.

## DIRECT CONSUMER EDGES

### EDGE-C069-01 — CONFIRMED direct call

`0x141657970 -> 0x140d15a90`

This is a direct edge in `call_edges.tsv`. `0x140d15a90` is also targeted-decompiled, so this is not a string-only relationship.

### EDGE-C069-02 — CONFIRMED chunk / reader / SQLite chain inside 0x140d15a90

Within one decompiled routine, the following operations are connected:

1. bounded 8-byte input read;
2. marker validation against the `CSFCHUNK / CHNKExta / CHNKSQLi` family;
3. repeated calls to the already-confirmed BE-u64 reader `0x1408c2d90 -> 0x1408c26e0`;
4. length-driven cursor advance through `0x1408c2dc0`;
5. a 16-byte bounded read after a required length value of `0x10`;
6. recognition of `CHNKSQLi`;
7. bounded input-to-output block transfer using `0x1408c27c0` and `0x1408c17d0`;
8. creation and clearing of SQLite table `ExternalChunk(ExternalID BLOB, Offset INTEGER)` through `0x140d1de70`.

This is the key C-069 trigger: it advances beyond the FIRST PASS parent-record/length boundary into a direct consumer-side chunk-to-SQLite chain.

### EDGE-C069-03 — CONFIRMED registration edge

`0x140d45d30` directly registers pairs through `0x141657140`, and `0x141657140 -> 0x141656a80` is direct. Relevant pairs include:

- `ModelData -> Canvas3DModelLoader`
- `BankData -> Canvas3DModelBank`
- `SceneData -> Manager3DOd`
- `Layer3DModelData -> ModelData3D`

This confirms registration, **not** a later lookup/load invocation.

## CALL FLOW

Current independently supported graph:

`0x141657970`
→ `0x140d15a90`
→ marker reads/checks (`CSFCHUNK`, `CHNKExta`, `CHNKSQLi`)
→ confirmed BE-u64 reads / bounded byte reads / cursor skips
→ CHNKSQLi bounded transfer
→ SQLite `ExternalChunk` table create/delete.

Sibling ExternalChunk island:

- `0x141657e60 -> 0x140d15700` — xref to `INSERT INTO ExternalChunk VALUES('%s',%s)`
- `0x1416578e0 -> 0x140d175d0` — xref to `SELECT Offset FROM ExternalChunk WHERE ExternalID='%s'`
- `0x141657540 -> 0x140d17e20` — second INSERT-side function

These sibling functions are high-value **CANDIDATE** paths because their bodies were not among the targeted decompiles. The SELECT-result-to-seek edge remains unproved.

The desired full path `.csmc dispatch -> ExternalChunk -> ModelData -> Canvas3DModelLoader -> serializer -> construction` is therefore **not yet closed**.

## READER FAMILIES

| Primitive | Level | Independent interpretation |
|---|---|---|
| `0x1408c2d90 -> 0x1408c26e0` | CONFIRMED | BE-u64 reader; prior FIRST PASS primitive directly reused by new chunk consumers |
| `0x1408c1960 -> 0x1408c1650` | CONFIRMED | BE-u64 writer; present in ExternalChunk INSERT-side functions |
| `0x1408c27c0` | STRONG | bounded byte read/copy `(cursor,dst,count)` |
| `0x1408c2dc0` | STRONG | cursor advance/skip by a read length |
| `0x1408c2f40` | STRONG | bounded marker compare/check |
| `0x1408c0d40` | CONFIRMED | resize/reserve/copy-on-write buffer growth; returns inline/heap data base |
| `0x1408c17d0` | STRONG | output write/copy in CHNKSQLi transfer loop |
| `0x1408c2db0` | CANDIDATE | availability/remaining-length query; exact role not decompiled |

Reader catalog **does not equal CSMC binding**. In particular, no direct F02 `CLIP_STUDIO_3D_DATA2` -> these readers edge is established.

## SQLITE / CHUNK RELATED FLOWS

Direct string xrefs localize a narrow ExternalChunk island:

- CREATE + DELETE: `0x140d15a90`, `0x140d18650`
- INSERT: `0x140d15700`, `0x140d17e20`
- SELECT Offset by ExternalID: `0x140d175d0`
- combined CSFCHUNK/CHNKExta/CHNKSQLi marker family: `0x140d15a90`, `0x140d16ae0`, `0x140d16eb0`

`EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP` remains **CANDIDATE**, not CONFIRMED, because the SELECT result's downstream seek/destination is not present as body-level proof in the snapshot.

## DESTINATION / CONSTRUCTION EDGES

Construction-side source-path xrefs identify 15 candidate functions under:

- `CrMVertex.cpp` — 12 functions
- `CrMDocObjBone.cpp` — 2 functions
- `CrMDocObjUV.cpp` — 1 function

A directed search of exported `call_edges.tsv` found **0 direct paths** from the chunk/SQLite callers/functions or the ModelData-registration island to those 15 construction functions.

Interpretation: `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION = UNRESOLVED`. This blocks semantic promotion. It is **not** a proof that the paths are unrelated because virtual/function-pointer dispatch may be missing from a direct call graph.

## SERIALIZER RTTI / CLASS RELATIONSHIPS

The snapshot contains typed `ODCChunkCellImporterT` specializations, including:

- `ODDPresetVertexArray`: Coordinate `0x1417e9468`, Normal `0x1417e94c0`, UV `0x1417e94e0`, NextLinkIndex `0x1417e9500`
- `ODDEditPresetHalfEdge`: VertexIndex `0x1417e48f8`, PointIndex `0x1417e4950`, LineIndex `0x1417e4970`, FaceIndex `0x1417e4990`, PairID `0x1417e49e8`, PostID `0x1417e4a40`
- `ODDPresetSkin`: BoneName `0x1417e8a60`, MeshName `0x1417e8ab8`, WeightInfo `0x1417e8ad8`, BindMatrix `0x1417e8af8`
- `ODDPresetMesh`: VertexArray `0x1417e7fc8`, FaceArray `0x1417e8020`, MaterialData `0x1417e8078` plus Name/NodeName/Location
- `ODDFaceData`: VertexIndex `0x1417eaff0`

All are **CANDIDATE** only. RTTI/vtable specialization demonstrates that typed serializer/importer classes exist; it does not establish the actual read primitive, field width, count/length, destination, CSMC reachability, or geometry semantics.

## COMPETING HYPOTHESES

### H-CHNKSQLI-AUTH

**A:** CHNKSQLi is the embedded SQLite index/database carrying the authoritative ExternalChunk map.  
**B:** CHNKSQLi is an auxiliary cache/staging DB.

Supports A: direct CHNKSQLi bounded transfer, ExternalChunk CREATE/DELETE, sibling INSERT/SELECT xrefs.  
Supports B: no `.csmc` dispatch or ModelData load bridge is proved.

Kill A: prove SELECT Offset never controls a payload seek/read.  
Kill B: prove `0x140d175d0` SELECT result directly controls cursor/CHNKExta payload positioning.

### H-KEY-EXTERNALID

**A:** CHNKExta key is SQLite ExternalID.  
**B:** key and ExternalID are distinct/derived independently.

Kill A: INSERT body sources ExternalID elsewhere.  
Kill B: direct key-bytes -> SQL ExternalID placeholder dataflow.

### H-VERTEXARRAY

**A:** Coordinate/Normal/UV specializations consume actual mesh arrays.  
**B:** they belong to preset/editor/cache structures outside the target load path.

Kill A: prove they are reachable only from a non-target path.  
Kill B: direct Canvas3DModelLoader/ModelData -> specialization -> reader -> destination chain.

### H-HALFEDGE-INDEX

**A:** VertexIndex is mesh-topology indexing.  
**B:** it is editor half-edge/object-reference indexing.

PairID/PostID and EditPreset context materially support B as a live competitor. The name `VertexIndex` alone is insufficient.

### H-WEIGHTINFO

**A:** WeightInfo is skinning-weight data.  
**B:** preset/editor weight metadata.

The joint BoneName/MeshName/WeightInfo/BindMatrix type pattern supports A as a candidate, but the absent direct construction bridge prevents promotion.

## COUNTEREXAMPLES / NEGATIVE CONTROLS

1. **`CLIP_STUDIO_3D_DATA2` is not a proved consumer entry.** Its observed xref is `0x140025c00`, which has no direct callers and only static-string construction/atexit behavior in the exported graph. Treat “DATA2 string hit = parser” as **REJECTED**.
2. `ModelInfo3D` / `ModelNodeInfo3D` observed xrefs are likewise static initializers; name presence alone is **REJECTED** as a direct consumer path claim.
3. No direct path was found from chunk/registration islands to CrM vertex/bone/UV candidates. This is a negative control against premature construction claims; indirect dispatch remains open.

## CONTROLLED FIXTURE PREDICTIONS

These predictions were generated **consumer-first**, not fitted to teacher values.

### CF-EXT-OFFSET-01

For any F01–F07 / R01–R05 / V01 pair where structural IR independently establishes a physical byte delta before a later external record: if `ExternalChunk.Offset` is a physical seek position, affected later offsets must move by the exact cumulative preceding delta while earlier offsets remain unchanged.

### CF-CHNK-ID-01

For any controlled pair isolating a CHNKExta key-like region: under H-KEY-EXTERNALID, unchanged key bytes imply unchanged SQL ExternalID even if Offset changes; a controlled key change must alter ExternalID iff the key feeds the first INSERT placeholder.

### CF-BOUND-READ-01

For any controlled pair with a validated boundary/length shift and stable upstream prefix: a length-delimited consumer should alter loop/skip bounds at that boundary; a fixed-size reader should not.

These are independently testable predictions, but **not** a current `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`.

## F02 ORACLE DISCRIMINATION MAP

Physical oracle remains `0/30 / PENDING_MANUAL_ORACLE`. Canonical Sentinel-9 is unchanged:

`M01 -> M10 -> M13 -> M14 -> M15 -> M18 -> M22 -> M23 -> M30`

Proposal-only interpretation from this independent pass:

- `M13/M14/M15`: boundary-transition discriminator for a future direct reader binding at payload 3216.
- `M01/M10`: uniform-vs-partitioned variable-prefix reader.
- `M18`: invariant-interior same-loop vs substructure discriminator.
- `M22/M23/M30`: logical-end vs framing-remainder discriminator.

No new order is proposed as canonical. The Full Snapshot **does not yet prove** that F02 DATA2 is consumed by `0x140d15a90` or the reader family above.

## DISCRIMINATING QUESTIONS FOR MAINLINE

- DQ-EXT-01: Does `0x140d175d0` SELECT Offset result control seek/CHNKExta payload read?
- DQ-EXT-02: What bytes feed ExternalID and Offset in `0x140d15700` / `0x140d17e20`?
- DQ-LOAD-01: Where is the runtime registry lookup/factory invocation for `ModelData -> Canvas3DModelLoader`?
- DQ-F02-BND-01: after a direct F02 binding, does a reader transition at 3216?
- DQ-F02-TERM-01: does the consumer distinguish 17687 from framing remainder 17688+?

These are questions for independent confirmation, not answers imposed on Mainline.

## QUESTIONS FOR MODELER STATIC

- DQ-SER-01: resolve vtable slot and direct primitive for `ODDPresetVertexArray::Coordinate` specialization.
- DQ-SER-02: resolve integer width/endian/count/destination for `ODDEditPresetHalfEdge::VertexIndex` specialization.
- DQ-WGT-01: resolve WeightInfo destination and downstream bone/skin consumer.
- DQ-DATA2-01: find a post-initialization consumer of `CLIP_STUDIO_3D_DATA2`.
- DQ-CONSTRUCT-01: resolve any indirect/vtable bridge from serializer/model-loader island to CrM construction functions.

## UNRESOLVED

- `EXPLICIT_CSMC_HANDLER_ENTRY = UNRESOLVED`
- `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP = CANDIDATE` (query xref exists; result flow unresolved)
- `EXPLICIT_MODELDATA_LOOKUP = UNRESOLVED`
- `EXPLICIT_CANVAS3D_LOAD_ENTRY = UNRESOLVED`
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION = UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`
- geometry/index/UV/material/bone/weight semantic confirmation = unresolved

## C-069 DECISION

C-069 **is authorized and created** because this pass found a genuinely new direct consumer edge and direct body-level chain beyond FIRST PASS: `0x141657970 -> 0x140d15a90`, followed by marker validation, confirmed BE-u64 reads, length-driven cursor movement, CHNKSQLi bounded transfer and ExternalChunk SQLite construction. It also generated independent controlled predictions.

This does **not** authorize semantic promotion, Blender emit, runtime dispatch, MODELER execution, Worker/Canary, RIO-26, or mainline mutation.

The independent report is sealed before cross-lane comparison. Status: **READY_FOR_CROSS_LANE_COMPARE**.
