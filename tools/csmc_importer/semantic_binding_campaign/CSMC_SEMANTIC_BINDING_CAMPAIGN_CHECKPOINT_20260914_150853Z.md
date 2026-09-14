# CSMC Semantic Binding Campaign — fail-closed checkpoint

Timestamp: 2026-09-14 15:08:53 UTC

## Outcome

The campaign remains STRUCTURAL_ONLY. No proof-grade semantic binding was established. semantic_promotion remains 0; Blender production emit remains BLOCKED; MODELER runtime was not started; F02 physical oracle remains 0/30 PENDING.

The evidence gap is now bounded:

1. C02 registration source 0x140d45d30
2. runtime factory / vtable / provenance-bound indirect bridge
3. concrete reader and read/write direction
4. width, endian and count
5. destination allocation / construction
6. controlled fixture response plus negative control

No string proximity, numeric coincidence, or Lab winner was promoted.

## Canonical readback

- Snapshot SHA-256: afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342
- Snapshot: 196 files; 79,493,525 uncompressed bytes
- MODELER 1.10.13 SHA-256: 2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150
- Starting current pointer: Supabase row 214, CSMC_MAINLINE_04_DQ_SER_WIDTH_GATE_CHECKPOINT_20260914
- Canonical C-069: row 209; duplicate row 213 is audit-only
- Sealed cross-lane comparison: row 216
- Priority 0: DQ-BRIDGE-LOADER-SER-01 = WAIT_FOR_BRIDGE_PROOF
- Priority 1: DQ-SER-WIDTH-01 = WAIT_FOR_PROOF

## Lane A — Mainline evidence intake

At 0x140d45d30, C02 registers BankData → Canvas3DModelBank, ModelData → Canvas3DModelLoader and Layer3DModelData → ModelData3D through 0x141657140 → 0x141656a80. The directly observed edge is a loader-registration binding. Existing canonical EXPLICIT_MODELDATA_LOOKUP is retained, but this body alone does not prove runtime factory invocation.

New bounded lead:

- lowercase modeldata at 0x14195fb88 has one exported xref, 0x140f62ec6 in 0x140f62d20
- adjacent strings: model_tmp at 0x14195fb78 and RootFolder at 0x14195fb98
- PW3DModelDataLoader vftable label: 0x14195fad0; next metadata label: 0x14195fb18
- PWCanvas3DModelLoader vftable label: 0x1417f6d30; next metadata label: 0x1417f6d78
- each label interval is 0x48 bytes, consistent with nine pointer-sized slots if the entire interval is table storage; initialized pointers are absent from the snapshot exports
- 0x140f62d20 calls 0x140f650c0 plus path/string helpers; its only direct caller is 0x140f64600
- 0x140f650c0 calls stream-like helpers 0x1408c0fc0, 0x1408c17d0, 0x1408c1190 and 0x1408c1990

Direct-call negative control:

- BFS from 0x140d45d30 reached 53 nodes
- BFS from 0x141657140 reached 32 nodes
- BFS from 0x141656a80 reached 31 nodes
- none reached 0x140f62d20, 0x140f64600, 0x140f650c0, 0x141658300 or 0x1416586f0

This does not exclude factory, vtable, callback, or provenance-bound indirect dispatch. It excludes claiming a direct-call bridge from the exported graph.

Snapshot coverage limitation:

- 180 targeted decompiles are present
- 0x140d45d30 is present
- 0x140f62d20, 0x140f64600, 0x140f650c0, 0x141658300 and 0x1416586f0 are absent
- the connected sandbox has the snapshot but not the raw MODELER executable

Result: no EXPLICIT_SERIALIZER_FIELD_READ or EXPLICIT_INTERNAL_MODEL_CONSTRUCTION accepted.

## Lane B — Companion-independent controls

The sealed C-069 evidence remains independent:

- report SHA-256: c69210650141db74ab3fc17a835a5d42c86c840a5c31bd34abb9de38cb423bdd
- evidence SHA-256: 5901afd90b42261cc57f95508aa89c40c978ae4e4ceebee4bcc3c4cff781b5b5
- questions SHA-256: 22dde754c1e7e777ed3732a011ca63d18f7db64f6979dfb2e2db5a9fd628fb8b

C-069 found 0x141657970 → 0x140d15a90 and a direct chunk/SQLite chain including BE-u64 reads. The firewall remains:

- BE-u64 is in the CHNKSQLi / ExternalChunk corridor
- it is not ModelData serializer width without a provenance bridge
- zero direct paths is a negative control, not proof that indirect paths do not exist

Competing interpretations for 0x140f62d20:

1. inbound modeldata member extraction into model_tmp
2. outbound exporter/cache/temp materialization
3. generic model-package handling unrelated to C02 ownership

Discriminator: resolve body direction, constructor/vtable ownership, registry object creation and invocation.

## Cross-lane comparison

Comparison occurred only after independent reports were sealed. Row 216 hashes:

- Markdown: 2b5dd5e7f9b779698e64e501a3b88ca0f8c9606aa1039c5fcb0fb8e2efdfb5f4
- JSON: ffa383d24e44d1a92ab0af62d87acf9a018fcff121024bd1e0181ddf92e1ddd7

Classification:

- A: both support the exact ExternalChunk lookup fact and ModelData/Canvas3D registration binding
- B: runtime factory invocation and result-to-seek remain interpretation boundaries
- C: 0x140f62d20 is Mainline-only post-comparison evidence; Companion receives only a blind verification question
- D: direct serializer field read and fixture-to-consumer match remain unresolved in both

## Lane C — bounded hypothesis lab

Logical batch: 16. Method: constraint-guided beam + falsification + counterexample feedback. No Classic GA and no padding.

Beam order: bridge/owner → direction/destination → width/endian → count/loop/container. Consumer evidence is a hard scope constraint, not a score bonus. Machine-readable details are in CSMC_IMPORTER_HYPOTHESIS_BATCH_V1_20260914.json.

## Controlled F02 evidence

The private 30-mutant bundle was inspected read-only. No MODELER mutation observation occurred.

- bundle SHA-256: 93b7bb5a55d862d86ada76a13473618385ec7c72d270ea97e77e5b4d298b1689
- exact reconstructed character BLOB SHA-256: cea288b2ebf3327263f02677bd496dc15eee85256a2c707edfa64f16538030a0
- payload offset: 65
- logical length: 17,687
- stored length: 17,696
- proven invariant start: payload offset 3,216
- all 30 variants are exactly one BLOB-byte XOR 0x01

The reconstructed SQLite file hash differs because page serialization differs; the character BLOB itself matches exactly and is the admissible recovered unit.

Raw-payload negative observations:

- no plaintext CSFCHUNK, CHNKExta, CHNKSQLi, ModelData, Canvas3DModelLoader or SQLite signature
- prefix entropy 0..3216: 7.93464 bits/byte
- invariant-core entropy 3216..17687: 7.96760 bits/byte
- alignment extension: one byte; framing remainder: eight bytes

These reject the current plaintext-tagged-record and unbridged raw fixed-offset scalar hypotheses. They do not prove encryption, compression, or semantics.

Information-gain proposal:

- highest structural IG among Sentinel-9 positions: M14 at payload offset 3216
- reason: exact first byte of the proven invariant region; best split among prefix ownership, exact-boundary ownership and invariant-core handling
- frozen order remains M01, M10, M13, M14, M15, M18, M22, M23, M30
- M01 remains the next physical operation; M14 is proposal-only

## Rejected hypotheses

1. modeldata string xref alone proves a reader
2. C-069 BE-u64 proves ModelData width/endian
3. exported direct-call graph contains a C02 → candidate-reader bridge
4. F02 contains a plaintext tagged ModelData/CHNK record
5. high entropy proves encryption or compression
6. exact BLOB reconstruction proves semantic field identity
7. Lab survival or oracle success alone permits promotion

## Open hypotheses

1. C02 creates PWCanvas3DModelLoader and delegates via vtable to PW3DModelDataLoader
2. 0x140f64600 / 0x140f62d20 perform inbound modeldata extraction
3. the same functions instead perform outbound cache/export
4. 0x140f650c0 is a bounded transfer with unknown direction/destination
5. 0x141658300 or 0x1416586f0 is a reader with unresolved owner/provenance
6. post-bridge 16/32-bit endian and parent/local/derived/sentinel count candidates remain competing

## Next action

Run CSMC_TARGETED_STATIC_EXTRACTION_REQUEST_V1_20260914.md against the exact MODELER SHA. Close DQ-BRIDGE-LOADER-SER-01 first; only then admit width/endian/count and controlled fixture matching.

## Manual gate

One operation only: run the targeted static snapshot extension against the stated MODELER SHA and return its analysis archive.

No MODELER launch, Save, F02 physical oracle, runtime dispatch, semantic promotion, or Blender emit is authorized.