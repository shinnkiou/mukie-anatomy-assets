# CSMC ANALYSIS COMPANION C — RUN C-010 — matrix / index / normalized-weight evidence audit

Status: STATIC SIDE-LANE NEGATIVE-EVIDENCE PASS / ZERO MODELER / ZERO RUNTIME

## QUESTION
Do existing static artifacts contain direct evidence for a 4x4 matrix layout, mesh index representation, or normalized skin weights, or are similarly named SQL/index/bone fields only semantic traps?

## PROBE
Audited the fixed-snapshot numeric evidence inventory, ParamScheme findings, schema map, and integration-probe claim boundary. No new payload scan was performed.

### matrix4x4
Existing names include transform-related fields/BLOBs such as `ModelRootNodeTranslation`, `ModelSkeletonRootNodeTranslation`, `ModelNodeRotation`, `PartsTransform`, and `BBox`. None of the examined evidence establishes a 16-element array, row/column order, affine last row/column, or any 4x4 matrix serialization.

Direct matrix4x4 evidence: **0**.

### mesh index representation
Historical SQL topology uses `ModelNodeInfoFirstIndex` and `NextIndex` INTEGER fields. Those values are navigation indices for latent SQL node records. No examined artifact establishes a vertex/face index buffer, uint16/uint32 element width, primitive topology, or index-count relation.

Direct mesh-index representation evidence: **0**.

### normalized skin weights
`DessindollBoneInfo` and other bone-related BLOB names exist in ParamScheme, but no examined artifact provides per-vertex weights, influence counts, numeric weight vectors, normalization checks, or sum-to-one evidence.

Direct normalized-weight evidence: **0**.

## INTERPRETATION
This run closes three naming-based false shortcuts. SQL `Index` fields are topology/navigation metadata, not evidence of mesh index buffers. Transform-related names do not imply matrix4x4 storage. Bone-related BLOB names do not imply skin-weight layout or normalization. The correct importer state remains explicit `NO_DIRECT_EVIDENCE` for all three categories.

## NEW INFORMATION
- `FirstIndex/NextIndex` evidence is positively classified as historical SQL traversal structure, which makes its use as mesh-index evidence specifically invalid.
- Existing transform field names provide semantic categories but no matrix dimensionality/layout evidence.
- Existing bone BLOB names provide a search target but no numeric weight grammar or normalization evidence.

## CLOSED HYPOTHESES
- `FirstIndex` / `NextIndex` names materially support uint16/uint32 mesh index-buffer decoding: REJECTED.
- Transform/rotation/translation/BLOB names are sufficient evidence for a 4x4 matrix serializer: REJECTED.
- `DessindollBoneInfo` naming is sufficient evidence for normalized skin weights: REJECTED.

## CONFIDENCE CHANGES
- matrix4x4 current evidence level: NO_DIRECT_EVIDENCE -> NO_DIRECT_EVIDENCE, confidence in the negative classification VERY HIGH.
- uint16/uint32 mesh index current evidence level: NO_DIRECT_EVIDENCE -> NO_DIRECT_EVIDENCE, confidence in the negative classification VERY HIGH.
- normalized skin-weight current evidence level: NO_DIRECT_EVIDENCE -> NO_DIRECT_EVIDENCE, confidence in the negative classification VERY HIGH.
- SQL node indices as hierarchy-navigation metadata: HIGH -> VERY HIGH.

## NEXT QUESTION
How strongly can the five +965 semantics-free record families be correlated with the owner/container graph: only to the character external payload surface, or also to an internal section/supergroup owner position?

## Guardrails
- Negative evidence is not a proof that these structures do not exist; it is a statement that current examined artifacts do not support decoding them.
- No semantic slot is promoted.
