# CSMC P4 independent-boundary triage — 2026-09-13

Public-safe aggregate analysis only. No purchased/private payload bytes are included.

## Why this analysis exists

The `+965` 48/49-qword record family has already been mined through its stable prefix, q21..27 control zone, length-class association, and rewritten-tail statistics. Repeating more fits on those same 22 records is closed pending independent evidence. The previous apparent pre-record owner/header was also rejected because it maps to the prior record tail.

This checkpoint therefore compares independent correspondence boundaries already preserved in `CSMC_P4_RECORD_SECTION_BOUNDARY_20260912.json` and asks a narrower question: which boundary looks like a local serializer-size shift, and which boundaries look like section-level repacking/reordering?

## Boundary gap asymmetry

For each boundary, define `symmetric_gap_asymmetry = abs(csmc_gap - clip_gap) / ((csmc_gap + clip_gap)/2)`.

| Boundary | clip gap | CSMC gap | signed delta | symmetric asymmetry |
|---|---:|---:|---:|---:|
| `+197 -> +195` | 380 | 378 | -2 blocks / -16 B | 0.005277 |
| `+4,693,615 -> +4,692,559` | 1325 | 269 | -1056 blocks / -8448 B | 1.324969 |
| `+4,692,559 -> +4,697,174` | 3573 | 8188 | +4615 blocks / +36,920 B | 0.784797 |

The first boundary is about 251x less asymmetric than the `+4,693,615 -> +4,692,559` boundary, and about 149x less asymmetric than the `+4,692,559 -> +4,697,174` boundary.

## Interpretation

### `+197 -> +195` is the best current local-boundary candidate

Its two serializations have nearly the same unanchored gap length (380 vs 378 qwords) and differ by only two 8-byte blocks. This does not identify a field or record type, and the barrier itself already has exact-qword LCS = 0, so direct byte-conversion guessing remains low value. But among the independent boundaries currently summarized, this is the cleanest place to look for a local consume/decode transition or local object-size/branch effect because it preserves neighborhood scale while changing correspondence delta by only -2 blocks.

### The ~4.69M-delta transitions are section-level repack candidates, not local-record analogues

Their gap asymmetries are huge and opposite-signed: one interval is clip-heavy by 1056 qwords, the next is CSMC-heavy by 4615 qwords. Together with the already-established order inversion (`clip 3,159,728 -> CSMC 3,994,948` versus much earlier `clip 236,792 -> CSMC 4,930,407`), this is more consistent with section-level repacking/reordering than with a 48/49-qword local record-size mechanism.

Do not reuse those 4.69M boundaries as if they were another instance of the +965 local record family.

## Closed / deprioritized hypotheses

- repeat q21..27 signature/cadence fitting on the same 22 `+965` records: closed pending independent data;
- one stable-prefix bit directly stores 48/49 length: rejected;
- equality signature completely determines 48/49 length: rejected (`0000111` remains 3/3 ambiguous);
- pre-record owner/header before the first +965 record: rejected; it maps to the previous record tail;
- fixed XOR/small arithmetic/endian/local byte patch over rewritten tail: deprioritized by the near-random Hamming/equal-byte profile;
- treating the ~4.69M section boundaries as local 384/392-byte record analogues: rejected by gap-scale/asymmetry and order-reordering evidence.

## Next static action

Use the `+197 -> +195` boundary as the next independent local target, but change the question from byte transform to structure: identify whether any public-safe recurrence, alignment, neighboring anchor-density change, or external owner/consume evidence brackets the 380/378-qword barrier. Do not rerun the already-zero exact-qword LCS or literal-size scans unchanged.

Runtime remains separate: the V4.2 idle partial-copy branch is closed (`returned_bytes=[0,0,0]`). The prepared `csmc_modeler_save_no_change_v1` candidate remains CI-only and not live-wired because it can write the current MODELER document. No MODELER action is performed by this checkpoint.

## Claim boundary

No vertex/index/UV/material/bone/weight semantics, codec/encryption/DRM mechanism, or Blender import is claimed.
