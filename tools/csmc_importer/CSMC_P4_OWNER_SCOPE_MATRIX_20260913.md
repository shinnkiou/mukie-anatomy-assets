# CSMC P4 owner-scope evidence matrix — 2026-09-13

Status: **PUBLIC-SAFE STATIC MAINLINE / ZERO MODELER ACTIONS / ZERO RUNTIME JOBS**

This pass combines already-verified aggregate evidence around `BND_197_TO_195`. It does not rescan barrier bytes and does not assign geometry or serializer semantics.

## Current route

The transition remains inside the already-resolved outer `character` route. The semantic parent object and consumer function are still unresolved.

## Evidence favoring continuity inside one higher-level owner

1. **Reused endpoints bound a local rewrite.** The last `+197` correspondence and first `+195` correspondence survive outside the open barrier while the open barrier itself is a complete aligned-qword extinction island.
2. **The gap is tightly conserved across surfaces.** The open barriers are 380 qwords in `.clip` and 378 qwords in CSMC; symmetric gap asymmetry is `0.005277044854881266`.
3. **The correspondence phase changes cleanly around the local gap.** `+197` dominates before, neither neighboring delta explains the barrier, and `+195` resumes after the gap and recurs later.
4. **Delta change alone cannot mean owner change.** The independent `+195→+194→+195` excursion returns to the base regime with zero net relative size change and no complete extinction.
5. **The known +965 whole-record grammar is not the child grammar here.** 378–382 qwords fall in the impossible gap between seven complete 48/49-qword records (max 343) and eight complete records (min 384). The +965 preservation floor also contradicts the barrier extinction.
6. Rejecting the known +965 parser does **not** reject a shared parent. Partial records, a different child grammar, or another sibling structure remain possible.

## Evidence that directly proves a new owner

None in the current public-safe aggregate set.

There is no verified explicit owner marker, parent record boundary, parent length field, or named consumer cross-reference at `BND_197_TO_195`.

## Classification

- owner scope: `SAME_HIGHER_LEVEL_OWNER_FAVORED_NOT_PROVEN`
- consumer scope: `DISTINCT_LOCAL_CHILD_GRAMMAR_CANDIDATE_INSIDE_CHARACTER_ROUTE`
- semantic owner: `UNRESOLVED`
- consumer function: `UNRESOLVED`
- semantic promotions: `0`

## Missing decisive edges

The static search should now target only these edges:

- `EXPLICIT_PARENT_RECORD_BOUNDARY`
- `EXPLICIT_PARENT_LENGTH_FIELD`
- `EXPLICIT_CONSUMER_CROSSREF`

This is narrower than searching for more literal bytes or fitting more transforms inside the barrier.

## Runtime gate

`STATIC_NOT_EXHAUSTED`

The current evidence does **not** yet justify firing the no-change Save solely to learn owner scope. Static metadata, route documents, schema dictionaries, and existing public-safe structural outputs should be searched first for an explicit parent boundary or consumer cross-reference.

If static work eventually resolves the parent boundary/length relation and leaves only `EXPLICIT_CONSUMER_CROSSREF`, then the existing fail-closed `BOUNDARY_TRANSITION_EVENT` contract becomes the eligible runtime path: exactly one no-change Save and exactly one narrow diagnostic, with no broad scan.

No claim is made for vertex/index/UV/material/bone/weight semantics, codec/encryption/DRM, or Blender import.
