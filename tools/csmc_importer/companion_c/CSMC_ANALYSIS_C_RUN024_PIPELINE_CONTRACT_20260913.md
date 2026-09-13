# Companion C — Run C-024

## QUESTION
Can the current Companion C gates be composed into one end-to-end static pipeline with explicit one-way transitions and no implicit evidence promotion?

## HYPOTHESIS
Intake, structural parsing, codec binding, semantic binding, and Blender readiness should be evaluated independently and in order.

## PROBE
Added `csmc_analysis_c_pipeline_contract.py`.

Pipeline states:
- `REJECTED_INPUT`
- `INTAKE_ONLY`
- `STRUCTURAL_ONLY`
- `CODEC_BOUND`
- `SEMANTIC_PARTIAL`

Readiness rules:
- mesh emission requires independently confirmed `geometry` and `index` semantic slots.
- scene-aware emission additionally requires independently confirmed `transform` and `hierarchy` semantic slots.
- material readiness is independent enrichment and does not back-propagate into other slots.

## SYNTHETIC TEST
5/5 PASS:
- rejected intake remains rejected
- valid structural IR without binding -> `STRUCTURAL_ONLY`
- confirmed codec binding without semantics -> `CODEC_BOUND`
- geometry+index confirmation opens mesh readiness only
- geometry+index+transform+hierarchy opens scene readiness

## REAL AGGREGATE RESULT
This run defines the pipeline contract only. No real semantic slot was promoted.

## NEW INFORMATION
- C-012/C-014/C-022/C-023 can be composed into a single deterministic gate order.
- Codec confirmation and semantic confirmation are mechanically non-equivalent.
- Mesh readiness and scene readiness can be separated, preventing transform/hierarchy uncertainty from contaminating geometry/index evidence and vice versa.

## CLOSED HYPOTHESES
- Accepted intake may imply codec binding: REJECTED.
- Confirmed codec binding may imply semantic binding: REJECTED.
- Material confirmation should unlock mesh or scene readiness: REJECTED.
- Scene readiness should be a single undifferentiated boolean with no slot-level explanation: REJECTED.

## CONFIDENCE CHANGES
- end-to-end static gate architecture: HIGH -> VERY HIGH
- accidental semantic promotion risk in parser design: reduced materially
- current real semantic readiness: unchanged

## NEXT QUESTION
What exact stage does the current real Companion C evidence occupy when evaluated through this pipeline contract?
