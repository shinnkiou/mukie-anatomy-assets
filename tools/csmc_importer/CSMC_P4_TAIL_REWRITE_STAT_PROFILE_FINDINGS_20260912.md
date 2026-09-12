# CSMC P4 tail rewrite statistical profile — 2026-09-12

Status: `REAL FILE-SIDE P4 TAIL-REWRITE PROFILE PASS / ZERO MODELER INTERACTION`

Scope: metadata-only statistical analysis of serializer-sensitive qwords inside the already-established `+965` 48/49-qword record family. No purchased model bytes are embedded.

## Result

Across the serializer-sensitive tail (`relative qword 21 .. record end-1`) there are **538 nonexact qword pairs** across the 22 complete records.

For two independent 64-bit values, the expected Hamming distance is 32 bits with variance 16. Observed across the 538 rewritten qwords:

- mean Hamming distance: `31.9907063` bits
- sample variance: `16.1619246`
- median: `32`
- minimum: `21`
- maximum: `44`
- mean z-score vs the independent 64-bit baseline: `-0.05389`

Across `538 × 8 = 4,304` compared bytes:

- observed equal bytes: `16`
- expected equal bytes for independent byte values: `16.8125`
- z-score: `-0.19854`

Across all 538 rewritten qword pairs:

- distinct XOR masks: `538`
- duplicate XOR masks: `0`
- maximum XOR-mask frequency: `1`

48-qword class:

- rewritten qwords: `319`
- mean Hamming distance: `32.01254`
- observed equal bytes: `10`
- independent-byte expectation: `9.96875`

49-qword class:

- rewritten qwords: `219`
- mean Hamming distance: `31.95890`
- observed equal bytes: `6`
- independent-byte expectation: `6.84375`

## Updated structural model

The current file-side model is two-layered:

1. **structural branch / preserve-selection layer** — 48/49 record class changes deterministic preservation behavior, strongest at qword 27 and qword 21;
2. **rewrite layer** — serializer-sensitive qwords that are not preserved become effectively decorrelated at byte/bit level between the two serializations.

This weakens simple local arithmetic, fixed XOR, byte-preserving, endianness-swap, or small-field-patch hypotheses. It increases the expected value of tracing the consume/decode boundary in MODELER/runtime rather than spending the next pass searching for direct bytewise conversion rules.

## Claim boundary

This result does **not** prove encryption, compression, hashing, a codec, geometry semantics, a vertex/index layout, bones/weights, or real Blender import.
