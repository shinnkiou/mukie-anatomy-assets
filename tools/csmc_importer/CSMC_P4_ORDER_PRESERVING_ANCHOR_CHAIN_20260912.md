# CSMC P4 Order-Preserving Anchor Chain — 2026-09-12

Status: REAL FILE-SIDE STRUCTURAL CORRESPONDENCE / PUBLIC-SAFE METADATA ONLY

This pass uses only exact aligned 8-byte blocks from the authorized `.clip catalog_character` and saved CSMC `character` payloads. It contains no model bytes.

## Result

- `.clip` aligned blocks: 6,973,071
- CSMC aligned blocks: 9,635,226
- shared 8-byte values occurring exactly once in each payload: 2,558
- longest order-preserving chain: **1,642 anchors**
- fraction of unique-once pairs retained in the increasing chain: **64.19%**

For two independent uniform random 64-bit block streams of these lengths, the expected cross-file collision count is about `3.64e-6`. The observed thousands of exact shared blocks therefore support deterministic structural reuse. This does not identify the transform or semantics.

## Dominant order-preserving regimes

- clip `138,942–140,021`: 476 chain anchors at delta `+965`; local density about `0.441`
- clip `194,034–222,310`: 892 chain anchors; dominant deltas `+197` (685) and `+195` (187)
- clip `236,792–236,821` -> CSMC `4,930,407–4,930,436`: 30/30 unique-once anchors at delta `+4,693,615`
- clip `238,147–238,186`: 13 anchors at delta `+4,692,559`

The shared blocks therefore preserve substantial relative order across the two serializations and are not merely an unordered bag of repeated values.

## Interpretation

Best current static model: **piecewise order-preserving reuse inside a larger reserialized/repacked representation**.

Guardrails:
- displacement changes do not by themselves prove literal insert/delete operations of exactly that size;
- sparse mappings can reflect reordering or different wrappers;
- exact block reuse does not identify geometry, materials, metadata, compression, encryption, or DRM.

## Mainline use

Prioritize:
1. unique-once order-preserving anchors;
2. high-entropy exact runs inside those regimes;
3. low-complexity repeated runs only as section/filler boundaries.

Use these landmarks only to narrow a concrete CELSYS consume/decode hypothesis. Do not claim vertex/index/UV/material/bone/weight decoding or Blender import from this evidence.
