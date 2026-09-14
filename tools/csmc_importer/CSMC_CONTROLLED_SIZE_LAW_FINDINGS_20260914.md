# CSMC Mainline — Bounded Size/Stride Relationship Screen — 2026-09-14

## QUESTION

After exact-qword reuse was ruled out inside the tested phase-normalized variable prefixes, can a small preregistered family of simple fixed-stride size laws explain the controlled geometry or rig growth?

## HYPOTHESIS FAMILY

The hypothesis family is deliberately bounded before evaluation.

Single-count whole-stored models:
- `stored = overhead + N * stride`
- `N ∈ {vertices, triangles, corners}`
- geometry stride candidates: `{4, 8, 12, 16}` bytes

Rig single-count whole-stored models:
- `N ∈ {bones, weight_assignments}`
- stride candidates: `{4, 8, 12, 16}` bytes

Rig two-factor model:
- `stored = overhead + bones * bone_stride + weight_assignments * weight_stride`
- both stride candidates: `{4, 8, 12, 16}` bytes

Same-phase F02↔F04 geometry-prefix models:
- observed bounded prefix growth: `(510 - 402) qwords = 864 bytes`
- teacher deltas: `Δvertices=22`, `Δtriangles=46`, `Δcorners=138`
- pure count stride candidates: `{4, 8, 12, 16}` bytes
- vertex stride candidates: `{12,16}` bytes
- corner/index width candidates: `{2,4}` bytes
- triangle stride candidates: `{4,8,12,16}` bytes

No arbitrary coefficient search or post-hoc widening is allowed.

## OBSERVED RESULT

### Geometry F01/F02/F03/F04 whole stored length

No exact model exists for vertices, triangles, or corners times `{4,8,12,16}` with one fixed overhead derived from the baseline.

### Same-phase F02 QUAD ↔ F04 CUBE_SUBDIV

The exact invariant suffix is already established. Therefore the complete stored-length growth is localized before that suffix:

- variable-prefix growth = **864 bytes**
- teacher deltas = `22 vertices`, `46 triangles`, `138 corners`

No exact model exists in the preregistered set for:
- one count × fixed stride
- `Δvertices * {12,16} + Δcorners * {2,4}`
- `Δvertices * {12,16} + Δtriangles * {4,8,12,16}`

### Rig R01-R05 whole stored length

No exact model exists for:
- bone count × `{4,8,12,16}`
- weight-assignment count × `{4,8,12,16}`
- bone count + weight-assignment count with both strides in `{4,8,12,16}`

This agrees with the existing R04→R05 negative control: weight assignments increase 8→16 while stored size decreases by 8 bytes.

## INTERPRETATION

Classification: `WHOLE_STORED_AND_PHASE_PREFIX_SIZE_NOT_SINGLE_SIMPLE_FIXED_STRIDE_ARRAY`.

This rejects a narrow class of naive direct-array explanations. It does **not** prove that vertices, indices, bones, or weights are absent from the prefix. The serializer may contain multiple coupled streams, metadata, transformed data, per-object/per-part overhead, variable-width records, or another structural owner. No codec/cipher/compression claim is made.

## IMPORTER CONSEQUENCE

The next geometry/index search should not treat whole stored length or the F02/F04 phase-normalized prefix length as one flat vertex/index array with an obvious fixed stride. The structural search mask remains useful, but semantic localization now needs internal segmentation/relationship evidence rather than another whole-region size fit.

## CONFIDENCE / GATE

- exact-qword prefix reuse: rejected for tested pairs
- simple fixed-stride whole-region size law: rejected for bounded candidate family
- geometry stream: UNRESOLVED
- index/topology stream: UNRESOLVED
- bone/weight direct fields: UNCONFIRMED
- semantic promotion count: 0
- Blender emit: BLOCKED
- runtime dispatch: false

## NEXT ACTION

Stay inside the phase-normalized candidate regions and search for internal sub-block boundaries whose individual lengths, repetition counts, or local growth obey the already-preregistered teacher relationships. Do not fit the whole prefix as one stream and do not widen the stride family post hoc.
