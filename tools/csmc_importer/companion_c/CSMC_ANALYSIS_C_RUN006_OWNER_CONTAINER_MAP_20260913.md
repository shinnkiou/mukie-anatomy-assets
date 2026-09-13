# CSMC Analysis Companion C — Run C-006 Owner / Container Route Map

## QUESTION
Can existing static `ParamScheme` and live external-reference evidence be combined into a semantics-free owner/container hierarchy map that tells the importer which payload surface routes to character data vs scene data without asserting mesh/bone encoding?

## HYPOTHESIS
The durable metadata is sufficient to classify edges into live-resolved, schema-only, and unresolved-route classes, allowing the importer to select the correct payload surface before any semantic decoder runs.

## PROBE
`csmc_analysis_c_owner_container_map.py` validates graph edges as exactly one of `LIVE_RESOLVED_EDGE`, `SCHEMA_ONLY_EDGE`, or `UNRESOLVED_ROUTE`. A live-resolved edge must have source/relation/target/target-kind. A schema-only edge must remain explicitly schema-only. An unresolved route is forbidden from claiming a target kind.

## SYNTHETIC TEST
3/3 PASS:
1. a live resolved route becomes an importer route while payload semantics stay `UNRESOLVED`;
2. a schema-only edge cannot masquerade as live;
3. an unresolved route cannot claim a target kind.

## REAL AGGREGATE RESULT
Edge counts: live-resolved=2, schema-only=3, unresolved=2.

### Live resolved importer routes
- character: `Canvas3DModelLoader.ModelData -> external ref -> CHNKExta -> CLIP_STUDIO_3D_DATA2 kind=catalog_character`
- scene: `Manager3DOd.SceneData -> external ref -> CHNKExta -> CLIP_STUDIO_3D_DATA2 kind=scene`

Both are real target routes, while byte semantics inside each payload remain `UNRESOLVED`.

### Schema-only historical hierarchy
- `Manager3D.ModelInfoFirstIndex -> ModelInfo3D`
- `ModelInfo3D.ModelNodeInfoFirstIndex -> ModelNodeInfo3D`
- `ModelNodeInfo3D.NextIndex -> ModelNodeInfo3D`

### Unresolved route candidates
- `ModelData3D.Layer3DModelData`
- `Canvas3DModelBank.BankData`

## INTERPRETATION
The importer can separate container routing from payload decoding: parse `.clip` / SQL refs -> resolve CHNKExta / DATA2 -> dispatch by confirmed route/kind -> run generic structural/codec probes -> keep mesh/bone/material/index semantics evidence-gated. Route ownership is not proof of serializer implementation ownership or internal semantic layout.

## NEW INFORMATION
- Two real target payload routes are statically distinguishable before semantic decoding: character and scene.
- The legacy node hierarchy can be preserved as a schema-only topology dictionary without contaminating live evidence.
- The importer can reject/park unresolved routes instead of guessing.

## CLOSED HYPOTHESES
- `Character and scene data must be treated as one undifferentiated CELSYS payload surface` — REJECTED.
- `Legacy ModelInfo3D / ModelNodeInfo3D relationships are live in the current target` — REJECTED.
- `A resolved external kind proves internal mesh/bone encoding` — REJECTED.

## CONFIDENCE CHANGES
- `pre-semantic route dispatch is viable`: MEDIUM -> VERY HIGH.
- `Canvas3DModelLoader.ModelData is the confirmed character external route`: HIGH -> VERY HIGH.
- `Manager3DOd.SceneData is the confirmed scene external route`: HIGH -> VERY HIGH.
- `legacy node chain is useful as topology hint`: MEDIUM -> HIGH.
- `unresolved Layer3DModelData/BankData target role`: remains UNKNOWN.

## NEXT QUESTION
Can Runs C-001 through C-006 be composed into a reusable minimal parser skeleton that performs route resolution -> structural normalization -> codec annotation while emitting no Blender geometry until semantic evidence is sufficient?
