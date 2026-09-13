# CSMC ANALYSIS COMPANION C — RUN C-014 — BindingEvidence promotion contract

Status: STATIC SIDE-LANE IMPLEMENTATION PASS / 4 TESTS PASS / ZERO RUNTIME DISPATCH

## QUESTION
What minimum current-payload facts are sufficient to add a codec-binding edge, and what additional facts are required for semantic promotion, without dispatching any MODELER/runtime work from this side lane?

## PROBE
Implemented:
- `csmc_analysis_c_binding_evidence.py`
- `csmc_analysis_c_binding_evidence.schema.json`
- synthetic tests for the promotion ladder.

Binding levels:
1. `NO_BINDING`
2. `CANDIDATE_CODEC_BINDING`
3. `CONFIRMED_CODEC_BINDING`
4. `CONFIRMED_SEMANTIC_BINDING`

Current-payload codec binding contract:
- `current_payload_mapping = true`
- a bounded current region identifier exists
- referenced codec has `CONFIRMED_ENCODING`
- at least two exact decode fits are observed for the same structural role
- same structural-role recurrence is established

A single exact fit on an opaque current region is intentionally candidate-only.

Semantic promotion additionally requires:
- controlled differential;
- known-input correlation;
- localized effect;
- explicit semantic slot.

## TEST RESULT
4/4 PASS:
- zero fit -> NO_BINDING;
- one exact fit -> CANDIDATE_CODEC_BINDING;
- recurrent exact fits with confirmed codec -> CONFIRMED_CODEC_BINDING;
- semantic promotion remains blocked until controlled differential + known-input correlation + localized effect + semantic slot are all present.

No runtime job is requested or emitted by the classifier.

## INTERPRETATION
C-013 identified the missing edge; C-014 now defines the exact admission rule for that edge. This lets the side lane remain isolated while being ready to ingest future evidence from any authorized source without relaxing standards or rewriting parser architecture.

The contract intentionally separates **codec binding** from **semantic binding**. Knowing how bytes decode is not enough to claim what the decoded values mean.

## NEW INFORMATION
- `CURRENT_PAYLOAD_BINDING_EDGE` is now represented by a machine-checkable evidence contract.
- A single accidental-looking exact fit cannot silently become a confirmed decoder binding.
- Codec confirmation and semantic confirmation now have separate promotion thresholds.
- Future evidence can be ingested without changing C-012 parser stages or touching mainline systems.

## CLOSED HYPOTHESES
- One exact decode fit in an opaque current payload is sufficient for confirmed codec binding: REJECTED.
- Confirmed codec binding is sufficient for semantic promotion: REJECTED.
- A controlled differential without known-input correlation/localized effect is sufficient for semantic promotion: REJECTED.
- The side lane must dispatch runtime work in order to define the evidence gate: REJECTED.

## CONFIDENCE CHANGES
- binding-edge acceptance criteria: UNKNOWN -> VERY HIGH / machine-defined.
- accidental codec overpromotion risk: materially reduced by recurrent-role requirement.
- accidental semantic overpromotion risk: materially reduced by separate differential/correlation/localization gate.
- current real +965 binding state: remains NO_BINDING.

## NEXT QUESTION
Audit the existing static corpus against the new BindingEvidence contract and produce a **gap vector** for the nearest current candidates: which exact contract fields are missing for counted-BE codec -> +965, quaternion candidate -> current node transform, and historical node topology -> current hierarchy?

## Guardrails
- This run defines acceptance criteria only; it does not create real binding evidence.
- Synthetic test promotion never mutates real semantic slots.
- No MODELER/runtime/Worker/Canary/Control Gate/RIO-26 action.
