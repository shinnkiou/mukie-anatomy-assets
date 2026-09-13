# CSMC P4 boundary motif comparison — 2026-09-13

Status: REAL FILE-SIDE STATIC PASS / ZERO MODELER ACTIONS / ZERO RUNTIME JOBS.

This pass compares the already-known `+197→+195` local boundary against the two large ~4.69M displacement transitions using the same aggregate-only owner/consume probe. No proprietary qword values or payload bytes are published.

## Comparable result

| Boundary | Clip/CSMC barrier qwords | Net relative change | Barrier matches old/new delta | Barrier qwords found anywhere in opposite payload | Complete qword extinction | 257-qword pre old-delta matches | 256-qword post new-delta matches |
|---|---:|---:|---:|---:|---|---:|---:|
| `BND_197_TO_195` | 380 / 378 | -16 B | 0 / 0 | clip→CSMC 0/380; CSMC→clip 0/378 | YES | 68/257 | 4/256 |
| `BND_4693615_TO_4692559` | 1325 / 269 | -8448 B | 9 / 7 | clip→CSMC 22/1217; CSMC→clip 18/246 | NO | 30/257 | 45/256 |
| `BND_4692559_TO_4697174` | 3573 / 8188 | +36920 B | 7 / 13 | clip→CSMC 124/3225; CSMC→clip 184/7924 | NO | 45/257 | 46/256 |

## Interpretation

- `BND_197_TO_195` is structurally distinct: its entire barrier is a complete aligned-qword extinction island, and the barrier contains **zero** direct matches under either neighboring displacement regime.
- The two ~4.69M transitions still retain exact barrier correspondences and non-zero global reuse in the opposite payload. They behave more like broad repack/reorder transition zones than a clean local serializer-owned rewrite island.
- This independently strengthens the decision to keep `+197→+195` as the preferred narrow owner/consumer landmark. The large-displacement transitions remain useful section-boundary evidence but are lower-value targets for a first narrow runtime trace.

This comparison does not identify geometry/material/rig semantics and does not establish compression, encryption, DRM, a key, or a Blender import path.

Efficiency: user actions 0; MODELER actions 0; runtime jobs 0; Production Worker/STABLE changes 0.
