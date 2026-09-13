# Companion C — Run C-026

## QUESTION
Can the remaining importer gap be decomposed per semantic slot instead of treating all unresolved semantics as one undifferentiated blocker?

## PROBE
Reclassified the existing static inventory by the five importer-relevant slots: geometry, index, transform, material, hierarchy.

## REAL AGGREGATE RESULT
### geometry
No direct current evidence. Existing negative inventory contains no direct float16 geometry evidence. Missing: current-data codec binding, geometry-specific interpretation, independent semantic correlation.

### index
No direct mesh-index evidence. Historical/SQL `FirstIndex` and `NextIndex` are positively classified as hierarchy-navigation fields and therefore are not mesh-index evidence. Missing: current-data codec binding, index width/layout evidence, semantic correlation.

### transform
Not zero-evidence: active SQLite `Manager3DOd` fields already establish counted BE-f64/f32 numeric encodings, and rotation has a quaternion-like candidate. However these are not bound to the current model record/regime. Missing: current model binding and independent semantic correlation.

### material
No direct material-bearing region or material codec is identified in the current Companion inventory.

### hierarchy
Container/reference routing is structurally confirmed. Historical schema provides count+first-index+NextIndex and NodeName hints. What remains absent is a current live model-node chain and a binding from the current record/regime to that hierarchy representation.

## NEW INFORMATION
- The five semantic slots are at different evidence depths.
- geometry/index/material are currently evidence-poor; transform/hierarchy already have useful external/schema evidence but lack current-model binding.
- The minimum mesh-emission blockers remain geometry+index; transform+hierarchy are additional scene-awareness blockers; material is independent enrichment.

## CLOSED HYPOTHESES
- All unresolved slots are equally unknown: REJECTED.
- Transform has no useful static evidence at all: REJECTED.
- Hierarchy has no useful static evidence at all: REJECTED.
- SQL `FirstIndex`/`NextIndex` can be reused as mesh-index evidence: REJECTED.

## CONFIDENCE CHANGES
- geometry blocker classification: HIGH
- index blocker classification: VERY HIGH
- transform evidence-depth classification: VERY HIGH
- hierarchy evidence-depth classification: VERY HIGH
- material blocker classification: HIGH

## NEXT QUESTION
Has the current fixed snapshot now reached a genuine static-analysis ceiling, and if so can that ceiling be expressed as a precise set of missing evidence edges rather than a generic “need more data” statement?
