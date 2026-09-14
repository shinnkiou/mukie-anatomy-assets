# CSMC ANALYSIS COMPANION C — RUN C-064
## Render-part residual localization reconciliation — 2026-09-14

### Scope

C-064 is a **reference-only structural reconciliation** of genuinely new public-safe mainline evidence. It does not reacquire private CSMC bytes and it does not repeat the earlier C-050 all-pair search.

Source mainline state:
- branch: `csmc-importer-experimental-20260902`
- source head: `b4052f282d48508b8f8573d49b9240cf74ff2697`
- findings commit: `1732f8c5918c8f9c46b812c8d33d61cf5c5d3e00`
- aggregate commit: `5d09201522ab995676c34830a39e80172c739d8d`
- source CI: `34825791598` SUCCESS

### New structural evidence admitted

The existing Level-4 `TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE` is refined, not promoted.

A public-safe exact triple-common block spans **924 qwords / 7392 bytes** at qword starts F03=442, F06=453, F07=465. The same block also occurs in V01 at qword 531781. This recurrence is evidence for structural reuse; it is not a proof of geometry semantics.

Relative to F03, the aligned common block begins +88 bytes later in F06 and +184 bytes later in F07. Therefore F07 differs from F06 by a **96-byte pre-common shift**.

Logical-length differences are:
- F03→F06: +2555 bytes
- F03→F07: +2651 bytes
- F06→F07: +96 bytes

After removing the pre-common shift, both F03→F06 and F03→F07 have identical **+2467-byte post-common growth**, which decomposes exactly as:

`2467 = 2456 cadence bytes + 11 other bytes`

This narrows the structural location of the prior cadence relationship, but does not name the 88/184/96-byte regions as material or object records.

### New bounded negative control

The source tested a preregistered direct-scalar family in the final 2048 bytes before validated phase-core boundaries. Across u8/u16/u32, LE/BE where applicable, and targets `render_part_count` or `cadence_count`, **40,928 configurations** were evaluated with **0 hard passes**.

C-064 therefore records only this narrow rejection:

`DIRECT_RAW_SHARED_BOUNDARY_RELATIVE_SCALAR_ONLY`

It does not reject transformed, encoded, indirect, variable-position, nested-counted, padding-bearing, or consumer-derived representations.

### Companion C interpretation

This is sufficient new evidence for a numbered run because it adds both:
1. a new positive structural localization/decomposition around the Level-4 cadence candidate; and
2. a preregistered bounded negative control eliminating a direct shared scalar family.

It is **not** sufficient for semantic promotion. The following remain unresolved:
- geometry
- index/topology
- explicit serializer field-read binding
- controlled fixture → consumer match

### Gate

- pipeline: `STRUCTURAL_ONLY`
- semantic promotion count: 0
- Blender emit: BLOCKED
- runtime dispatch: false
- MODELER actions: 0
- Worker/Canary/Control Gate actions: 0
- RIO-26 mutation: 0
- mainline mutation: 0
- automatic integration: false
- raw/private publication: false

### Next evidence preference

The highest-value unresolved evidence remains a proof-grade `EXPLICIT_SERIALIZER_FIELD_READ` or the already-preregistered read-only 30-variant F02 MODELER oracle. Absent those, future static work should use a structurally distinct family with a fresh validation split rather than widening rejected families post hoc.
