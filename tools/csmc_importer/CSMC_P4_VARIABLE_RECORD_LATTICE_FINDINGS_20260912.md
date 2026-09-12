# CSMC P4 +965 Variable-Record Lattice Findings — 2026-09-12

Status: `STRONG_VARIABLE_LENGTH_RECORD_BOUNDARY_CANDIDATE` / file-side only / zero MODELER interaction.

This checkpoint contains structural metadata only. It contains no purchased model bytes, recovered mesh/texture data, credentials, or private runtime capture bytes.

## Stronger boundary result

The previously observed `+965` lattice is stronger than a generic record-like pattern. Across **22 complete intervals**:

- record lengths are only **48 blocks (384 bytes)** or **49 blocks (392 bytes)**,
- counts: **13 × 48-block** and **9 × 49-block**,
- each of the four complete 5-record groups sums to **242 blocks = 1,936 bytes**,
- at each record start, relative blocks `0..20` (**168 bytes**) are exact in **22/22** record pairs,
- those prefix qwords are not low-complexity filler: every prefix position has **22 distinct values across the 22 records** and byte entropy around ~6.8–7.0 bits/byte,
- relative blocks `22..23` are different in **22/22**,
- relative blocks `25..26` are exact in **22/22**,
- relative block `28` through the record tail is rewritten for the complete intervals,
- at every **interior** next-record boundary, the 168-byte preserved prefix restarts exactly,
- the terminal cluster is only partially inside the `+965` regime, so it is treated as a regime edge rather than a failed record recurrence.

This makes the cluster starts high-confidence **variable-length record boundary candidates**, not merely anchor clusters.

## Field-zone structure

Within each 48/49-block record, the correspondence can be divided structurally:

| Relative blocks | Bytes | Cross-serialization behavior |
|---|---:|---|
| `0..20` | 168 | exact, high-entropy, record-specific |
| `21` | 8 | mixed (`6/22` exact) |
| `22..23` | 16 | always rewritten (`0/22`) |
| `24` | 8 | mixed (`3/22` exact) |
| `25..26` | 16 | always exact (`22/22`) |
| `27` | 8 | mixed (`12/22` exact) |
| `28..end` | 160 or 168 | rewritten until next record boundary |

The exact 16-byte island at `25..26` is preserved but **must not yet be labeled** as an ID, vector, GUID, transform, or other semantic field.

## Local relocation negative result

Every exact 8-byte match found inside corresponding record pairs occurred at the **same relative offset**:

- same-position matches: **527**
- off-diagonal matches: **0**

Therefore the divergent tail is not explained by a simple local block insertion/shift inside these records. The safer model is a fixed correspondence layout containing preserved and serializer-sensitive zones.

## Stride-class correlation

The mixed positions are not random with respect to record length:

- relative block `21`: 48-block records exact `0/13`; 49-block records exact `6/9`
- relative block `24`: 48-block records exact `3/13`; 49-block records exact `0/9`
- relative block `27`: 48-block records exact `3/13`; 49-block records exact `9/9`

In particular, block `27` is preserved in **all 9/9 49-block records** while only **3/13 48-block records** preserve it. This is a useful structural discriminator but not a decoded length field.

No single constant byte/bit in the tested record body perfectly classified 48-vs-49 length, so there is no evidence yet for a trivial one-byte length flag.

## Updated structural hypothesis

Retain the global hypothesis:

`piecewise order-preserving deterministic structural reuse inside a larger reserialized/repacked representation`

Refine the `+965` local model to:

`repeated 48/49-block variable records grouped into 1,936-byte five-record supergroups, with a 168-byte high-entropy preserved prefix, narrow mixed/rewrite zones, a preserved 16-byte island, and a rewritten tail that resets at the next record boundary.`

This is still structural evidence only. It does not prove vertex/index/UV/material/bone/weight semantics, compression, encryption, or DRM behavior.

## Next file-side target

1. Use these now-bounded record starts to search for a **group-level owner/header** immediately before the first `+965` record and at each 1,936-byte supergroup boundary.
2. Compare the `+965` five-record groups against neighboring regimes to determine whether the 5-record grouping is local-only or repeated elsewhere.
3. Correlate the mixed `21/24/27` positions with the 48/49 stride class using only structural/aggregate relations; avoid semantic naming.
4. Revisit the `+197 -> +195` -16-byte boundary with the same recurrence test: determine whether a repeated record layout changes by exactly one 16-byte field/island.
5. Do not return to runtime until one of these bounded layouts implies a concrete consume/decode observation.

## Physical Gate log

- Human MODELER operations used for this analysis: **0**.
- Already automated in P4.1: attach to existing MODELER, scan trigger, finish/package, Explorer-select output ZIP.
- Current human runtime lane: launch the P4.1 observer and privately hand off the ZIP.
- Next removable gate: narrow Worker `csmc_observer_capture` starts the fixed observer and detects the ZIP; artifact upload remains a separate bounded capability.
