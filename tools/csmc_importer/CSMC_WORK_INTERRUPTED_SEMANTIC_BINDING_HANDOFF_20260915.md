# CSMC WORK — INTERRUPTED SEMANTIC BINDING CAMPAIGN HANDOFF — 2026-09-15 00:41 JST

Status: `WORK_CREDIT_LIMIT_INTERRUPTED__DURABLY_RECONCILED__NO_SCIENTIFIC_PROMOTION`

Purpose: preserve the exact resumable state of the ChatGPT Work semantic-binding campaign that stopped because the Work credit limit was reached. This artifact is a restart pointer and durability record. It does **not** supersede scientific evidence gates, does not roll back Mainline, and does not treat post-interruption concurrent lane results as already integrated.

## 0. Three-way state separation

The interrupted Work session must be resumed with three distinct state classes.

### A. Current Mainline canonical pointer

- Supabase: row **218** — `CSMC_TARGETED_STATIC_EXTRACTION_INTAKE_GATE_V1_20260915`
- status: `HANDOFF_CURRENT`
- classification: `TARGETED_STATIC_INTAKE_GATE_VERIFIED_NO_NEW_EVIDENCE`
- Base44: `6aa8128c6687e989beef27a4`
- canonical GitHub read-first file: `tools/csmc_importer/CSMC_MAINLINE_04_READ_FIRST_20260914.md`
- targeted intake gate commit: `77415f789a6c3a9fa33c044bb2574eeab459b4d2`
- targeted intake CI: `34862082867` SUCCESS
- importer smoke: `34862082732` SUCCESS
- Drive intake checkpoint MD: `17qHMtLYyl9n2l4tqDG1CR6NzwGS0KjaL`
- Drive intake checkpoint JSON: `1WlGI63Ijc12Mlu1vy01MU-F0FhP3qxSK`

Row 217 is scientifically preserved but superseded as current pointer by row218.

### B. Current GitHub structural continuation after row218

Mainline branch: `csmc-importer-experimental-20260902`

Current observed HEAD at handoff time:
`db2d3c2322ce6db0a62d6bebbd68436559862579`

Commit message: `CSMC: record bounded Phase-B static ancestry addendum`

This adds a **bounded Phase-B scope refinement, not proof**:

`0x140e78810 -> 0x140e7c270 -> 0x140f5e510 -> 0x140f5ac20 -> 0x140f64600 -> 0x140f62d20 -> 0x140f650c0`

Conditional Phase-B decompile order if the primary targeted extraction remains inconclusive:
1. `0x140f5ac20`
2. `0x140f5e510`
3. `0x140e7c270`
4. `0x140e78810`

Only if factory/vtable resolution points to `0x141658300`, include its sole exported direct caller wrapper `0x1416586c0`.

This ancestry does **not** connect the chain to C02 in the exported direct-call graph and does not prove loader ownership, serializer semantics, a ModelData reader, or an internal construction path.

### C. Post-current independent lane result — NOT YET MAINLINE-INTEGRATED

Supabase row **220**:
`CSMC_ANALYSIS_C_C069_FULL_SNAPSHOT_INDEPENDENT_20260915`

Status:
`SEALED_INDEPENDENT_ANALYSIS_READY_FOR_CROSS_LANE_COMPARE`

Base44:
`6aa814d1558760c2d7131e48`

GitHub isolated branch:
`csmc-analysis-companion-c-fullsnapshot-independent-20260915`

Sealed commit:
`239c1a265c2b96ffa765b62b813bd7af53f356fe`

It independently reports two new direct container/data-flow edges:
- `DIRECT_CONTAINER_FIELD_READ_16B`
- `CHNKSQLI_LENGTH_BOUNDED_STREAM_COPY`

But it still keeps:
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION = UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`
- semantic promotion = 0
- Blender emit = BLOCKED
- runtime dispatch = false

**Do not silently merge row220 into row218/Mainline.** It must first undergo explicit cross-lane reconciliation under the same provenance/scope firewall. In particular, CHNKSQLi/ExternalChunk reads must not become ModelData serializer width evidence without a provenance-bound bridge.

Naming warning: row220 is a later independent result also labelled `C-069`; older canonical C-069 durability exists at row209. Treat this as a reconciliation/audit collision, not two automatically additive semantic events.

## 1. Interrupted Work mission and UI progress

Mission: advance current CSMC analysis from `STRUCTURAL_ONLY` toward the first proof-grade semantic binding candidate without semantic promotion or Blender production emit.

The interrupted Work UI showed:
- read back current pointers and verify snapshot provenance — completed
- Lane A: trace ModelData reader/destination chain — completed for the bounded static evidence available
- Lane B: preserve competing interpretations and negative controls — completed
- Lane C: run bounded constraint-guided hypothesis batch — the UI was still showing this lane in progress when credits stopped
- cross-lane compare only after sealed A/B reports — completed for the then-sealed A/B state
- persist reports/read back GitHub, Drive, Base44, Linear, Supabase, Library — not fully checked in the UI at interruption

However, the durable stores now show that the major campaign artifacts, the fail-closed intake gate, the Drive durability repair, and the later Phase-B scope addendum were persisted/read back. Therefore resume from durable state, not the UI spinner state.

## 2. Campaign checkpoint retained from row217

Campaign checkpoint:
`CSMC_SEMANTIC_BINDING_CAMPAIGN_CHECKPOINT_20260914_150853Z`

Base44:
`6aa81042fd57221e087734d2`

The campaign established **no proof-grade semantic binding**. It localized the evidence gap to:
1. C02 registration source `0x140d45d30`
2. runtime factory / vtable / provenance-bound indirect bridge
3. concrete reader and read/write direction
4. width / endian / count
5. destination allocation / construction
6. controlled fixture response plus negative control

Exact baseline identities:
- MODELER 1.10.13 SHA-256: `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`
- Full Snapshot SHA-256: `afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342`
- Full Snapshot: 196 files, 79,493,525 uncompressed bytes

## 3. Lane A — bounded ModelData / candidate reader findings

Confirmed C02 anchor:
- source function `0x140d45d30`
- observed registration pair `ModelData -> Canvas3DModelLoader`
- same body separately registers sibling pairs such as `BankData -> Canvas3DModelBank` and `Layer3DModelData -> ModelData3D`

Bounded lead:
- lowercase `modeldata` at `0x14195fb88`
- one exported xref at `0x140f62ec6` inside `0x140f62d20`
- adjacent strings include `model_tmp` and `RootFolder`
- `PW3DModelDataLoader` vftable label interval: `0x14195fad0 .. <0x14195fb18`
- `PWCanvas3DModelLoader` vftable label interval: `0x1417f6d30 .. <0x1417f6d78`
- each interval is 0x48 bytes / 72 bytes, compatible with 9 pointer-sized slots if the full interval is table storage
- initialized pointer values were not available in the baseline snapshot exports

Candidate call path:
- `0x140f62d20` calls `0x140f650c0` plus path/string helpers
- sole exported direct caller of `0x140f62d20`: `0x140f64600`
- `0x140f650c0` calls stream-like helpers including `0x1408c0fc0`, `0x1408c17d0`, `0x1408c1190`, `0x1408c1990`

Direct-call negative control:
- BFS from `0x140d45d30` reached 53 nodes
- BFS from `0x141657140` reached 32 nodes
- BFS from `0x141656a80` reached 31 nodes
- none reached `0x140f62d20`, `0x140f64600`, `0x140f650c0`, `0x141658300`, `0x1416586f0`

Interpretation: this excludes claiming a direct-call bridge from the exported graph. It does **not** exclude factory, vtable, callback, or provenance-bound indirect dispatch.

## 4. Lane B — competing interpretations and firewall

Competing interpretations of `0x140f62d20` remain open:
1. inbound ModelData/member extraction into temporary/model structure
2. outbound exporter/cache/temp materialization
3. generic model-package handling unrelated to C02 ownership

Required discriminator:
- body direction
- constructor/vtable ownership
- registry object creation and invocation
- provenance from C02/registry factory to the concrete reader

ExternalChunk/CHNKSQLi firewall remains mandatory:
- C-069/Companion BE-u64 and bounded stream-copy facts belong to the CHNKSQLi / ExternalChunk corridor unless provenance says otherwise
- they are not ModelData width/endian evidence by proximity
- zero direct paths are negative controls only

## 5. Lane C — bounded constraint-guided hypothesis work

Durable logical batch:
- batch size: 16
- method: constraint-guided beam + falsification + counterexample feedback
- no Classic GA
- no padding/refill
- ordering: `bridge/owner -> direction/destination -> width/endian -> count/loop/container`
- consumer evidence is a hard scope/falsification constraint, not a score bonus

Artifact:
`tools/csmc_importer/semantic_binding_campaign/CSMC_IMPORTER_HYPOTHESIS_BATCH_V1_20260914.json`

The Work UI showed Lane C still active when credits stopped. The safe handoff interpretation is:
- the bounded batch definition/artifact is durable
- no candidate is promoted merely because it survived/scored well
- do not infer that the whole Work UI lane completed beyond what the durable artifacts prove

## 6. Controlled F02 state

Private 30-mutant bundle was inspected read-only. No physical MODELER mutation observation occurred.

Durable structural facts:
- bundle SHA-256: `93b7bb5a55d862d86ada76a13473618385ec7c72d270ea97e77e5b4d298b1689`
- exact reconstructed character BLOB SHA-256: `cea288b2ebf3327263f02677bd496dc15eee85256a2c707edfa64f16538030a0`
- payload offset: 65
- logical length: 17,687
- stored length: 17,696
- proven invariant start: payload offset 3,216
- all 30 variants are one BLOB-byte XOR `0x01`

Physical state:
- F02 physical oracle: `0/30 PENDING_MANUAL_ORACLE`
- frozen Sentinel-9: `M01 -> M10 -> M13 -> M14 -> M15 -> M18 -> M22 -> M23 -> M30`
- next physical operation remains `M01`
- `M14` at offset 3216 is the highest structural information-gain proposal only; it does not reorder the frozen sequence

## 7. Targeted static extraction — current real blocker

Frozen request:
`tools/csmc_importer/semantic_binding_campaign/CSMC_TARGETED_STATIC_EXTRACTION_REQUEST_V1_20260914.md`

Fail-closed intake contract:
`tools/csmc_importer/semantic_binding_campaign/CSMC_TARGETED_STATIC_EXTRACTION_INTAKE_CONTRACT_V1.json`

Validator:
`tools/csmc_importer/semantic_binding_campaign/csmc_targeted_static_extraction_intake.py`

Required primary functions:
- `0x140f62d20`
- `0x140f64600`
- `0x140f650c0`
- `0x140f622f0`
- `0x140f63200`
- `0x140f635d0`

Required additional evidence:
- initialized pointer values, symbols and xrefs for both 9-slot vtable intervals
- constructor/destructor xrefs assigning either vftable
- trace factory helper `0x141656a80` to concrete lookup, construction and virtual invocation
- only when resolution points there, decompile `0x141658300` and `0x1416586f0`

Required proof fields include:
- source/target VA and edge kind
- exact instruction/basic block
- input stream argument
- read/write direction
- width/endian
- count source / loop bound
- allocation/resize/reserve
- destination object/type/field offset
- downstream builder
- negative control
- exact executable SHA and tool version

Passing the intake validator means only:
`INTAKE_COMPLETE_STATIC_REVIEW_REQUIRED`

It is not automatic bridge proof, serializer proof, semantic promotion, or Blender authorization.

## 8. Current proof gates

Keep these exact values until new admissible proof arrives:

- MAINLINE = `ACTIVE`
- STRUCTURAL DEVELOPMENT = `ACTIVE`
- pipeline = `STRUCTURAL_ONLY`
- semantic gate = `CLOSED`
- semantic promotion count = `0`
- `DQ-BRIDGE-LOADER-SER-01 = WAIT_FOR_BRIDGE_PROOF`
- `DQ-SER-WIDTH-01 = WAIT_FOR_PROOF`
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION = UNRESOLVED`
- geometry = `UNRESOLVED`
- index/topology = `UNRESOLVED`
- Blender production emit = `BLOCKED`
- runtime dispatch = `false`
- F02 physical oracle = `0/30 PENDING_MANUAL_ORACLE`

## 9. Durability state and the credit-limit interruption

The interrupted Work session encountered a Google Docs quota/rate-limit problem while persisting the first campaign checkpoint. That empty native document was explicitly quarantined:
`1ujbhlFwR7OamWCReQxlsT0cxYH4iuphI-6MDtFUhUZ0`
with title beginning `SUPERSEDED_EMPTY_RATE_LIMITED__...`.

Raw Drive durability repair exists and is authoritative for the campaign body:
- campaign MD: `1qh1m7910k0xHQoao-QBcmwmmrBrtiC5B`
- campaign JSON: `1_58ORbnvmErfwFYSZ2uvRp8xxMAKCXw1`

Targeted intake checkpoint:
- MD: `17qHMtLYyl9n2l4tqDG1CR6NzwGS0KjaL`
- JSON: `1WlGI63Ijc12Mlu1vy01MU-F0FhP3qxSK`

Phase-B scope addendum:
- Drive MD: `1QP29M2xxJDVbpGgDuNHV9ZCRHIll6bcU`
- Drive JSON: `1n7sxtB8O1cSdLRUAZpKcu5DYEjeUmWgE`
- GitHub commit: `db2d3c2322ce6db0a62d6bebbd68436559862579`
- smoke: `34863505346` SUCCESS

Gmail bounded audit found only GitHub/Linear notification traffic, including historical transient CI failure notifications. Later durable GitHub/Linear/Supabase success records are authoritative. No Gmail message is admitted as scientific evidence.

Google Calendar bounded audit for `CSMC` and `MODELER` over 2026-09-14 through 2026-09-16 returned no matching events; Calendar contributes no scientific evidence or scheduling constraint.

## 10. Resume order

Resume without redoing already durable work:

1. Read back Supabase row218 + this handoff + GitHub current branch HEAD.
2. Treat row220 as an independent sealed lane waiting explicit reconciliation, not as Mainline truth.
3. Obtain/receive the exact private targeted static extraction package for the stated MODELER SHA.
4. Run it through the existing fail-closed intake validator.
5. Separately review evidence for `DQ-BRIDGE-LOADER-SER-01`.
6. Only after a provenance-bound bridge is admitted, review `DQ-SER-WIDTH-01` and width/endian/count/destination.
7. Only after field proof is additionally bound to the controlled F02 bounded region may F02 candidate pruning occur.
8. Continue to destination/internal construction and independent controlled-fixture-to-consumer validation.
9. Keep semantic promotion and Blender production emit blocked until the full proof chain closes.

If the primary six-function extraction plus vtable/factory trace remains inconclusive, use the frozen Phase-B conditional ancestry order from section 0B. Do not widen to blind broad search.

## 11. Prohibited actions during resume

Do not:
- launch MODELER from this lane
- Save / Save As / Ctrl+S / trigger serialization
- hook, inject, patch, or modify MODELER
- fabricate or infer F02 runtime observations
- mutate Worker, Canary, Control Gate, Production or STABLE
- mutate RIO-26 state
- treat public `.clip` names as CSMC field proof
- treat Lab survival/score as semantic proof
- use row220 CHNKSQLi/ExternalChunk data as ModelData width without provenance
- enable Blender production emit
- promote geometry/index/UV/material/bone/weight semantics without proof-grade binding

## 12. Historical pointer separation

Supabase row219 / Base44 `6aa81490c856272b4c891ea0` is the reconstructed Mainline03 historical handoff created separately. It is audit/history only and must not replace row218 or this interrupted-Work resume state.

End of interrupted Work handoff.
