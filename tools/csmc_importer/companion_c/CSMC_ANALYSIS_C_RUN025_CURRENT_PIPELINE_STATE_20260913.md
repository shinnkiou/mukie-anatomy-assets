# Companion C — Run C-025

## QUESTION
What exact stage does the current real Companion C evidence occupy under the C-024 pipeline contract?

## INPUT
Current public-safe aggregate evidence from C-001 through C-024 only. No new private data, runtime activity, MODELER interaction, Worker operation, canonical repoll, or RIO-26 mutation.

## PROBE
Instantiate the C-024 gate contract with current evidence:
- intake accepted for the existing public-safe aggregate set
- live character/scene route edges resolved
- structural IR valid
- confirmed current +965 codec binding: absent
- semantic slots geometry/index/transform/material/hierarchy: all unresolved

## REAL AGGREGATE RESULT
Current pipeline state: `STRUCTURAL_ONLY`.

Readiness:
- codec binding level: `NO_BINDING`
- binding scope: `UNCONFIRMED`
- mesh emit: BLOCKED
- scene emit: BLOCKED
- material ready: NO

Primary blockers:
1. no confirmed current-data codec binding edge from the +965 record family/regime
2. geometry semantic slot unresolved
3. index semantic slot unresolved

## NEW INFORMATION
- The current project is no longer merely “unknown format”; it has a validated structural parser layer but has not crossed the codec-binding gate.
- The exact stopping point is between structural normalization and current-data codec binding.
- Blender emission is blocked for a specific evidence reason rather than general parser incompleteness.

## CLOSED HYPOTHESES
- Current evidence is still pre-structure / intake-only: REJECTED.
- Current evidence has already reached `CODEC_BOUND`: REJECTED.
- Quaternion/schema hints are enough to mark transform semantic slot confirmed: REJECTED.
- Blender emit is blocked because routing is unresolved: REJECTED; routing is already resolved for the two live surfaces.

## CONFIDENCE CHANGES
- current stage=`STRUCTURAL_ONLY`: VERY HIGH
- main missing edge=current +965 codec binding: VERY HIGH
- geometry/index readiness: remains UNRESOLVED/BLOCKED

## NEXT QUESTION
Can the remaining importer gap be decomposed into a minimal blocker matrix for geometry/index/transform/material/hierarchy, separating “missing codec binding” from “missing semantic correlation” for each slot?
