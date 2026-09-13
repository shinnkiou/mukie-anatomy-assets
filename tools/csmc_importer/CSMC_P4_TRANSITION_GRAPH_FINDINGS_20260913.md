# CSMC P4 transition graph / owner-scope findings — 2026-09-13

Status: **PUBLIC-SAFE STATIC MAINLINE / ZERO MODELER ACTIONS / ZERO RUNTIME JOBS**

This pass composes already-verified transition evidence into one semantics-free graph. It does not rescan payload bytes and does not infer model semantics from displacement values.

## Inputs

Verified character-route transitions:

1. `BND_197_TO_195`
   - structural class: `LOCAL_LENGTH_CHANGING_CHILD_CANDIDATE`
   - 380 / 378 qword open barrier
   - net -16 B
   - complete cross-serialization qword extinction: YES

2. `BND_195_TO_194`
   - sparse excursion boundary
   - 5090 / 5089 qwords
   - net -8 B
   - complete extinction: NO

3. `BND_194_TO_195`
   - sparse excursion boundary
   - 1582 / 1583 qwords
   - net +8 B
   - complete extinction: NO

4. `BND_4693615_TO_4692559`
   - section repack/reorder candidate
   - 1325 / 269 qwords
   - net -8448 B
   - complete extinction: NO

5. `BND_4692559_TO_4697174`
   - section repack/reorder candidate
   - 3573 / 8188 qwords
   - net +36920 B
   - complete extinction: NO

Verified unique-once anchor support used only where known:
- +197: 685
- +195: 187
- +194: 6

## Implementation

Added `csmc_p4_transition_graph.py` and `test_csmc_p4_transition_graph_synthetic.py`.

The graph deliberately keeps transition class and semantic owner separate. Guardrails require semantic owner, geometry, index, codec, runtime execution, and Blender import to remain false/unconfirmed.

## New result — reversible sparse excursion

The graph contains a real reversible cycle:

`+195 -> +194 -> +195`

Properties:
- anchor support ratio `+194 / +195 = 6 / 187 = 0.03208556149732621`;
- first edge changes relative size by -8 B;
- return edge changes it by +8 B;
- round-trip net relative size change = **0 B**;
- neither barrier is a complete cross-serialization extinction island.

Classification:

`SPARSE_REVERSIBLE_EXCURSION_INSIDE_BASE_REGIME`

Structural owner implication:

`DELTA_CHANGE_NOT_SUFFICIENT_FOR_OWNER_CHANGE`

This is a strict negative rule: a displacement change by itself cannot be treated as an owner/section switch because the observed data contain a sparse delta excursion that returns to the dominant +195 regime with zero net displacement change.

## Effect on +197 -> +195 interpretation

This strengthens the evidential separation between ordinary delta changes and the +197→+195 landmark.

The importance of +197→+195 is **not** that the displacement changes by two qwords. Its distinctive evidence is the conjunction of:
- tight local gap conservation (380 vs 378 qwords);
- exact offset/gap identity;
- exact reused transition endpoints;
- complete barrier qword extinction;
- clean +197-only -> neither -> +195-only phase switch;
- later recurrence of +195.

Therefore the current best structural owner model remains:

`character external container -> unresolved higher-level ordered owner -> local length-changing child transition BND_197_TO_195 -> continuing ordered region`

with owner identity still `UNRESOLVED`.

## Contrast with section-scale transitions

The ~4.69M transitions remain `SECTION_REPACK_OR_REORDER_CANDIDATE` because they combine large asymmetric gaps with retained barrier/global qword reuse. They should not be collapsed into the same structural family as either the reversible +194 excursion or the complete-extinction +197→+195 child candidate.

## Closed hypotheses

- any delta/displacement switch implies owner change: **REJECTED**;
- small delta change is sufficient to identify a serializer-owned extinction child: **REJECTED**;
- +197→+195 is important merely because its delta changes by two qwords: **REJECTED**;
- +194 is a peer stable regime to +195: **REJECTED / strongly disfavored by 6 vs 187 unique-once anchor support**;
- current graph proves a named serializer function or semantic owner: **REJECTED**;
- current graph proves geometry/index or Blender import: **REJECTED**.

## Current consumer target

Preferred narrow consumer landmark remains:

`BND_197_TO_195`

The transition graph reduces the future runtime question further. If static evidence cannot map the local child to a named consumer, a future trace should ask only which module+RVA/call sequence is causally active across this already-preregistered local transition during the single no-change Save. The fail-closed `BOUNDARY_TRANSITION_EVENT` contract remains the required intake surface.

No runtime trigger was executed in this pass.
