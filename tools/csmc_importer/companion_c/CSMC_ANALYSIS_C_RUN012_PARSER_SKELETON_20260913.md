# CSMC ANALYSIS COMPANION C — RUN C-012 — semantics-gated parser skeleton

Status: STATIC SIDE-LANE IMPLEMENTATION PASS / 4 TESTS PASS / ZERO MODELER / ZERO RUNTIME

## QUESTION
Can C-003/C-005/C-006/C-011 be composed into a minimal parser skeleton that performs `route resolution -> structural normalization -> typed codec annotation -> semantic gate`, while mechanically refusing Blender geometry emission until independently evidenced geometry/index semantics are CONFIRMED?

## PROBE
Implemented `csmc_analysis_c_parser_skeleton.py` and synthetic tests. Inputs are public-safe aggregate IR only:
- C-003 minimal structural IR;
- C-005 numeric evidence catalog;
- C-006 owner/container route map;
- C-011 record-family route correlation.

The skeleton deliberately has four stages:
1. route resolution;
2. structural normalization;
3. typed codec **catalog** annotation;
4. semantic gate.

A confirmed codec is not bound to a record family unless a separate binding exists. Current binding list is empty.

## TEST RESULT
4/4 PASS:
- current evidence blocks Blender geometry emit;
- confirmed codec catalog does not auto-bind to +965 record families;
- CANDIDATE geometry/index still block emit;
- synthetic CONFIRMED geometry+index slots with evidence IDs open the gate.

Current real aggregate state:
- live importer routes: 2 (`character`, `scene`);
- character regime: `REGIME_PLUS_965`, 5 families / 22 instances, internal owner UNRESOLVED;
- confirmed codec catalog entries: 4;
- record-family codec bindings: 0;
- semantic promotions from numeric evidence: 0;
- Blender geometry emit: **BLOCKED** on `geometry`, `index`.

## INTERPRETATION
The importer can now advance structurally without pretending to be a mesh importer. Route and record normalization are useful even with all geometry/index semantics unresolved. The semantic gate prevents the common reverse-engineering failure mode where a plausible codec or field name silently turns into a mesh/bone claim.

## NEW INFORMATION
- C-003/C-005/C-006/C-011 compose cleanly into an executable four-stage parser architecture.
- Confirmed codec knowledge can be retained globally while record-family bindings remain empty.
- The current character +965 regime can be represented in the parser without assigning an internal owner or semantic type.
- Blender geometry emission can be made a mechanically enforced evidence gate rather than a prose convention.

## CLOSED HYPOTHESES
- Structural parsing must wait until geometry/index semantics are known: REJECTED.
- A CONFIRMED_ENCODING entry may automatically bind to an unrelated +965 record family: REJECTED.
- CANDIDATE geometry/index status is sufficient for Blender mesh emission: REJECTED.
- The current evidence set already permits Blender geometry emission: REJECTED.

## CONFIDENCE CHANGES
- semantics-gated parser architecture viable now: HIGH -> VERY HIGH.
- current +965 codec binding availability: UNKNOWN/LOW -> CONFIRMED ABSENT in current evidence graph.
- accidental semantic leakage into Blender emission: reduced by explicit machine gate.
- real CSMC -> Blender mesh import: remains UNPROVEN / gate BLOCKED.

## NEXT QUESTION
Can any existing static evidence create a legitimate **binding edge** between a current character record family/regime and a confirmed codec or semantic schema, or is `current-payload binding` now the precise remaining evidence gap that static analysis cannot cross?

## Guardrails
- No raw payload bytes embedded.
- No MODELER/runtime/Worker/Canary/Control Gate/RIO-26 mutation.
- No mainline canonical repoll.
- Synthetic gate-open test does not promote any real semantic slot.
