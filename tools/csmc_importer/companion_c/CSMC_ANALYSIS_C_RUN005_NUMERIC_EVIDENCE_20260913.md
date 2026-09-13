# CSMC Analysis Companion C — Run C-005 Static Numeric-Pattern Evidence Audit

## QUESTION
Do existing static code/findings already contain public-safe numeric-pattern evidence that narrows importer decoding without repeating closed byte-search experiments or requesting new runtime/MODELER observations?

## HYPOTHESIS
At least one CELSYS numeric grammar is already proven strongly enough to become a reusable codec candidate, while semantic mappings to CSMC record families remain unproven.

## PROBE
`csmc_analysis_c_numeric_evidence_matrix.py` classifies pre-existing public-safe evidence into `CONFIRMED_ENCODING`, `SEMANTIC_CANDIDATE`, `SCHEMA_HINT`, `NO_DIRECT_EVIDENCE`, or `CONFIRMED_SEMANTIC`.

A codec is confirmed only when an active observed field has an exact-length fit and an explicit decoder rule. Semantic promotion is stricter: controlled differential + current-payload mapping + known-input correlation are all required. No raw target payload was rescanned in this run.

## SYNTHETIC TEST
3/3 PASS:
1. exact active codec evidence confirms an encoding but does not promote a semantic slot;
2. a schema hint is not treated as current-payload semantics;
3. semantic promotion requires controlled current-payload known-input correlation.

## REAL AGGREGATE RESULT
11 evidence entries:
- `CONFIRMED_ENCODING`: 4
- `SEMANTIC_CANDIDATE`: 1
- `SCHEMA_HINT`: 2
- `NO_DIRECT_EVIDENCE`: 4
- `CONFIRMED_SEMANTIC`: 0

### Confirmed encodings
1. count + numeric array grammar in active `.clip` `Manager3DOd` BLOBs: u32 big-endian element count plus exactly `count*8` BE float64 or `count*4` BE float32; 7 exact-length fields and no trailing bytes required.
2. BE float64: 6 exact active fields.
3. BE float32: 1 exact active field.
4. external-reference/container routing: live SQL external-reference strings resolve to `CHNKExta` entries and CELSYS `CLIP_STUDIO_3D_DATA2` metadata. This is container/reference-graph evidence, not bone/mesh semantics.

### Semantic candidate
- `MultiViewPresetCameraRotate` is a named count-4 BE-f64 active field decoding to `[1,0,0,0]`.
- latent `ModelNodeInfo3D` schema names `NodeRotationR` + `NodeRotationVX/VY/VZ`.
- Together these are strongly consistent with scalar-plus-vector quaternion usage somewhere in CELSYS 3D state.
- This remains candidate because there is no controlled known-rotation differential mapping the current scene/CSMC payload to these components.

### Schema hints
- historical node list: `ModelNodeInfoCount` + `ModelNodeInfoFirstIndex -> ModelNodeInfo3D` + `NextIndex`.
- `ModelNodeInfo3D.NodeName` is TEXT.
- Current target does not instantiate live `ModelInfo3D/ModelNodeInfo3D`, so these are dictionaries/hints rather than current blob layout proof.

### No direct static evidence found in the examined fixed snapshot
- float16
- uint16/uint32 index buffer representation
- matrix 4x4 representation
- normalized skin weight representation

## INTERPRETATION
The static lane now has a reusable numeric codec catalog, but still no justified mapping from the +965 record families or +197/+195 child unit to geometry/index/transform/material/hierarchy.

This materially helps importer design: a decoder can expose generic typed candidates (`counted_be_f64`, `counted_be_f32`, external-ref route) while leaving semantic binding separate and evidence-gated. Codec evidence may be `CONFIRMED_ENCODING`; record/section semantic role remains `UNRESOLVED` unless independent correlation exists. No semantic slot in the C-003 minimal IR is promoted by this run.

## NEW INFORMATION
- CELSYS active `.clip` numeric serialization has at least one confirmed reusable grammar: u32be count + exact BE-f64/BE-f32 array.
- Quaternion-like scalar+vector rotation is a strong semantic candidate, not a confirmed current-payload mapping.
- Container external-reference resolution is confirmed separately from payload semantics.
- Existing fixed-snapshot evidence provides no direct support for float16, index-buffer integers, matrix4x4, or normalized weights.

## CLOSED HYPOTHESES
- `No numeric serializer grammar is known until a new runtime pair is captured` — REJECTED.
- `A confirmed numeric codec automatically identifies the semantic role of +965 records` — REJECTED.
- `ParamScheme latent node fields prove current scene/CSMC byte layout` — REJECTED.

## CONFIDENCE CHANGES
- `counted BE numeric array is a reusable CELSYS codec`: MEDIUM -> VERY HIGH.
- `CELSYS rotation state may use quaternion-like R+VXYZ`: MEDIUM -> MEDIUM-HIGH.
- `+965 record family is transform/bone data`: remains VERY LOW / UNPROVEN.
- `geometry/index/material/hierarchy semantic slots can be promoted now`: remains VERY LOW.
- `generic typed-codec stage belongs before semantic decoding in importer`: MEDIUM -> HIGH.

## NEXT QUESTION
Can the existing static `ParamScheme` and live external-reference graph be combined into a semantics-free owner/container hierarchy map that tells the importer which payload surface owns character data vs scene data, without asserting mesh/bone encoding?
