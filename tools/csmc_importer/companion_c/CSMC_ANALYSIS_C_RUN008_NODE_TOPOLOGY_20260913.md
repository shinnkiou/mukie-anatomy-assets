# CSMC ANALYSIS COMPANION C — RUN C-008 — NodeName / ModelNodeInfo / NextIndex relation

Status: STATIC SIDE-LANE PASS / SCHEMA-ONLY TOPOLOGY / ZERO MODELER / ZERO RUNTIME

## QUESTION
What structural relation is supported among `NodeName`, `ModelNodeInfoCount`, `ModelNodeInfoFirstIndex`, and `ModelNodeInfo3D.NextIndex` without treating latent ParamScheme schema as current payload layout?

## PROBE
Cross-checked the fixed-snapshot `CLIP_3D_PARAMSCHEME_FINDINGS_20260903` and `CLIP_3D_SCHEMA_MAP_FINDINGS_20260903`. Current target has no live `ModelInfo3D` / `ModelNodeInfo3D` rows, so every relation in this run remains `SCHEMA_ONLY`.

Recovered structural roles:
- `ModelInfo3D.ModelNodeInfoCount`: cardinality metadata.
- `ModelInfo3D.ModelNodeInfoFirstIndex`: traversal seed / reference to `ModelNodeInfo3D`.
- `ModelNodeInfo3D.NextIndex`: self-link from one node record to another.
- `ModelNodeInfo3D.NodeName`: TEXT property on the node record.

Semantics-free graph:

`ModelInfo3D descriptor {count, first_index}`
`  -> ModelNodeInfo3D node`
`     -> name_property: NodeName`
`     -> next_index: ModelNodeInfo3D node`

## INTERPRETATION
The historical SQL-side node representation is best modeled as a list descriptor (`count + first-index`) feeding a linked node chain (`NextIndex`), with `NodeName` as record data rather than an ownership/pointer field. Explicit `FirstIndex` and `NextIndex` make a pure contiguous-array assumption unnecessary and currently unsupported. The exact termination/sentinel convention is not known from the static schema alone.

## NEW INFORMATION
- Historical hierarchy metadata separates list cardinality, traversal seed, self-link, and node naming into distinct structural roles.
- `NodeName` can be represented in IR as a node property without assigning bone/joint semantics.
- A semantics-free linked-chain topology is supported even though the current target does not instantiate these legacy tables.

## CLOSED HYPOTHESES
- `NodeName` is an owner pointer or traversal key: REJECTED; it is defined as TEXT data on the node record.
- `ModelNodeInfoCount` alone proves a contiguous node array: REJECTED as the sufficient model because explicit FirstIndex and NextIndex relations coexist.
- The latent `ModelNodeInfo3D` chain is a live hierarchy table in the current target: REJECTED.

## CONFIDENCE CHANGES
- Historical SQL node-list topology (`count + first + next`): MEDIUM-HIGH -> VERY HIGH.
- `NodeName` as per-node textual property: HIGH -> VERY HIGH.
- Exact traversal termination/sentinel rule: remains UNKNOWN.
- Mapping of this historical topology onto current external `scene` or `catalog_character` payload bytes: remains UNRESOLVED / VERY LOW.

## NEXT QUESTION
Does the quaternion-like rotation candidate have independent evidence beyond the single active count-4 identity vector, and how far can that evidence be promoted without claiming current node byte layout?

## Guardrails
- Schema registration is not live usage.
- SQL hierarchy topology is not current scene BLOB layout proof.
- No bone semantic promotion is made from `NodeName` alone.
