# CSMC P4 Record / Section Boundary Checkpoint — 2026-09-12

Status: REAL FILE-SIDE P4 BOUNDARY PASS / ZERO MODELER INTERACTION.

This checkpoint contains metadata and structural observations only. It does not contain purchased model bytes, extracted geometry, texture data, credentials, or private runtime captures.

## Reproduced anchor baseline

- shared aligned 8-byte values unique once in each payload: 2,558
- longest order-preserving chain: 1,642 anchors
- chain fraction: 64.19%
- accepted model remains: `piecewise order-preserving deterministic structural reuse inside a larger reserialized/repacked representation`

## Strong `+965` record-like lattice

The `+965` regime contains 476 order-preserving unique anchors. Splitting it at large anchor gaps yields 23 anchor clusters. The first 22 complete cluster-to-cluster intervals are only 48 or 49 blocks long:

- 48-block intervals: 13
- 49-block intervals: 9
- byte pitch: 384 / 392 bytes
- every complete group of five successive intervals sums to exactly 242 blocks = 1,936 bytes
- four complete five-interval groups reproduce that 242-block sum

Across those 22 complete intervals, 1,065 aligned blocks were compared and 527 are exact between the two serializations (49.48%). The relative-position profile is strongly structured:

- blocks 0–20: exact in 22/22 intervals (168 bytes always preserved)
- blocks 22–23: different in 22/22 intervals (16 bytes always serializer-sensitive)
- blocks 25–26: exact in 22/22 intervals (16 bytes always preserved)
- blocks 28 onward: different in every complete interval
- blocks 21, 24 and 27 are mixed

This supports a repeated record-like positional lattice with a stable internal correspondence boundary. It does not identify semantic field types.

No stronger 16/32/64-byte start alignment was found beyond 8-byte block alignment.

## Bounded relative-size transitions

### `+197 -> +195`

The strongest `+197` run ends at clip block 199,315 / CSMC 199,512. The next `+195` run begins at clip 199,696 / CSMC 199,891.

- clip unanchored gap: 380 blocks
- CSMC unanchored gap: 378 blocks
- net delta change: -2 blocks = -16 bytes

A net 16-byte relative-length change is introduced somewhere in this boundary window. Literal insertion/deletion semantics are not yet proven.

### `+4,693,615 -> +4,692,559`

- clip gap: 1,325 blocks
- CSMC gap: 269 blocks
- net delta change: -1,056 blocks = -8,448 bytes

### `+4,692,559 -> +4,697,174`

- clip gap: 3,573 blocks
- CSMC gap: 8,188 blocks
- net delta change: +4,615 blocks = +36,920 bytes

These are section-boundary candidates bounded by exact order-preserving anchors.

## Section reordering evidence

A separate high-information exact run exists at clip block 3,159,728 -> CSMC block 3,994,948, delta +835,220, length 30 blocks. But the much earlier clip region 236,792 maps to CSMC 4,930,407.

Therefore a later clip section maps to an earlier CSMC position than the 4.93M-mapped section. Global transformation cannot be modeled as insertion/deletion plus one cumulative offset; at least some sections are reordered/repacked.

## Literal size-field negative check

Selected boundary windows were scanned for obvious 32-bit LE/BE literals matching candidate byte sizes 384, 392, 1,936, 168, 224, 1,576, 1,560, 8,448 and 36,920. No literal hits were found in the checked ±512-byte windows.

## Next mainline

1. Treat the `+965` 48/49-block lattice as the first record-boundary target.
2. Analyze its preserved prefix / narrow mixed zone / preserved 16-byte island / divergent tail without assigning semantics prematurely.
3. Treat the `+197 -> +195` window as a bounded 16-byte relation target.
4. Use the 4.93M-regime boundaries and reordered +835,220 section to infer section permutation/length rules.
5. Resume runtime tracing only when one of these file-side structures yields a concrete consume/decode hypothesis.

Human MODELER operations required for this pass: 0. Keep the already-open MODELER/model state untouched.

Claim boundary unchanged: no vertex/index/UV/material/bone/weight recovery and no real Blender import yet.
