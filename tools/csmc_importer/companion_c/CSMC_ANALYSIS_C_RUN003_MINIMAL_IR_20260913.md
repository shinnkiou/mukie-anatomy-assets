# CSMC Analysis Companion C — Run C-003 Minimal Semantics-Free Importer IR

## QUESTION
Can current confirmed structural evidence be represented in one importer-oriented intermediate schema without prematurely assigning geometry/index/transform/material/hierarchy semantics?

## HYPOTHESIS
A two-layer IR can preserve current structure losslessly if structural grammar and semantic claims are separate: boundary class + record layout/family axes in the structural layer, and explicitly unresolved semantic slots in the semantic layer.

## PROBE
`csmc_analysis_c_minimal_ir.py` builds and validates `csmc_analysis_c_minimal_ir_v1` from the aggregate outputs of Run C-001/C-002 plus the already-durable q21..27 control-zone grammar. It reads no raw model/payload bytes.

A companion JSON Schema, `csmc_analysis_c_minimal_ir.schema.json`, documents the machine-facing contract.

## SYNTHETIC TEST
Three tests PASS:
1. valid semantics-free IR is accepted;
2. a semantic slot cannot be marked `CONFIRMED` without explicit evidence IDs;
3. aggregate IR rejects `raw_payload_bytes_embedded=true`.

## REAL AGGREGATE RESULT
The real aggregate instance validates with:
- boundary classes: `LOCAL_EXTINCTION_CANDIDATE`, `MIXED_REUSE_REPACK_CANDIDATE`;
- 3 current boundaries;
- 5 current joint record families;
- independent record axes: `length_blocks`, `preserve_signature`;
- qword size = 8 B;
- observed record lengths = 48 / 49 qwords;
- stable prefix = q0..20;
- control zone = q21..27;
- fixed rewrite = q22/q23;
- fixed preserve = q25/q26;
- conditional = q21/q24/q27;
- rewrite tail begins q28;
- geometry/index/transform/material/hierarchy = all `UNRESOLVED` with confidence 0.0.

No payload bytes are embedded in the IR.

## INTERPRETATION
Yes: the currently confirmed static evidence is sufficient to define a useful preprocessing/interchange layer for a future Blender importer without making any semantic type claim. This separates two problems that should not be conflated:

1. **structural parser** — locate/regroup sections and record families using correspondence grammar;
2. **semantic decoder** — later prove which structures carry geometry/index/transform/material/hierarchy data.

The structural layer can now stabilize even while semantic decoding remains open. Later evidence can attach semantic labels to existing IR nodes rather than rewriting the low-level parser.

This is **not** a real mesh extractor and does not prove Blender import.

## NEW INFORMATION
- A lossless current-evidence IR exists using two independent layers: structural grammar and semantic status.
- Current importer work can proceed on section/record normalization without waiting for semantic decoding.
- The minimal structural contract now requires at least: boundary class, qword record layout, `length_blocks`, and `preserve_signature`.
- Semantic uncertainty can be machine-enforced rather than left as prose only.

## CLOSED HYPOTHESES
- `Importer schema must wait until Mesh/Index/Material/etc. are identified` — REJECTED.
- `Structural and semantic record type should be a single enum` — REJECTED for the current evidence model.
- `A useful importer IR requires embedding raw proprietary payload bytes` — REJECTED for the aggregate structural layer.

## CONFIDENCE CHANGES
- `semantics-free structural IR is viable now`: LOW -> HIGH.
- `structural parser can be developed independently of semantic decoder`: MEDIUM -> HIGH.
- `current evidence is sufficient for real Blender mesh import`: remains VERY LOW / UNPROVEN.
- geometry/index/transform/material/hierarchy semantic assignments: remain UNRESOLVED.

## NEXT QUESTION
Do existing historical controlled-pair artifacts (`P3-CONTROL/CAMERA/BONE/TRANS/VARIANT/MATERIAL`) contain any already-recorded cross-instance differential evidence that can attach a semantic candidate to this IR without requesting a new runtime or MODELER operation?
