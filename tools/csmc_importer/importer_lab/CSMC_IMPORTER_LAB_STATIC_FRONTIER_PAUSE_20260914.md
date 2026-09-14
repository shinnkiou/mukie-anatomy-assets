# CSMC Importer Lab — Static GEN0 Frontier Pause

Status: `PAUSED_WAITING_FOR_NEW_INDEPENDENT_EVIDENCE`

Trigger: three consecutive bounded GEN0 generations without validation-frontier improvement.

- Phase-7 `LOCAL_INDEX_RANGE_BLOCK`: 48/48 hard fail in the frozen raw-index family.
- Phase-8 `LOCAL_COUNT_TO_ANCHOR_EXTENT`: one TRAIN-only hit, zero VALIDATION hits, zero common formats.
- Phase-9 `LOCAL_LENGTH_CHAIN`: zero TRAIN hits, zero VALIDATION hits, zero common formats.

Decision: stop static enumeration here. This is a resource-allocation stop, not a semantic claim that all parser/serializer explanations are false.

Resume gates:
- F02 read-only 30-variant MODELER mutation oracle; or
- proof-grade direct serializer field read / destination data flow; or
- independently justified evidence that adds a new constraint axis.

Guardrails remain: `STRUCTURAL_ONLY`, semantic promotion 0, Blender emit blocked, no runtime dispatch, no Worker/Canary/STABLE/Control Gate mutation.
