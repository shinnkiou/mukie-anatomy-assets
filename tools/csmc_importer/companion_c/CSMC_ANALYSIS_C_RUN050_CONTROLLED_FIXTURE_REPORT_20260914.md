# CSMC ANALYSIS COMPANION C — RUN C-050

## QUESTION

Given 13 genuinely new controlled `.csmc` fixtures plus an independent Blender teacher report for VRoid, which serialization differences correlate with geometry complexity, UV edits, material/render-part count, object count, bone count, weight assignment presence/distribution, and weight values — without promoting semantics or touching mainline/runtime?

## NEW INFORMATION

### 1. DATA2 outer framing is now cross-fixture validated

All 13 fixture files are SQLite with one `character` payload row and `CLIP_STUDIO_3D_DATA2` / `character` outer framing. Across all 13:

- u32 at blob offset 53 = `2`
- u32 at offset 57 behaves as logical payload length
- u32 at offset 61 equals bytes after offset 65
- the exact relation is:

`framed_len = 8 + ceil(logical_len / 8) * 8`

This is a VERY-HIGH structural result: the DATA2 body uses an 8-byte framed/padded transform. It does **not** by itself identify encryption/compression semantics.

### 2. A 2456-byte / 307-qword tail cadence appears

A private-derived recurring motif was used only as an internal locator; its raw bytes are not published. The observed periodicity is exactly 2456 bytes (307 qwords).

The longest cadence count is:

- F01/F02/F03/F04/F05: 3
- F06 MAT2: 4
- F07 TWO_CUBES: 4
- R01/R02/R03/R04/R05: 3
- V01 VRoid: 10

For all 13 fixtures, this matches:

`tail cadence count = 2 + render-part count`

where a mesh with no explicit material still contributes one implicit render part, while explicit material partitions contribute one part each.

This is a **HIGH-confidence semantic candidate**, not CONFIRMED semantic binding.

## PAIRWISE EVIDENCE

| Pair | framed delta | qword delta | cadence delta | residual after cadence |
|---|---:|---:|---:|---:|
| F01→F02 | +8 B | +1 | 0 | +1 qword |
| F02→F03 | +256 B | +32 | 0 | +32 qwords |
| F03→F04 | +608 B | +76 | 0 | +76 qwords |
| F03→F05 | +56 B | +7 | 0 | +7 qwords |
| F03→F06 | +2560 B | +320 | +1 | +13 qwords after subtracting 307 |
| F03→F07 | +2656 B | +332 | +1 | +25 qwords after subtracting 307 |
| R01→R02 | +264 B | +33 | 0 | +33 qwords |
| R02→R03 | +72 B | +9 | 0 | +9 qwords |
| R03→R04 | +56 B | +7 | 0 | +7 qwords |
| R04→R05 | -8 B | -1 | 0 | -1 qword |

The F03→F06 and F03→F07 comparisons are especially useful: both add one render-part cadence unit, but after removing that common 307-qword contribution, material-specific residual is +13 qwords while second-object residual is +25 qwords.

## NEGATIVE CONTROLS

- SQLite file size is page-quantized and is therefore a poor semantic-size metric. Character blob logical/framed lengths are preferable.
- Known VRoid teacher counts `10567`, `17944`, `59`, and weight values `1.0` / `0.5` were not found as direct LE/BE 4-byte literals in tested framed payloads. Do not assume teacher values are stored verbatim.
- A 7392-byte exact block shared by F03/F06/F07 also appears unchanged in VRoid. Therefore `shared block == cube geometry stream` is rejected.
- F03→F05 is **not yet a clean UV absence→presence control** because the supplied Blender script does not explicitly remove UV from F03. Treat this pair as UV layout/edit evidence until per-fixture Blender inventory confirms the baseline UV-layer count.
- R04→R05 changes both assignment multiplicity (8→16) and weight values (1.0→0.5), so it does not isolate weight value alone.

## SEMANTIC CANDIDATES

### HIGH — `TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE`

Evidence:

- controlled fixture correlation: PASS
- geometry complexity negative control: PASS
- UV-edit negative control: PASS
- rig/weight negative controls: PASS
- material/object positive controls: PASS
- VRoid independent consistency: PASS (`8` material slots / render parts → cadence `10 = 2 + 8`)

Promotion remains `CANDIDATE_ONLY`.

### MEDIUM — rig/weight differential

Within the fixed 3-cadence cube-rig family:

- no weights → 8 full-weight assignments: +33 qwords
- 1 bone → 2 bones with assignment count fixed: +9 qwords
- same bones / same assignment count, split across two groups: +7 qwords
- split 100% → mixed 50/50: -1 qword, but assignment count also doubles

This is useful for locating rig-sensitive regions but not enough to identify a concrete weight stream.

## REJECTED INTERPRETATIONS

- file size directly equals geometry complexity
- the 7392-byte shared block is cube vertex/index data
- Blender teacher counts are serialized as plain u32/f32 literals
- R04→R05 isolates weight value only
- F03→F05 already proves UV presence/absence

## MAINLINE-USEFUL RESULT

Safe to hand off as reference-only evidence:

- DATA2 outer framing rule
- 2456-byte / 307-qword tail cadence
- HIGH render-part cardinality candidate
- pairwise framed qword deltas
- fixture-design negative controls

Do **not** auto-promote:

- vertex/index/UV/material/bone/weight semantic binding
- Blender emit
- runtime policy

Pipeline remains `STRUCTURAL_ONLY`; semantic promotion count = 0; Blender emit = BLOCKED.

## NEXT QUESTION

Use two new single-variable controls:

1. one mesh with **3 explicit material partitions** — predicted cadence = 5;
2. **3 mesh objects** with no explicit materials — predicted cadence = 5.

For weights, keep assignment cardinality fixed and compare 25/75 vs 50/50 so weight value changes alone. Owner/consumer evidence is still required before any CONFIRMED semantic promotion.
