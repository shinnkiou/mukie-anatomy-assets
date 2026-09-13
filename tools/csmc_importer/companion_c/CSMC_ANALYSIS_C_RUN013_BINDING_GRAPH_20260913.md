# CSMC ANALYSIS COMPANION C — RUN C-013 — current-payload binding graph

Status: STATIC SIDE-LANE PASS / 4 TESTS PASS / ZERO MODELER / ZERO RUNTIME

## QUESTION
Can any existing static evidence create a legitimate binding edge between a current character record family/regime and a confirmed codec or semantic schema, or is `current-payload binding` the precise remaining evidence gap?

## PROBE
Built a public-safe evidence graph using only C-002/C-005/C-006/C-008/C-011/C-012 results. No new byte fitting or payload rescan.

Evidence layers are deliberately distinct:
- route layer: `character`, `scene`;
- structural layer: `REGIME_plus965`, RF_00..RF_04;
- codec layer: confirmed counted-BE numeric codec observed on active Manager3DOd named BLOB fields;
- schema layer: latent ParamScheme `ModelNodeInfo3D`;
- semantic layer: geometry/index/transform/hierarchy slots.

Existing graph contains:
- `ROUTE_character -> REGIME_plus965` structural provenance edge;
- `REGIME_plus965 -> RF_00..RF_04` family edges;
- **zero** RF/regime -> confirmed codec edges;
- **zero** RF/regime -> latent node schema edges;
- **zero** RF/regime -> semantic-slot edges.

## TEST RESULT
4/4 PASS:
- current record->codec path absent;
- current record->semantic paths absent;
- character route->record family path exists;
- adding a synthetic record->codec bridge creates codec reachability but still does not create geometry/index semantic reachability.

## INTERPRETATION
The current static-analysis ceiling is now sharply defined. The problem is no longer lack of a route parser, record grammar, codec catalog, or historical semantic dictionary. The missing object is a **binding edge** showing that a bounded region/field inside the current character payload actually uses one of those codecs or corresponds to one of those schema/semantic structures.

Similarity, shared CELSYS provenance, matching arity, or suggestive names do not substitute for that edge.

## NEW INFORMATION
- There is a complete structural path from the live character route to all five current +965 record families.
- There is no current evidence path from those families to the confirmed counted-BE codec.
- There is no current evidence path from those families to `ModelNodeInfo3D` or any geometry/index/transform/hierarchy semantic slot.
- The precise static gap can be named `CURRENT_PAYLOAD_BINDING_EDGE`.

## CLOSED HYPOTHESES
- Existing counted-BE codec evidence already creates a +965 decoder binding: REJECTED.
- Latent ModelNodeInfo3D schema already creates a +965 schema binding: REJECTED.
- Character-route provenance plus CELSYS product identity is enough to bridge record families to semantics: REJECTED.
- A codec binding alone would automatically prove geometry/index semantics: REJECTED by synthetic graph test.

## CONFIDENCE CHANGES
- `CURRENT_PAYLOAD_BINDING_EDGE` as the next evidence bottleneck: MEDIUM -> VERY HIGH.
- Existing +965 -> counted-BE codec binding: LOW -> CONFIRMED ABSENT in current evidence graph.
- Existing +965 -> node schema binding: LOW -> CONFIRMED ABSENT in current evidence graph.
- Existing +965 -> geometry/index semantic binding: VERY LOW -> CONFIRMED ABSENT in current evidence graph.

## NEXT QUESTION
Define a side-lane-only `BindingEvidence` contract: what minimum static/current-payload facts would be sufficient to add a codec binding edge, and what additional facts would be required for semantic promotion, without dispatching any runtime/MODELER work?

## Guardrails
- No raw payload bytes recorded.
- No mainline canonical repoll.
- No runtime request is dispatched from this side lane.
