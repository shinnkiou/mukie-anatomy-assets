# CSMC P4 +197 → +195 transition-object findings — 2026-09-13

Status: **PUBLIC-SAFE STATIC MAINLINE / ZERO MODELER ACTIONS / ZERO RUNTIME JOBS**

This pass does not rescan the barrier bytes. It formalizes the already-established +197 → extinction island → +195 switch as one machine-checkable transition object and asks a narrower owner/consumer question: is the evidence more consistent with a local length-changing child inside a continuing higher-level owner, or with a section/owner routing transition?

## Inputs already verified

- container route: `character` / `catalog_character` comparison surface;
- pre-regime: `+197`;
- post-regime: `+195`;
- clip open barrier: 380 qwords;
- CSMC open barrier: 378 qwords;
- net relative-length change: -2 qwords = -16 bytes;
- both transition endpoints are exact reused qwords at their expected correspondence offsets;
- complete cross-serialization aligned-qword extinction inside the open barrier;
- phase-lock counts: pre `68/0`, barrier `0/0`, post `0/65` for before/after deltas;
- +195 recurs later in denser correspondence islands.

No purchased/private payload bytes are stored in this artifact.

## New transition-object contract

Added `csmc_p4_transition_object.py` with a fail-closed schema and `test_csmc_p4_transition_object_synthetic.py`.

A local-child classification requires all of the following simultaneously:

1. offset/gap identity: `(csmc_gap - clip_gap) == (delta_after - delta_before)`;
2. local scale preserved: symmetric gap asymmetry <= 0.05;
3. exact reused anchors at both ends;
4. complete cross-serialization qword extinction inside the bridge;
5. clean phase switch: pre uses only the old delta, barrier uses neither, post uses only the new delta;
6. the post-regime recurs later independently.

The contract rejects semantic owner, codec, geometry, Blender-import, or runtime-trace promotion as input guardrails.

Synthetic coverage includes:
- +197→+195-shaped local transition: PASS;
- large-asymmetry 1325→269 boundary: classified as section repack/reorder candidate;
- semantic guardrail violation: fail-closed;
- offset/gap identity mismatch: remains unresolved;
- missing phase-lock evidence: fail-closed.

## Real aggregate result

`BND_197_TO_195` passes every preregistered local-child gate:

- symmetric gap asymmetry = **0.005277044854881266**;
- offset/gap identity = true;
- reused-anchor bracket = true;
- complete extinction = true;
- clean phase switch = true;
- post-regime recurrence = true.

Classification:

`LOCAL_LENGTH_CHANGING_CHILD_CANDIDATE`

Owner scope:

`SAME_HIGHER_LEVEL_OWNER_FAVORED_NOT_PROVEN`

The semantic owner remains `UNRESOLVED` and semantic promotions remain zero.

## Interpretation

This does not name the serializer function, object type, or model semantic. It does narrow the hierarchy of explanations.

The +197 and +195 neighborhoods are now better modeled as two correspondence phases of the same higher-level ordered region, separated by one locally reserialized child/subunit whose representation is 16 bytes shorter in CSMC. By contrast, the large ~4.69M transitions retain their section-repack/reorder character because their gap asymmetry is orders of magnitude larger and the broader file already contains section-order inversion.

Therefore the next useful question is no longer “what bytes are inside the 3 KiB barrier?” It is:

> what bounded serializer/consumer event begins after the last +197 phase, owns the local length-changing child, and returns control before the +195 phase resumes?

## Static ceiling reached for naming the consumer

Current public-safe static evidence can classify the transition scope, but it does not contain a mapping from this exact transition to a named internal function/callsite or a confirmed geometry/index semantic. Guessing such a name would exceed the evidence.

This is a **consumer-identity evidence gap**, not a reason to reopen broad byte scans.

## Runtime implication — preparation only, not execution

If a runtime trace is eventually necessary, the transition object preregisters exactly one useful landmark:

`BOUNDARY_TRANSITION_EVENT`

A future trace should be accepted only if it is causally tied to one no-change Save and remains bounded to the serialization interval around this transition. Broad GUID scans, whole-memory searches, repeated Save operations, and idle partial-copy diagnostics remain closed.

No Save, Ctrl+S, MODELER UI action, or runtime diagnostic was executed in this pass.

## CLOSED / DEPRIORITIZED

- barrier byte brute-force as the next mainline question: CLOSED;
- exact-qword relocation of the barrier: CLOSED by global extinction;
- aligned 4-byte literal relocation as a high-priority explanation: DEPRIORITIZED by collision baseline;
- +197→+195 as a large owner/section permutation boundary: materially weakened;
- named semantic owner / mesh / index / bone / material promotion: unsupported;
- Blender import success: not claimed.

## NEXT

Build a fail-closed `BOUNDARY_TRANSITION_EVENT` evidence contract and synthetic tests now, without executing runtime. The contract should make any future one-shot no-change-Save trace immediately analyzable while forbidding broad memory collection and semantic promotion.
