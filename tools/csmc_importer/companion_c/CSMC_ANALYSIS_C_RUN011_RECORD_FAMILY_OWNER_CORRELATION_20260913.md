# CSMC ANALYSIS COMPANION C — RUN C-011 — record family vs owner/container position correlation

Status: STATIC SIDE-LANE PASS / COARSE ROUTE CORRELATION ONLY / ZERO MODELER / ZERO RUNTIME

## QUESTION
How strongly can the five +965 semantics-free record families be correlated with the owner/container graph: only to the character external payload surface, or also to an internal section/supergroup owner position?

## PROBE
Joined only already-established public-safe provenance:

1. C-006 live route:
   `Canvas3DModelLoader.ModelData -> external ref -> CHNKExta -> DATA2 kind=catalog_character`.
2. +965 record analysis provenance:
   all 22 complete 48/49-qword record instances were derived from comparison of the `.clip` embedded `catalog_character` payload against the saved CSMC `character` payload.
3. C-002 families:
   five joint structural families over `length_blocks + preserve_signature`.
4. Existing +965 grouping:
   four complete five-record groups each sum to 242 qwords = 1,936 bytes.

No new cadence fitting, no new +965 boundary discovery, and no +197/+195 fitting were performed.

## RESULT
A coarse route correlation is supported:

`character external container`
`  -> unresolved internal +965 regime`
`     -> semantics-free record family {RF_00..RF_04}`
`        -> unresolved child/payload zones`

The record-family corpus is therefore located on the `catalog_character/character` serialization surface, not on the independently resolved `scene` route in the evidence used here.

However:
- the scene route has not been subjected to the same record-family analysis, so character exclusivity is not proven;
- no current public-safe aggregate maps individual RF families to specific supergroup slots or a named internal section owner;
- the repeated five-record / 1,936-byte grouping is structural locality evidence, not an owner identity.

## INTERPRETATION
C-006 and C-002 can now be composed one level further without semantic naming: top-level route/container association is supported, while internal section ownership remains unresolved. This is enough for an importer IR to carry `container_route=character` on the +965 family corpus, but not enough to label an internal section, object type, mesh, bone, material, or transform owner.

## NEW INFORMATION
- All five currently observed record families and all 22 record instances have provenance within the character external payload comparison surface.
- The `scene` route is a separate live top-level route but is not part of the current +965 family corpus.
- A minimal hierarchy can safely extend from `character container` to `unresolved +965 regime` to `record family`, while leaving internal section owner blank.
- Four 1,936-byte five-record supergroups provide locality/grouping evidence but do not identify a semantic or serializer owner.

## CLOSED HYPOTHESES
- Current +965 record families are uncorrelated with any owner/container route: REJECTED at the coarse top-level route; character provenance is established.
- Existing evidence assigns the five families to the live `scene` route: REJECTED for the analyzed corpus.
- The five-record supergroup periodicity by itself identifies an internal section/owner type: REJECTED.
- Family ID or preserve signature currently determines a specific owner/container position: REJECTED / unsupported by the retained aggregate data.

## CONFIDENCE CHANGES
- +965 corpus belongs to the character external payload surface: MEDIUM -> VERY HIGH.
- Character route is exclusive location of this grammar across all CELSYS payloads: remains UNKNOWN.
- Five-record supergroups represent a local structural grouping: HIGH -> VERY HIGH.
- Named/semantic internal section owner for RF_00..RF_04: remains UNRESOLVED / VERY LOW.
- Full hierarchy `container -> section -> record family -> child blob`: partial support only; `container -> unresolved regime -> record family` is HIGH, semantic section/child roles remain UNPROVEN.

## NEXT QUESTION
Can C-003/C-005/C-006/C-011 now be composed into a minimal parser skeleton with ordered stages `route resolution -> structural regime/record normalization -> typed codec annotation -> semantic gate`, where Blender geometry emission is mechanically refused until geometry/index semantics reach independently evidenced CONFIRMED status?

## Guardrails
- This is provenance correlation, not semantic ownership proof.
- No family is named Mesh/Index/Bone/Weight/Transform/Material.
- No mainline branch, runtime, MODELER, Worker, Canary, Control Gate, or RIO-26 state was touched.
