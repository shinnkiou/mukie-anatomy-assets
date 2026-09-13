# CSMC P4 small-delta excursion comparison — 2026-09-13

Status: REAL FILE-SIDE STATIC PASS / ZERO MODELER ACTIONS / ZERO RUNTIME JOBS.

After establishing that the `+197→+195` boundary is sharper than the large ~4.69M repack/reorder transitions, this pass tests another **small, near-conserved displacement change** instead of fitting more transforms to the same bridge.

The order-preserving chain contains only **6 unique-once anchors at +194** versus **187 at +195**, so +194 must be treated as a sparse excursion, not a peer stable regime.

## Paired excursion

| Boundary | clip / CSMC open barrier | Relative change | barrier direct matches old/new delta | barrier distinct qwords found anywhere in opposite payload | Complete global qword extinction |
|---|---:|---:|---:|---:|---|
| `+195→+194` | 5090 / 5089 qwords | -8 B | 0 / 0 | clip→CSMC 6/5089; CSMC→clip 5/5089 | NO |
| `+194→+195` | 1582 / 1583 qwords | +8 B | 0 / 0 | clip→CSMC 10/1576; CSMC→clip 4/1572 | NO |

Local phase checks:
- before `+195→+194`, a 257-qword window has **17** `+195` matches and 0 `+194`; first 256 qwords after have only **2** `+194` matches;
- before `+194→+195`, a 257-qword window has **4** `+194` matches and 0 `+195`; first 256 qwords after have **45** `+195` matches and 0 `+194`.

The two displacement changes are `-1 qword` then `+1 qword`, so the broader correspondence returns to `+195` with **net zero displacement change across the pair**.

## Interpretation

This is useful contrast evidence. Small relative-length changes do occur elsewhere, but they do **not** automatically produce the complete cross-serialization qword extinction seen at `+197→+195`. Both +194 excursion barriers retain exact qwords elsewhere in the opposite payload, and +194 itself has only six unique-once anchors.

Therefore `+197→+195` remains the preferred first narrow owner/consumer landmark: it combines stronger neighboring phase support with a complete extinction island. The +194 pair is better modeled as a sparse temporary one-qword displacement excursion inside the broader +195 section, not as evidence that every small delta switch has the same serializer-owned rewrite signature.

No geometry/material/rig semantics, codec/encryption/DRM claim, or Blender-import claim is made.

Efficiency: user actions 0; MODELER actions 0; runtime jobs 0; Production Worker/STABLE changes 0.
