# CSMC MODELER STATIC ANALYSIS — SECOND PASS bounded checkpoint

Date: 2026-09-14
Lane: MODELER consumer-side static analysis
Status: `BOUND_CHECKPOINT_NOT_PROOF_RUN`

## Purpose

Continue the MODELER 1.10.13 consumer-side static-analysis lane without repeating FIRST PASS and without changing Companion C's controlled-differential role.

This checkpoint records what can and cannot currently be proved from the accessible public-safe handoff plus connected durable stores. It does not claim a new consumer edge where none was observed.

## Source identity

Public-safe handoff ZIP SHA-256:

`4aa70ad694e2ab202466993ab526a8424e5b6f414908a9c8053975533eff14a5`

Referenced private analysis package:

- package: `CSMC_MODELER_STATIC_ANALYSIS_PACKAGE_20260914.zip`
- package SHA-256: `099E62273CAAE43D74EE4E8FF3A746E4F0BD2B55E2D95A05E5C51D42D55DC80B`
- executable: `CLIPStudioModeler.exe`
- executable SHA-256: `2EBE2D90F8609496CB2E81A7C9DEFAE4E851479B8E5DB76EB9DD8EC05D943150`
- version: CLIP STUDIO MODELER 1.10.13

The currently attached handoff contains public-safe reports/manifests only. The referenced private EXE/DLL analysis package was not present in the attached ZIP and was not located in the connected Drive/Base44/Supabase artifact surfaces checked in this pass.

## FIRST PASS state — do not reopen

The following are already CONFIRMED and are excluded from SECOND PASS re-search:

- `EXPLICIT_PARENT_RECORD_BOUNDARY`
- `EXPLICIT_PARENT_LENGTH_FIELD`
- `EXPLICIT_CONSUMER_CROSSREF`

Known direct anchors retained:

- CSFCHUNK parser loop near `0x140D18000`
- BE-u64 reader path `0x1408C2D90 -> 0x1408C26E0`
- BE-u64 writer path `0x1408C1960 -> 0x1408C1650`
- `record_end = position_after_length + record_length`
- registry registration block near `0x140D45EAB`
- registry wrapper around `0x141657140`
- registry insertion around `0x141656A80`
- explicit pair `ModelData -> Canvas3DModelLoader`

## SECOND PASS proof graph — current accessible state

### Island 1 — `.csmc` dispatch

Known:
- `.csmc` is active in runtime extension/type comparison paths.

Missing proof edge:
- exact selected handler/factory/load entry.

Classification:
- `EXPLICIT_CSMC_HANDLER_ENTRY = UNRESOLVED`

### Island 2 — CSFCHUNK / CHNKExta / ExternalChunk

Known:
- explicit parent record boundary and BE-u64 length semantics;
- CHNKExta reader/writer structural symmetry;
- provisional field order: tag, record_length, key_length=0x28, 40-byte key, payload_length, payload;
- SQLite `ExternalChunk(ExternalID BLOB, Offset INTEGER)` SQL strings and read/write statements exist in a coherent consumer cluster.

Missing proof edges:
- producer identity of the 40-byte CHNKExta key;
- data-flow identity between that key and SQLite `ExternalID`;
- producer of `Offset`;
- exact lookup result consumer;
- exact target semantics of `Offset`.

Classification:
- `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP = UNRESOLVED`

Do not promote `CHNKExta key == ExternalID` from locality alone.

### Island 3 — ModelData registry / Canvas3DModelLoader

Known:
- executable registration is direct and explicit: `ModelData -> Canvas3DModelLoader`.

Missing proof edges:
- later registry lookup callsite;
- function-pointer/factory selection;
- concrete Canvas3DModelLoader constructor/load entry;
- ModelData acquisition at that load entry;
- downstream child parser/model-object creation.

Classification:
- `EXPLICIT_MODELDATA_LOOKUP = UNRESOLVED`
- `EXPLICIT_CANVAS3D_LOAD_ENTRY = UNRESOLVED`

A registration pair is not itself a proven load call.

### Island 4 — serializer field reads

Known:
- serializer/importer architecture strings/templates exist, including `ODCImporterT`, `ODIChunkCellImporterT`, `serialize_traits` and labels such as `WeightInfo`, `VertexIndex`, `PointIndex`, `LineIndex`, `FaceIndex`, `Material`.

Missing proof edge:
- a direct field-read operation tying one label/template instantiation to a concrete read primitive, width/endian/count rule, destination field, and caller path.

Classification:
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`

String/RTTI proximity remains CANDIDATE only.

### Island 5 — internal model construction

Known:
- MODELER contains explicit FBX consumer APIs for mesh, UV, material, transforms, skin clusters, control-point weights and matrices.

Missing proof edge:
- convergence from the CSMC ModelData/serializer path into the same internal model construction functions/objects.

Classification:
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION = UNRESOLVED`

FBX capability does not prove CSMC payload semantics.

### Island 6 — controlled fixture bridge

New mainline structural input visible in the connected store:
- `CSMC_MAINLINE_SCOUT_SEGMENT_IR_20260914`
- structural segment IR materializes seven validated pairwise ranges as `VARIABLE_PREFIX_CANDIDATE_REGION`, `EXACT_INVARIANT_CORE`, and `TERMINAL_REMAINDER_CANDIDATE_REGION`.
- semantic promotion remains zero.

Manual mutation-oracle batch:
- `CSMC_F02_SINGLE_BYTE_XOR01_30_20260914`
- 30 variants exist, but every current observation row remains `PENDING_MANUAL_ORACLE`.

Missing proof edge:
- no currently accessible consumer field-read/callsite binds a controlled segment to a specific serializer/internal-model field.

Classification:
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`

The segment IR narrows search space but is not consumer binding evidence by itself.

## Evidence-value decision

No new proof-grade consumer edge was found in this pass from the accessible public-safe corpus. Therefore this is deliberately not numbered as a proof run and does not mark any A-G item CONFIRMED.

The current highest-value target remains `EXPLICIT_SERIALIZER_FIELD_READ`, because Companion C now has bounded structural candidate regions and needs one concrete consumer read to begin an independent cross-check. A valid direct field-read slice may naturally continue into `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION`; if instead the lookup/factory chain is encountered first, `EXPLICIT_MODELDATA_LOOKUP` / `EXPLICIT_CANVAS3D_LOAD_ENTRY` should be followed without forcing serializer semantics.

## Bounded close

`BOUND`:
accessible public-safe handoff + GitHub/Drive/Base44/Linear/Supabase durable evidence as of this pass.

`REASON`:
the private MODELER binary/decompiler database or a new public-safe SECOND PASS call/data-flow slice is not available to this execution lane. Existing reports expose FIRST PASS conclusions but not enough instruction-level data to establish the missing call/data-flow edges.

`WHAT_WAS_EXHAUSTED`:
- exact/broad connected-store search for MODELER SECOND PASS outputs;
- `EXPLICIT_SERIALIZER_FIELD_READ` artifacts;
- dispatch/callgraph/index-flow output names from the handoff plan;
- private-package hash/name references in connected durable ledgers;
- pending mutation-oracle observation sheet.

`NEXT_HIGH_VALUE_EVIDENCE`:
one private read-only static-analysis slice that proves a direct serializer field read, preferably around `ODIChunkCellImporterT`, containing public-safe aggregate facts only:
- executable hash;
- caller/callee/function VAs;
- template/class/field label;
- direct read primitive and width/endian behavior;
- count/length source if applicable;
- destination object/field or downstream consumer;
- call/data-flow link back toward Canvas3DModelLoader/ModelData where available;
- confidence and negative-control note.

Alternative high-value slice: a direct registry lookup/factory/load-entry chain for `ModelData -> Canvas3DModelLoader`.

Do not request runtime execution to obtain either slice.

## Isolation readback

- MODELER process actions: 0
- hooks/injection/patches: 0
- save/Ctrl+S triggers: 0
- runtime dispatch: false
- Worker/Canary/Control Gate/Production/STABLE mutations: 0
- RIO-26 mutations: 0
- mainline branch mutations: 0
- semantic promotions: 0
- Blender emit: BLOCKED
- private binary/raw decompiler publication: false
