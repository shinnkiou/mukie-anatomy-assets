# CSMC P4 — +197→+195 Unaligned k-mer Extinction (2026-09-13)

## Scope

Public-safe aggregate analysis of the already-authorized `BND_197_TO_195` barrier. No proprietary payload bytes or matched byte values are included here.

The earlier owner/consume bracket established a local transition from dense `+197` exact qword reuse, through a 380-qword / 378-qword extinction barrier, into `+195` reuse. The aligned 4-byte collision baseline then showed only collision-scale cross-payload reuse.

This pass asks a narrower question: **could the apparent extinction merely be an 8-byte or 4-byte alignment artifact, with the same literal bytes surviving at another byte phase elsewhere in the opposite payload?**

## Method

For k = 5, 6, 7, 8 bytes:

- enumerate every byte-phase k-mer in the bounded barrier;
- scan every byte phase of the entire opposite payload;
- count matching windows and distinct matched k-mers;
- compare observed counts with a uniform-random collision baseline;
- emit aggregate counts only.

Barrier sizes:

- CLIP-side barrier: 3,040 bytes
- CSMC-side barrier: 3,024 bytes

Payload sizes used by the private authorized run:

- CLIP `catalog_character` stored payload: 55,784,568 bytes
- CSMC `character` stored payload: 77,081,808 bytes

## Result

| Direction | k | Source windows | Exact occurrences anywhere in opposite payload | Uniform-random expected occurrences | Poisson P(X≥observed) |
|---|---:|---:|---:|---:|---:|
| CLIP barrier → full CSMC | 8 | 3,033 | 0 | 1.2673732638e-08 | 1.0 |
| CSMC barrier → full CLIP | 8 | 3,017 | 0 | 9.1236708150e-09 | 1.0 |
| CLIP barrier → full CSMC | 7 | 3,034 | 0 | 3.2455453223e-06 | 1.0 |
| CSMC barrier → full CLIP | 7 | 3,018 | 0 | 2.3364339368e-06 | 1.0 |
| CLIP barrier → full CSMC | 6 | 3,035 | 0 | 8.3113346287e-04 | 1.0 |
| CSMC barrier → full CLIP | 6 | 3,019 | 0 | 5.9832528513e-04 | 1.0 |
| CLIP barrier → full CSMC | 5 | 3,036 | 1 | 2.1284027475e-01 | 0.1917147695 |
| CSMC barrier → full CLIP | 5 | 3,020 | 1 | 1.5322201150e-01 | 0.1420607717 |

All source k-mers were distinct for these k values. Local barrier-to-barrier shared distinct k-mers were also zero for k = 5, 6, 7, 8.

## Interpretation

The qword extinction is **not an alignment artifact**. At every byte phase, neither barrier contains any literal 6-, 7-, or 8-byte substring that occurs anywhere in the entire opposite payload. The single 5-byte occurrence in each direction is compatible with ordinary random coincidence rather than excess literal reuse.

This materially weakens these explanations for the barrier:

- a qword-only phase shift;
- a 4-byte alignment shift;
- a simple byte-offset relocation of mostly preserved local content;
- hidden literal bridge bytes surviving elsewhere in the opposite serialization at length ≥6 bytes.

The strongest current structural model remains:

> a local serializer-owned divergence inside a continuing order-preserving neighborhood, with a small net length change but no literal bridge reuse at six bytes or longer.

The useful runtime/decompiler landmark is therefore the **transition/consume event around the +197→+195 boundary**, not a literal barrier signature.

## Guardrails

This result does **not** establish:

- encryption, compression, DRM, or a protection mechanism;
- a key or bypass route;
- geometry, index, UV, material, texture, bone, or weight semantics;
- a working Blender import path.

No MODELER action and no runtime job were required for this pass. Production Worker and STABLE state remain unchanged.
