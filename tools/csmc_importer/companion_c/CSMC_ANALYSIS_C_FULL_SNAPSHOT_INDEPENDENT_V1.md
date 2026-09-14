# CSMC ANALYSIS COMPANION C â€” C-069 FULL STATIC SNAPSHOT INDEPENDENT DEEP PASS

Date: 2026-09-15  
Run: **C-069**  
Status: **SEALED_INDEPENDENT_ANALYSIS_READY_FOR_CROSS_LANE_COMPARE**  
Pipeline: `STRUCTURAL_ONLY`

## Independence / contamination guard

This pass was performed from the pre-Full-Snapshot safe Companion base `0121fa9187d11a9578945ed2522787911fc8b3c4` on isolated branch `csmc-analysis-companion-c-fullsnapshot-independent-20260915`. During initialization, the ordinary Companion branch was observed to have moved to a newer commit with a post-seal cross-lane-comparison commit message. Its content was deliberately **not read**. No Mainline NEW Full Snapshot result was consulted before this report was sealed.

## Provenance

- snapshot: `CSMC_FULL_SNAPSHOT_20260914_214659.zip`
- snapshot SHA-256: `afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342`
- target: CLIP STUDIO MODELER 1.10.13
- target EXE SHA-256: `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`
- Ghidra: 12.1.3
- internal inventory verification: 195/195 hashes matched, missing 0
- runtime started: false
- semantic promotion: false

Observed snapshot tables: 75,721 functions, 267,088 direct call edges, 29,883 strings, 669,282 symbols. These counts describe the snapshot tables and are not semantic evidence by themselves.

## C-069 admission decision

**C-069 is justified by new direct consumer evidence, not by inventory readiness.**

The new evidence is a direct container-reader chain in `FUN_140d15a90` that was not available in the earlier public-safe SECOND PASS checkpoint:

1. CSFCHUNK / CHNKHead-family tags are read and directly validated.
2. an encoded integer field is required to equal exactly `0x10`;
3. `FUN_1408c0d40` sizes an object-relative destination (`param_1 + 0x1e`) to exactly 16 bytes;
4. `FUN_1408c27c0` transfers exactly 16 bytes from the parser/stream context into that returned destination pointer.

This is classified **CONFIRMED direct container field read**. The 16-byte field's meaning is **UNRESOLVED**. It is not promoted to ExternalID, UUID, checksum, geometry, or any serializer semantic.

A second direct edge in the same function validates `CHNKSQLi`, decodes a u64 length, allocates/prepares a 1 MiB transfer buffer, and loops over `min(remaining, capacity)` while transferring exactly the same chunk size into a destination stream/object and decrementing `remaining` by that size. This is **CONFIRMED length-bounded streaming copy**.

Therefore the run condition `new direct consumer edge` is met. `EXPLICIT_SERIALIZER_FIELD_READ` is **not** closed by this evidence.

## Direct consumer edges

### E-C069-001 â€” CONFIRMED â€” 16-byte container field read

Direct path:

`0x141657970 -> 0x140d15a90 -> {0x1408c2d90, 0x1408c0d40, 0x1408c27c0, 0x1408c2f40}`

- `0x1408c2d90 -> 0x1408c26e0` remains the pre-existing FIRST PASS BE-u64 reader fact.
- `0x1408c0d40` is now directly decompiled in this snapshot and is a buffer-resize/ensure operation: it grows storage when required, preserves old logical bytes, sets logical size to the requested size, and returns the data pointer.
- `0x1408c27c0` is used as the bounded transfer primitive; its call graph includes `memcpy`.
- `0x1408c2f40` is a fixed-length comparison helper and directly calls `memcmp`.

Negative control: the 16-byte field is **not identified** as ExternalChunk.ExternalID. There is no direct identity edge, and the prior CHNKExta key-width evidence is different. Field meaning remains opaque.

### E-C069-002 â€” CONFIRMED â€” CHNKSQLi length-bounded transfer

After CHNKSQLi validation, a decoded u64 determines the remaining byte count. The function forwards exactly that many bytes in bounded chunks. This proves a concrete read-length â†’ loop-bound â†’ transfer chain at the container/database layer; it does not identify any mesh semantic.

## ExternalChunk / CHNKExta island

The exact target binary contains direct SQL xrefs:

- `CREATE TABLE IF NOT EXISTS ExternalChunk(ExternalID BLOB, Offset INTEGER);` -> `0x140d18650`, `0x140d15a90`
- `DELETE FROM ExternalChunk;` -> `0x140d18650`, `0x140d15a90`
- `INSERT INTO ExternalChunk VALUES('%s',%s);` -> `0x140d17e20`, `0x140d15700`
- `SELECT Offset FROM ExternalChunk WHERE ExternalID='%s';` -> **`0x140d175d0`**

Direct call roots:

- `0x1416578e0 -> 0x140d175d0` (lookup island)
- `0x141657540 -> 0x140d17e20` (insert/write island)
- `0x141657e60 -> 0x140d15700` (insert/write island)
- `0x141657970 -> 0x140d18650` and `0x141657970 -> 0x140d15a90` (schema/container initialization/read island)

`0x140d175d0` contains the SELECT xref and directly calls the BE-u64 reader thunk, bounded transfer, fixed compare, buffer resize, and `0x1408c2dc0`. This is **STRONG local convergence** for a CHNKExta-related lookup consumer, but the snapshot lacks its decompiled body, so **SELECT result -> seek/cursor** remains unresolved.

## ModelData / Canvas3DModelLoader registry island

`0x14023a330 -> 0x140d45d30 -> 0x141657140 -> 0x141656a80`

`0x140d45d30` directly registers:

- `ModelData -> Canvas3DModelLoader`
- `BankData -> Canvas3DModelBank`
- `SceneData -> Manager3DOd`
- `Layer3DModelData -> ModelData3D`

This is CONFIRMED registration, **not** a proven lookup or load invocation. `EXPLICIT_MODELDATA_LOOKUP` and `EXPLICIT_CANVAS3D_LOAD_ENTRY` remain unresolved.

## Typed serializer architecture

The exact MODELER binary contains concrete `ODCChunkCellImporterT` RTTI/vtables for, among others:

- `ODDPresetVertexArray`: Coordinate, Normal, UV, NextLinkIndex
- `ODEditPresetHalfEdge`: VertexIndex, PointIndex, LineIndex, FaceIndex
- `ODDPresetMesh`: VertexArray, FaceArray, MaterialData, Location, Name/NodeName
- `ODDPresetSkin`: BoneName, MeshName, WeightInfo, BindMatrix
- `ODDFaceData`: VertexIndex

This is **STRONG architecture evidence** that typed importers for model-like fields exist in this exact executable. It is **not a CSMC binding**: the snapshot does not provide a direct Canvas3DModelLoader/ModelData -> typed importer dispatch or a typed importer -> numeric reader -> destination chain. Consequently `EXPLICIT_SERIALIZER_FIELD_READ` remains `UNRESOLVED`.

## Reader catalog

| Primitive | Classification | Level | C-069 meaning |
|---|---|---|---|
| `0x1408c2d90 -> 0x1408c26e0` | BE-u64 reader | CONFIRMED, pre-existing | framing/count reader |
| `0x1408c27c0` | bounded stream-to-buffer transfer | CONFIRMED in direct local use | exact 16-byte and chunk transfers |
| `0x1408c2f40` | fixed-length compare | CONFIRMED | tag validation (`memcmp`) |
| `0x1408c0d40` | buffer resize/ensure + data pointer | CONFIRMED | direct destination construction |
| `0x1408c2dc0` | cursor/skip-like | CANDIDATE | body unavailable; do not call seek yet |
| `0x1408c2db0` | remaining/size-like | CANDIDATE | body unavailable |

Reader catalog does not imply CSMC semantic binding.

## Construction side

Newly confirmed destination/construction facts are limited to the **container layer**:

- object-relative 16-byte buffer allocation/resize and direct fill;
- CHNKSQLi bounded transfer buffer and destination stream forwarding.

No proof-grade internal mesh/node/material/bone construction edge has been connected to the CSMC loader path. Typed mesh/skin RTTI is strong but unbound.

## Negative controls / counterexamples

1. `ModelInfo3D`, `ModelNodeInfo3Da, `Canvas3DModelLoader`, `Layer3DModelData`, and `CLIP_STUDIO_3D_DATA2` have semantic-looking string hits whose direct xrefs can terminate in small global/string initializer functions. **String hit != consumer evidence.**
2. `ModelData -> Canvas3DModelLoader` registration does not prove later lookup/load invocation.
3. Typed `ODCChunkCellImporterT` vtables do not prove they consume CSMC until loader reachability is shown.
4. The 16-byte field must not be named ExternalID/UUID/etc. without a direct downstream identity edge.

## Competing hypotheses

### H-EaPµ=MP)èáÑ•É¹…±¡Õ¹¬¹=™™Í•Ñ€¥Ì„Á¡åÍ¥…°ÍÑÉ•…´½™¥±”½•±°Á½Í¥Ñ¥½¸ÕÍ•Ñ¼±½…Ñ”!9-áÑ„Á…å±½…¸€€)è¥Ð¥Ì„‘…Ñ…‰…Í”µÉ•±…Ñ¥Ù”½Èµ•Ñ…‘…Ñ„½É•™•É•¹”Í…±…È¸()MÕÁÁ½ÉÐèM1Pµ‰äµáÑ•É¹…±%…¹!9-áÑ„½Á…ÉÍ•ÈÁÉ¥µ¥Ñ¥Ù•Ì½¹Ù•É”¥¸€ÁàÄÐÁÄÜÕÁ€¸€€)MÕÁÁ½ÉÐè¥ÑÌ‰½‘ä¥Ì¹½Ð¥¸Ñ¡”Ñ…É•Ñ•‘•½µÁ¥±”Í•Ðì‘¥É•ÐÅÕ•ÉäµÉ•ÍÕ±ÐµÑ¼µÕÉÍ½È™±½Ü¥Ì…‰Í•¹Ð¸€€)-¥±°èÍ¡½ÜÉ•ÍÕ±Ð¹•Ù•ÈÉ•…¡•ÌÁ½Í¥Ñ¥½¸½ÕÉÍ½ÈÍÑ…Ñ”¸€€)-¥±°èÍ¡½ÜÉ•ÍÕ±Ð‘¥É•Ñ±ä™••‘Ì„ÍÑÉ•…´µÁ½Í¥Ñ¥½¸ÁÉ¥µ¥Ñ¥Ù”‰•™½É”!9-áÑ„ÑÉ…¹Í™•È¸((ŒŒŒ µQeAµMI%1%iH)èÑåÁ•=‘åÍÍ•ä¥µÁ½ÉÑ•ÉÌ…É”½¸Ñ¡”M55½‘•±…Ñ„±½…Á…Ñ ¸€€)èÑ¡•ä…É”Õ¹É•±…Ñ•ÁÉ•Í•Ð½•‘¥Ñ½ÈÝ½É­™±½ÝÌ¸()-¥±°èÁÉ½Ù”¹¼±½…‘•ÈÉ•…¡…‰¥±¥Ñä…¹½¹±äÕ¹É•±…Ñ•…±±•ÉÌ¸€€)-¥±°è½¹”‘¥É•Ð±½…‘•ÈµÑ¼µ¥µÁ½ÉÑ•È‘¥ÍÁ…Ñ Á±ÕÌÉ•…‘•È½‘•ÍÑ¥¹…Ñ¥½¸‰¥¹‘¥¹œ¸((ŒŒŒ ´ÄÙµ%1)èÁ•ÉÍ¥ÍÑ•¹Ð½¹Ñ…¥¹•È¥‘•¹Ñ¥Ñä½¥¹Ñ•É¥Ñä½‘•ÍÉ¥ÁÑ½È‘…Ñ„¸€€)è½Á…ÅÕ”ÑÉ…¹ÍÁ½ÉÐµ•Ñ…‘…Ñ„¸()-¥±°•¥Ñ¡•È‰äÑÉ…¥¹œÑ¡”½‰©•ÐµÉ•±…Ñ¥Ù”‘•ÍÑ¥¹…Ñ¥½¸Ñ¼¥ÑÌ™¥ÉÍÐµ•…¹¥¹™Õ°‘½Ý¹ÍÑÉ•…´½¹ÍÕµ•È¸((ŒŒ½¹ÑÉ½±±•™¥áÑÕÉ”ÁÉ•‘¥Ñ¥½¹Ì((ŒŒŒ@µÀØä´ÀÀÄƒŠP½¹‘¥Ñ¥½¹…°°¥¹‘•Á•¹‘•¹Ñ±äÑ•ÍÑ…‰±”()%˜Ñ¡”•ÍÑ…‰±¥Í¡•ÀÈ€ØÔµ‰åÑ”½ÕÑ•È•¹Ù•±½Á”µ…ÁÌÑ¼Ñ¡”M!9,½!9-!•…™É…µ¥¹œÑ¡…Ð¥ÌÁ…ÉÍ•‰•™½É”Ñ¡”‘½Ý¹ÍÑÉ•…´µÕÑ…Ñ¥½¸Á…å±½…°Ñ¡•¸4ÀÄµ4ÌÀÍ¡½Õ±¹½Ð¡…¹”Ñ¡”•á…Ð€ÄØµ‰åÑ”¡•…‘•ÈÉ•…½È¥ÑÌÁÉ••‘¥¹œÑ…œ½±•¹Ñ …•ÁÑ…¹”¸™…¥±ÕÉ”…ÑÑÉ¥‰ÕÑ…‰±”‰•™½É”Ñ¡…Ð±…å•ÈÝ½Õ±™…±Í¥™äÑ¡”½½É‘¥¹…Ñ”µ…ÁÁ¥¹œ½ÈÉ•Ù•…°Á…å±½…µÝ¥‘”¥¹Ñ•É¥Ñä½ÕÁ±¥¹œ¸()Q¡¥ÌÁÉ•‘¥Ñ¥½¸Ý…Ì•¹•É…Ñ•™É½´Ñ¡”¹•Ü½¹ÍÕµ•ÈÁ…Ñ ™¥ÉÍÐì¹¼Ñ•…¡•ÈÙ…±Õ”Ý…ÌÕÍ•Ñ¼Í•±•Ð…¸…¹ÍÝ•È¸((ŒŒŒ@µÀØä´ÀÀÈƒŠPáÑ•É¹…±¡Õ¹¬É•±½…Ñ¥½¸½¹ÑÉ½°()%˜áÑ•É¹…±¡Õ¹¬¹=™™Í•Ñ€¥Ì„Á¡åÍ¥…°±½…Ñ¥½¸°Ñ¡•¸É•±½…Ñ¥¹œ…¸½Ñ¡•ÉÝ¥Í”¥‘•¹Ñ¥…°áÑ•É¹…±%µ‰…­•Á…å±½…‰ä‘•±Ñ„‰åÑ•ÌÁÉ•‘¥ÑÌ…¸=™™Í•Ð¡…¹”½˜Ñ¡”Í…µ”‘•±Ñ„Ý¡¥±”ÁÉ•Í•ÉÙ¥¹œáÑ•É¹…±%¸µ•Ñ…‘…Ñ„½É•™•É•¹”¥¹Ñ•ÉÁÉ•Ñ…Ñ¥½¸‘½•Ì¹½ÐÉ•ÅÕ¥É”Ñ¡¥Ì•ÅÕ…±¥Ñä¸ÁÉ½Ù•¹…¹”µ‰½Õ¹É•±½…Ñ¥½¸µ½¹±ä™¥áÑÕÉ”…¸Ñ¡•É•™½É”‘¥ÍÉ¥µ¥¹…Ñ”Ñ¡”¡åÁ½Ñ¡•Í•Ì¸((ŒŒÀÈ½É…±”‘¥ÍÉ¥µ¥¹…Ñ¥½¸()A¡åÍ¥…°½‰Í•ÉÙ…Ñ¥½¹ÌÉ•µ…¥¸Õ¹™¥±±•¥¸Ñ¡”™É½é•¸µ…À¸…¹½¹¥…°M•¹Ñ¥¹•°´ä¥ÌÁÉ•Í•ÉÙ•Õ¹¡…¹•è()4ÀÄ€´ø4ÄÀ€´ø4ÄÌ€´ø4ÄÐ€´ø4ÄÔ€´ø4Äà€´ø4ÈÈ€´ø4ÈÌ€´ø4ÌÁ€()Q•Éµ¥¹…°•á…Ðµ…Àè((´4ÈÈÁ…å±½…€ÄÜØàÜ€¼‰±½ˆ€ÄÜÜÔÈè…±¥¹µ•¹Ðµ•áÑ•¹Í¥½¸ÍÑ…ÉÐ(´4ÈÌÁ…å±½…€ÄÜØàà€¼‰±½ˆ€ÄÜÜÔÌè™É…µ¥¹œµÉ•µ…¥¹‘•ÈÍÑ…ÉÐ(´4ÈÐ¸¹4ÌÀÁ…å±½…€ÄÜØàä¸¸ÄÜØäÔ€¼‰±½ˆ€ÄÜÜÔÐ¸¸ÄÜÜØÀè™É…µ¥¹œÉ•µ…¥¹‘•È()9¼…¹½¹¥…°É•½É‘•È¥ÌÁÉ½Á½Í•¸Q¡”¹•Ü½ÕÑ•Èµ•¹Ù•±½Á”µÙÌµ¥¹Ñ•É¥ÑäÅÕ•ÍÑ¥½¸¥Ì½Ù•É•‰ä•á¥ÍÑ¥¹œM•¹Ñ¥¹•°´äÉ•ÁÉ•Í•¹Ñ…Ñ¥Ù•Ìì…¹ä‘¥™™•É•¹ÐÉ…¹­¥¹œÝ½Õ±Ñ¡•É•™½É”‰”AI=A=M1}=91e€…¹¥ÌÕ¹¹••ÍÍ…Éä…ÐÑ¡¥ÌÁ½¥¹Ð¸((ŒŒEÕ•ÍÑ¥½¹Ì™½È5…¥¹±¥¹”€¼MÑ…Ñ¥Œ±…¹”()Q¡”µ…¡¥¹”µÉ•…‘…‰±”Á…­•ÐM5}91eM%M}}%MI%5%9Q%9}EUMQ%=9M}XÄ¹©Í½¹€™É••é•ÌÑ•¸ÅÕ•ÍÑ¥½¹ÌÝ¥Ñ¡½ÕÐÍÕÁÁ±å¥¹œ5…¥¹±¥¹”…¹ÍÝ•ÉÌ¸!¥¡•ÍÐµÙ…±Õ”¥Ñ•µÌ…É”è((Ä¸M1P=™™Í•ÐÉ•ÍÕ±Ð€´øÕÉÍ½È½Í••¬‘¥É•Ð‘•˜µÕÍ”¥¸€ÁàÄÐÁÄÜÕÁ€¸(È¸…¹Ù…ÌÍ5½‘•±1½…‘•È½¹É•Ñ”±½…µ•Ñ¡½€´øÑåÁ•=¡Õ¹­•±±%µÁ½ÉÑ•ÉQ€‘¥ÍÁ…Ñ ¸(Ì¸½¹”ÑåÁ•¥µÁ½ÉÑ•È€´ø•á…ÐÉ•…‘•ÈÝ¥‘Ñ ½•¹‘¥…¸½½Õ¹Ð€´ø‘•ÍÑ¥¹…Ñ¥½¸µ•µ‰•È½½¹Ñ…¥¹•È¸(Ð¸™¥ÉÍÐ‘½Ý¹ÍÑÉ•…´½¹ÍÕµ•È½˜Ñ¡”¹•Ü€ÄØµ‰åÑ”½‰©•Ð™¥•±¸(Ô¸‘¥É•Ð¥‘•¹Ñ¥Ñä‰É¥‘”‰•ÑÝ••¸Ñ¡”€ÐÀµ‰åÑ”!9-áÑ„­•ä…¹ME1¥Ñ”áÑ•É¹…±%¸((ŒŒU¹É•Í½±Ù•€¼…Ñ•Ì((´€¹Íµ€•á…Ð¡…¹‘±•ÈèU9IM=1Y(´áÑ•É¹…±¡Õ¹¬ÅÕ•ÉäµÉ•ÍÕ±Ð€´øÍ••¬èU9IM=1Y(´!9-áÑ„­•ä€´øáÑ•É¹…±%èU9IM=1Y(´5½‘•±…Ñ„±½½­ÕÀ€¼…¹Ù…ÌÍ±½…•¹ÑÉäèU9IM=1Y(´aA1%%Q}MI%1%iI}%1}I€è€¨©U9IM=1Y¨¨(´aA1%%Q}%9QI91}5=1}=9MQIUQ%=9€è€¨©U9IM=1Y¨¨(´=9QI=11}%aQUI}Q=}=9MU5I}5Q!€è€¨©U9IM=1Y¨¨(´•½µ•ÑÉä½¥¹‘•à½µ…Ñ•É¥…°½UX½‰½¹”½Ý•¥¡ÐÍ•µ…¹Ñ¥Ìè€¨©U9IM=1Y¨¨(´Í•µ…¹Ñ¥ŒÁÉ½µ½Ñ¥½¸è€¨¨À¨¨(´	±•¹‘•È•µ¥Ðè€¨©	1=-¨¨(´ÉÕ¹Ñ¥µ”è€¨©™…±Í”¨¨(´5=1H…Ñ¥½¹Ìè€¨¨À¨¨(´]½É­•È½…¹…Éäè€¨¨À¨¨(´I%<´ÈØ½µ…¥¹±¥¹”µÕÑ…Ñ¥½¹Ìè€¨¨À¨¨((ŒŒI•ÍÕ±Ð()´ÀØä…‘Ù…¹•ÌÑ¡”ÍÑ…Ñ¥Œ½¹ÍÕµ•È™É½¹Ñ¥•È™É½´ƒŠqÁÉ¥Ù…Ñ”¥¹ÍÑÉÕÑ¥½¸µ±•Ù•°Á…­…”Õ¹…Ù…¥±…‰±—ŠtÑ¼€¨©ÑÝ¼½¹™¥Éµ•½¹Ñ…¥¹•Èµ±…å•È‘¥É•ÐÉ•…½‘…Ñ„µ™±½Ü•‘•Ì¨¨…¹„ÍÑÉ½¹•ÈáÑ•É¹…±¡Õ¹¬‘¥ÍÉ¥µ¥¹…Ñ¥½¸Ñ…É•Ð¸%Ð‘½•Ì€¨©¹½Ð¨¨±…¥´„ÁÉ½½˜µÉ…‘”Í•µ…¹Ñ¥Œ‰¥¹‘¥¹œ¸Q¡”É•Á½ÉÐ¥ÌÍ•…±•™½È±…Ñ•È¥¹‘•Á•¹‘•¹Ð½µÁ…É¥Í½¸½¹±ä…™Ñ•È¥ÑÌ¡…Í¡•Ì…É”É•½É‘•¸