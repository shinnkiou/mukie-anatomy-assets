# CSMC ANALYSIS COMPANION C — FULL SNAPSHOT CROSS-LANE COMPARE V1

Date: 2026-09-14
Status: `UNNUMBERED_CROSS_LANE_RECONCILIATION_NOT_NEW_C_RUN`
Independent source run: **C-069**
Independent seal state before comparison: **READY_FOR_CROSS_LANE_COMPARE**
Pipeline: `STRUCTURAL_ONLY`
Semantic promotion: 0
Blender emit: BLOCKED
Runtime dispatch: false

## Scope and chronology

This comparison was created only after Companion C sealed its independent Full Snapshot report and hashes. It compares the already-sealed Companion C result against the later-visible Mainline/Static Full Snapshot reconciliation. It does not retroactively modify C-069 and does not create C-070.

Canonical Companion C-069 durability remains Supabase row **209**. The later row 213/Base44 duplicate is audit-only and must not be counted as a second evidence event.

## Inputs

### Companion C independent result
- snapshot SHA-256: `afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342`
- MODELER EXE SHA-256: `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`
- GitHub head at seal: `aad64b96fad0699426d36f1f0bfd290a4f5751ad`
- canonical Supabase row: 209
- report SHA-256: `c69210650141db74ab3fc17a835a5d42c86c840a5c31bd34abb9de38cb423bdd`
- evidence SHA-256: `5901afd90b42261cc57f95508aa89c40c978ae4e4ceebee4bcc3c4cff781b5b5`
- questions SHA-256: `22dde754c1e7e777ed3732a011ca63d18f7db64f6979dfb2e2db5a9fd628fb8b`

### Mainline/Static comparison source
- Full Snapshot reconciliation: Supabase row 207
- static head: `fa3c3a7af57342eee9178cd78a65c11a83f8c471`
- Mainline current checkpoint observed after seal: row 214
- row214 still reports `EXPLICIT_SERIALIZER_FIELD_READ=UNRESOLVED` and `DQ-SER-WIDTH-01=WAIT_FOR_PROOF`.

## Cross-lane comparison

| Evidence class | Companion C sealed result | Mainline/Static result | Factual comparison | Reconciliation |
|---|---|---|---|---|
| `EXPLICIT_CSMC_HANDLER_ENTRY` | UNRESOLVED | UNRESOLVED | Agreement | No direct `.csmc` dispatch edge yet. |
| ExternalChunk exact SELECT lookup | exact query localized at `0x140d175d0`, caller `0x1416578e0` | same concrete function/caller | Strong agreement | Direct fact is shared. |
| `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP` | CANDIDATE | CONFIRMED / proof-grade | Classification disagreement | Companion requires SELECT-result → seek/read destination; Mainline admits exact keyed lookup itself. `DQ-EXT-01` discriminates. |
| `ModelData -> Canvas3DModelLoader` registration | CONFIRMED registration fact | CONFIRMED registration fact | Strong agreement | Both see same pair/helper. |
| `EXPLICIT_MODELDATA_LOOKUP` | UNRESOLVED | CONFIRMED / proof-grade | Classification disagreement | Companion preserves frozen definition that registration != later lookup/factory invocation. `DQ-LOAD-01` discriminates. |
| `EXPLICIT_CANVAS3D_LOAD_ENTRY` | UNRESOLVED | CANDIDATE | Compatible | Neither has concrete loader method invocation. |
| `EXPLICIT_SERIALIZER_FIELD_READ` | UNRESOLVED | UNRESOLVED | Agreement | Full Snapshot does not yet bind F02/serializer primitive + width/endian/count/destination/data-flow. |
| `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION` | UNRESOLVED; no direct CrM path observed | CANDIDATE via GADCharacter importer RTTI/vtables | Threshold/target-set difference | No direct construction call/data-flow is agreed. |
| `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH` | UNRESOLVED | UNRESOLVED | Agreement | No same-identity fixture binding. |
| F02 frozen five questions | unresolved | unresolved | Agreement | Physical oracle remains 0/30. |
| semantic promotion | 0 | 0 | Agreement | No geometry/index/UV/material/bone/weight promotion. |

## Independent Companion-only contributions

1. `0x141657970 -> 0x140d15a90` direct caller edge.
2. Body-level chain inside `0x140d15a90`: marker validation -> BE-u64 reads -> length/cursor operations -> fixed 16-byte destination read -> CHNKSQLi bounded read/write -> ExternalChunk SQLite initialization.
3. Fixed 16-byte read destination rooted at object storage (`param_1 + 0x1e`) after explicit resize.
4. Consumer-first controlled predictions `CF-EXT-OFFSET-01`, `CF-CHNK-ID-01`, `CF-BOUND-READ-01`.
5. Negative controls rejecting `CLIP_STUDIO_3D_DATA2`, `ModelInfo3D`, and `ModelNodeInfo3D` string/static-initializer hits as direct consumer proof.

## Mainline-only emphasis

1. Mainline admits the exact ExternalChunk keyed lookup itself as proof-grade `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP`.
2. Mainline calls the `ModelData -> Canvas3DModelLoader` registration relation proof-grade `EXPLICIT_MODELDATA_LOOKUP`.
3. Mainline retains `ODCImporterT<GADCharacter>` / GADCharacter serializer RTTI as `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION=CANDIDATE`.
4. Mainline follow-up row214 has a fail-closed width gate; synthetic 16/32-bit survivor counts are explicitly not real serializer-width evidence and no F02 pruning was applied.

## Interpretation of disagreements

### 1. ExternalChunk: fact agrees, proof threshold differs

There is no factual contradiction that `0x140d175d0` contains the exact `SELECT Offset FROM ExternalChunk WHERE ExternalID='%s'` lookup and is called from `0x1416578e0`.

The disagreement is what `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP` is intended to certify:
- Mainline: exact keyed field lookup is sufficient.
- Companion: the frozen SECOND PASS question also required the lookup result's concrete downstream consumer/seek semantics.

Fail-closed reconciliation: retain the shared direct lookup fact, but keep **result -> physical seek/read** unresolved until `DQ-EXT-01` is answered.

### 2. ModelData: registration is agreed; runtime lookup remains unproved under Companion definition

Both lanes directly observe `ModelData -> Canvas3DModelLoader` registration. The Mainline report names this `EXPLICIT_MODELDATA_LOOKUP=CONFIRMED`; Companion does not, because the original missing edge was the **later registry lookup/factory selection/load invocation**.

Fail-closed reconciliation: record **REGISTRATION CONFIRMED** without silently converting that fact into a runtime lookup. `DQ-LOAD-01` remains open.

### 3. Construction: candidate evidence exists but no direct bridge

Mainline's GADCharacter importer RTTI and Companion's typed serializer RTTI both support the existence of rich model-import structures. Companion's direct-call negative control did not find a bridge from the chunk/registration islands into selected CrM vertex/bone/UV construction candidates.

This is not a contradiction: virtual/function-pointer dispatch can be absent from `call_edges.tsv`. Keep `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION` below CONFIRMED until a destination/call/data-flow edge is bound.

## Discriminating questions after comparison

### `DQ-EXT-01`
Does the result of `0x140d175d0` directly control cursor positioning, seek/advance, or CHNKExta payload read?

Required evidence: targeted decompile, SQL-result destination, result-to-position/read data-flow, negative control.

### `DQ-LOAD-01`
Where is the later runtime registry lookup/factory call that takes `ModelData` and invokes a concrete `Canvas3DModelLoader` load method?

Required evidence: lookup callsite, returned function/factory target, load-entry call, ModelData acquisition.

### `DQ-SER-WIDTH-01`
What actual width/endian/count/destination does a concrete serializer specialization use?

Mainline row214 correctly remains `WAIT_FOR_PROOF`; synthetic 16/32-bit counts cannot answer it. Hard F02 pruning additionally requires an explicit F02 DATA2 variable-prefix binding.

### `DQ-CONSTRUCT-01`
Does an indirect/vtable/function-pointer edge connect the loader/serializer island to a concrete model-construction destination?

## Cross-lane verdict

The independent pass is **usefully independent**: it converges with Mainline on the architecture and all semantic gates, while disagreeing at two admission boundaries rather than merely duplicating labels.

Shared high-confidence facts:
- ExternalChunk keyed Offset query exists at a concrete function/caller.
- `ModelData -> Canvas3DModelLoader` registration is direct.
- concrete byte/chunk reader primitives exist.
- serializer/model-related RTTI is extensive.
- the requested F02 serializer field-read bridge remains unproved.
- fixture-to-consumer match remains unproved.

No cross-lane averaging or automatic promotion is allowed. The stricter unresolved state is retained wherever the lanes disagree about whether a label's evidence contract has been fully satisfied.

## Gates

- latest numbered Companion run remains **C-069**
- C-070: **NOT CREATED**
- `STRUCTURAL_ONLY`
- semantic promotion = 0
- Blender emit = BLOCKED
- runtime dispatch = false
- MODELER runtime action = 0
- physical oracle = `0/30 PENDING_MANUAL_ORACLE`
- canonical Sentinel-9 unchanged
- Worker / Canary / Control Gate / Production / STABLE = 0
- RIO-26 mutation = 0
- mainline mutation = 0

Status: `CROSS_LANE_COMPARE_COMPLETE_FAIL_CLOSED`.
