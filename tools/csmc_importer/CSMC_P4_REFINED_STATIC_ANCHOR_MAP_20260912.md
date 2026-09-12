# CSMC P4 Refined Static Anchor Map — 2026-09-12

Status: REAL FILE-SIDE REFINEMENT / PUBLIC-SAFE METADATA ONLY

This note compares only authorized `.clip catalog_character` and saved CSMC `character` payload structure. It contains no purchased model bytes.

## Correction to the earlier longest-run ranking

Several of the longest aligned exact runs are low-complexity repetition rather than high-information structure:

- delta `+197` blocks: 184 blocks / 1,472 bytes, one unique 8-byte block, byte entropy 3.0
- delta `+195`: 186 blocks / 1,488 bytes, one unique block, entropy 3.0
- delta `+133`: 233 blocks / 1,864 bytes, one unique block, entropy 3.0

The repeated block occurs 6,531 times in the `.clip` payload and 4,222 times in the CSMC payload. These longest spans should be treated as filler/sentinel-like repetition, not semantic or geometry evidence.

## Higher-information exact runs

Diverse high-entropy exact runs remain:

| delta blocks | delta bytes | clip start block | CSMC start block | exact length | unique blocks | entropy |
|---:|---:|---:|---:|---:|---:|---:|
| +197 | +1,576 | 197,359 | 197,556 | 40 blocks / 320 B | 40 | 7.289 |
| +965 | +7,720 | 139,813 | 140,778 | 22 / 176 B | 22 | 6.841 |
| +4,693,615 | +37,548,920 | 236,792 | 4,930,407 | 30 / 240 B | 30 | 7.139 |
| +4,692,559 | +37,540,472 | 238,156 | 4,930,715 | 31 / 248 B | 31 | 7.200 |
| +835,220 | +6,681,760 | 3,159,728 | 3,994,948 | 30 / 240 B | 30 | 7.108 |

For these checked runs, equality does not extend to both adjacent aligned blocks. Treat them as local structural fingerprints only.

## Unique-once anchor segmentation

Full aligned analysis found 2,558 shared 8-byte values that occur exactly once in each payload.

Strong position-delta populations:

- `+197`: 685 unique-once anchors
- `+965`: 476
- `+195`: 187
- `+1,448`: 48
- `-779`: 37
- `+4,693,615`: 30
- `+4,692,559`: 13

A strong micro-region at delta `+4,693,615` contains 30 unique-once anchors across a 30-block span (density 1.0).

## Working interpretation

The data supports a working hypothesis of an **8-byte block-oriented deterministic encoded/packed representation with reusable substructures**. This is deliberately not a claim of encryption, cipher, compression, or DRM.

Reasons include:

1. observed CELSYS outer records satisfy `stored_size = align8(logical_size) + 8`;
2. the large payloads have near-maximal byte entropy;
3. thousands of aligned random-looking 8-byte values are reused;
4. high-entropy exact runs survive at shifted positions after low-complexity repetition is filtered.

## Next use

Use the high-information / unique-once regions as static landmarks when narrowing the CELSYS consume/decode path. Do not rank landmarks solely by longest exact run length.

Claim boundary remains unchanged: vertex/index/UV/material/bone/weight decoding and real Blender import are still unproven.
