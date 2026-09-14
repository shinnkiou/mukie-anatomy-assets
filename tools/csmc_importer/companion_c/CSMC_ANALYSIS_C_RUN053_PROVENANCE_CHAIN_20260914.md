# CSMC ANALYSIS COMPANION C — RUN C-053

## QUESTION
C-052 proves source-realization only at the public-safe metadata level, and C-051 accepts aggregate CSMC observations. Can those stages be bound so a later observation cannot silently refer to a different `.blend`, a different teacher row, or a different converted `.csmc` container?

## HYPOTHESIS
A hash chain can close that provenance gap without publishing raw payload bytes:

`source_blend_sha256 -> teacher_row_sha256 -> csmc_container_sha256 -> aggregate observation`

The chain must remain structural-only and must not promote Mesh/Index/UV/Material/Bone/Weight semantics by itself.

## PROBE / IMPLEMENTATION
Added:

- `csmc_analysis_c_c051_provenance_chain_c053.py`
- `csmc_analysis_c_c051_blender_provenance_probe_c053.py`
- `test_csmc_analysis_c_c051_provenance_chain_c053.py`
- `CSMC_ANALYSIS_C_C051_PROVENANCE_CHAIN_CONTRACT_C053_20260914.json`

The Blender probe hashes each preregistered `.blend` source and computes a deterministic `teacher_row_sha256` from public-safe teacher metadata. It does not read or write `.csmc`.

The provenance validator then requires an external conversion manifest to bind:

- exact `source_blend_sha256`
- exact `teacher_row_sha256`
- `csmc_container_sha256`
- non-empty `converter_id`

A later aggregate observation must repeat all three hashes and pass the C-050/C-051 outer-framing rule before it is admitted.

## SYNTHETIC TEST
Local fail-closed self-test: **17/17 PASS**.
Dedicated regression test file: **8/8 PASS**.

Covered failures include:

- malformed source hash
- teacher metadata mutation after fingerprinting
- raw `.blend` / raw `.csmc` field injection
- source hash swap during conversion
- teacher-row swap during conversion
- malformed CSMC hash
- missing converter id
- CSMC hash swap at analysis stage
- bad outer framing
- incomplete 7-fixture set

## PUBLIC-SAFE RESULT
`PROVENANCE_GATE_READY_INPUT_NOT_YET_ACQUIRED`

No actual C-051 `.blend` provenance manifest, conversion manifest, or new `.csmc` corpus is claimed acquired in C-053.

## NEW INFORMATION
C-051/C-052 previously had a stage-boundary provenance gap: valid teacher metadata and valid aggregate observations could, in principle, come from different physical files while retaining the same fixture id. C-053 closes that gap at the contract level with a cryptographic chain.

This does **not** confirm what the 2456-byte / 307-qword cadence means. It only makes future evidence traceable to the exact source fixture and converted container that produced it.

## CLOSED HYPOTHESES
- Fixture id alone is enough provenance across Blender -> conversion -> aggregate analysis: **REJECTED**.
- Teacher metadata identity alone proves the analyzed CSMC came from that source: **REJECTED**.
- A CSMC SHA alone proves source identity without source/teacher binding: **REJECTED**.
- Provenance continuity itself authorizes semantic promotion: **REJECTED**.

## CONFIDENCE CHANGES
- future C-051 evidence-chain integrity contract: **VERY HIGH** after synthetic fail-closed coverage.
- actual C-051 source realization: **NOT YET ACQUIRED**.
- actual conversion provenance: **NOT YET ACQUIRED**.
- 2456/307 semantic owner: unchanged, **HIGH candidate / NOT CONFIRMED**.

## SAFETY / ISOLATION
- pipeline=`STRUCTURAL_ONLY`
- semantic promotion count=0
- Blender mesh/scene emit=BLOCKED
- runtime dispatch=false
- MODELER/Worker/Canary/Control Gate actions=0
- mainline mutation=0
- RIO-26 mutation=0
- automatic integration=false
- raw/private payload publication=false

## NEXT QUESTION
When an actual C-051 teacher manifest appears, validate source realization with C-052 first, then validate the C-053 hash chain before admitting any C-051 aggregate differential. Until then, move to adjacent public-safe preparation rather than re-analyzing C-050.
