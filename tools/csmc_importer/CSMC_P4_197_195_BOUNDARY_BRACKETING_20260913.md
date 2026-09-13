# CSMC P4 +197 -> +195 boundary bracketing — 2026-09-13

Public-safe aggregate analysis only. No purchased/private payload bytes are included. No MODELER/UI action was performed.

## Starting point

The previous independent-boundary triage selected `BND_197_TO_195` because its unanchored neighborhood sizes are nearly conserved across the two serializations:

- clip gap: 380 qwords = 3,040 bytes
- CSMC gap: 378 qwords = 3,024 bytes
- correspondence delta changes from +197 to +195 qwords
- net relative-size shift: -2 qwords = -16 bytes

The exact-qword LCS and nearby literal-size scan were already negative, so this pass does **not** repeat them. It asks whether the boundary can be bracketed by recurrence and exact-anchor density.

## 1. The barrier itself has zero exact 8-byte reuse

The open intervals between the bounding anchors were compared as unordered sets of aligned 8-byte blocks:

- clip boundary window: 380 blocks, 380 distinct
- CSMC boundary window: 378 blocks, 378 distinct
- exact shared distinct qwords across the two boundary windows: **0**
- shared-once-each qwords: **0**
- weighted shared occurrences: **0**
- exact-qword set Jaccard: **0.0**

Thus the 16-byte relative-size shift does **not** look like a mostly byte-identical local record with a small insertion/deletion inside it. The whole ~3 KiB bridge is serializer-divergent at aligned 8-byte granularity.

This does not prove encryption/compression or any particular transform.

## 2. Exact positional reuse collapses across the boundary

Using the established local correspondence deltas on each side, exact positional 8-byte equality was measured in windows immediately adjacent to the transition:

| window | before boundary under +197 | after boundary under +195 |
|---:|---:|---:|
| 64 qwords | 56/64 = **87.5%** | 4/64 = **6.25%** |
| 128 qwords | 68/128 = **53.125%** | 4/128 = **3.125%** |
| 256 qwords | 68/256 = **26.5625%** | 4/256 = **1.5625%** |
| 512 qwords | 103/512 = **20.1172%** | 13/512 = **2.5391%** |

So the transition is not only a -16-byte offset change. It also brackets a strong change from a dense direct-reuse neighborhood to an immediately sparse direct-reuse neighborhood.

## 3. Recurrence says +195 is a real later regime, not a one-off accident

The existing unique-once anchor segmentation contains:

- +197 correspondence: 685 unique-once anchors total across the summarized segments
- +195 correspondence: 187 unique-once anchors total

Immediately before the selected boundary, dense +197 segments include:

- 68 anchors across 78 qwords: density **0.8718**
- 50 anchors across 70 qwords: density **0.7143**

The first +195 segment after the boundary is much sparser:

- 65 anchors across 1,376 qwords: density **0.04724**

But +195 later reappears in denser islands, including 17/30 = **0.5667** and 14/22 = **0.6364**. Therefore +195 is a recurring correspondence regime; the low density is specific to the first post-boundary bridge, not evidence that the +195 mapping itself is spurious.

## Narrow interpretation

The strongest current structural model for `BND_197_TO_195` is:

> a locally bounded serializer-divergent bridge of ~3 KiB in which the relative representation shrinks by 16 bytes, followed by a recurring +195 correspondence regime whose first stretch has very low exact-anchor density before denser reuse islands resume.

This is stronger than the previous generic “local size shift” description, but it still does **not** identify a field, object type, geometry buffer, codec, or semantic owner.

## Closed / rejected by this pass

- “the 380/378-qword barrier is mostly the same qwords plus a 16-byte insertion/deletion”: rejected by zero unordered exact-qword intersection;
- rerunning exact-qword LCS or literal-size searches unchanged: remains closed;
- interpreting +195 as a one-off accidental offset: weakened by repeated +195 anchor islands later in the payload;
- assigning vertex/index/UV/material/bone/weight semantics: not supported.

## Next static action

Change the question again rather than fitting bytes inside the bridge. The next highest-information file-side task is to test **owner/consume bracketing around the transition endpoints**, using only already-authorized payload metadata/code/static references: determine whether the last dense +197 anchor neighborhood and the first recurring +195 islands fall inside the same higher-level object/section or on opposite sides of an externally identifiable consume/decode boundary.

Do not touch MODELER for this static task. Keep the V4.4 no-change-save candidate inert and not live-wired. Production Worker/STABLE remain unchanged.

## Claim boundary

No real Blender import, vertex/index mapping, mesh semantics, codec/encryption/DRM mechanism, or universal CELSYS format is claimed.