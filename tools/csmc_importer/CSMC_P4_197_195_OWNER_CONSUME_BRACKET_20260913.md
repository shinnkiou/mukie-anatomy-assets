# CSMC P4 +197 → +195 owner/consume bracketing — 2026-09-13

Status: **REAL FILE-SIDE STATIC PASS / ZERO MODELER ACTIONS / ZERO RUNTIME JOBS**

This pass changes the question again. It does not repeat exact-LCS, literal-size, XOR, cadence fitting, or idle-memory scanning. It tests whether the already-bracketed `+197 → +195` bridge is better explained as a relocated/reordered section or as a locally reserialized length-changing unit inside an otherwise continuing ordered neighborhood.

Only aggregate positions/counts are recorded. No purchased/private payload bytes are included.

## 1. The ~3 KiB bridge is not merely locally unmatched — its qwords disappear globally across serializations

Known open barrier:

- clip blocks `199316..199695`: **380 qwords / 3,040 B**
- CSMC blocks `199513..199890`: **378 qwords / 3,024 B**
- mapping phase changes `+197 → +195 qwords`
- relative representation shrinks **2 qwords = 16 B**

New global-presence result:

- all 380 clip barrier qwords are distinct;
- **0 / 380** occur anywhere in the entire CSMC `character` payload;
- all 378 CSMC barrier qwords are distinct;
- **0 / 378** occur anywhere in the entire clip `catalog_character` payload.

Therefore the barrier is not an exact-qword section that was merely moved elsewhere. At aligned 8-byte granularity, the corresponding content is completely reserialized/re-encoded between the two representations.

This strengthens the earlier local Jaccard=0 result because the negative now holds against the *entire opposite payload*, not only the paired boundary window.

## 2. The extinction interval is exactly bracketed by reused qwords

The qword immediately before the barrier is reused at the expected `+197` position, and the first qword after the barrier is reused at the expected `+195` position. The same is true viewed from CSMC back to clip.

Thus, around this transition, the maximal contiguous run of qwords with **no occurrence anywhere in the opposite serialization** is exactly the already-known open barrier:

- clip: `199316..199695` = **380 qwords**
- CSMC: `199513..199890` = **378 qwords**

This makes the two endpoint anchors materially stronger than arbitrary sparse-anchor endpoints: they bracket a complete cross-serialization **qword-extinction island**.

## 3. Clean three-phase correspondence switch

Direct positional equality under the two established local deltas gives a clean phase switch:

| phase | clip range | length | matches at +197 | matches at +195 |
|---|---:|---:|---:|---:|
| dense pre-boundary | `199238..199315` | 78 qwords | **68** | **0** |
| extinction bridge | `199316..199695` | 380 qwords | **0** | **0** |
| first post-boundary span | `199696..201071` | 1,376 qwords | **0** | **65** |

For the first 512 qwords after the bridge specifically, the counts are `0` at +197 and `13` at +195.

So this is not a noisy gradual drift between offsets. The observed structure is:

> **phase-locked +197 reuse → complete extinction island → phase-locked +195 reuse**

with a net 16-byte shrink inside the extinction island.

## 4. Owner/consume consequence

This new evidence does not identify a semantic owner or decoder function, but it narrows the structural model.

A pure section-reordering explanation for this boundary is now **disfavored at exact-qword granularity** because none of the bridge qwords relocates anywhere in the opposite payload. Yet ordered exact reuse resumes immediately after the bridge at the new stable `+195` phase.

The strongest current file-side model is therefore:

> a **local serializer-owned length-changing unit** inside a continuing ordered neighborhood: the unit is fully reserialized between `catalog_character` and `character`, changes relative length by 16 bytes, and downstream correspondence immediately resumes at the new phase.

This favors — but does not prove — that the last dense `+197` neighborhood and the first `+195` neighborhood belong to the same larger ordered owner/section with a divergent child/subunit between them, rather than lying on opposite sides of a global section permutation boundary.

## Runtime hypothesis sharpening

If/when runtime tracing is used, do not search broadly for the erased barrier bytes: exact qwords from either saved representation are not expected to survive across the other serialization.

The useful runtime landmark becomes the **transition event itself**:

1. identify the consumer/serializer operating immediately after the last `+197` preserved anchor neighborhood;
2. follow the length-changing unit through the bridge;
3. verify that downstream state resumes on the `+195` correspondence phase;
4. only then inspect whether the decoded/consumed object exposes a regular geometry-bearing allocation.

This is a narrower consume/decode hypothesis than generic GUID/header scanning.

## Efficiency / gates

- MODELER actions: **0**
- runtime jobs: **0**
- repeated closed experiments: **0**
- permission gate reconsideration: **0**
- Production Worker / STABLE changes: **0**

No additional user action is required for this static pass.

## Guardrails

- no private payload bytes in public artifacts;
- no vertex/index/UV/material/bone/weight semantics;
- no compression/encryption/DRM claim;
- same higher-level owner is favored, not proven;
- real Blender import remains unproven.
