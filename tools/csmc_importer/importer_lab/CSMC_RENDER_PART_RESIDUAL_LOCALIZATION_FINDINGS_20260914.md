# CSMC Importer Lab — render-part residual localization follow-up — 2026-09-14

## Scope

Private authorized controlled fixture bytes were read locally from corpus SHA-256:

`be6132ef83959167ffd19218810e099f0bd164714fbd1ec4770f9296b38643b6`

No raw CSMC bytes, motif bytes, decryption material, or proprietary model content are embedded in this report.

Pipeline remains `STRUCTURAL_ONLY`.
Semantic promotion remains `false`.
Blender emit remains `BLOCKED`.

This is a targeted follow-up to the already accepted Level-4 `TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE`; it does not rerun the earlier all-pair C-050 search.

## New structural localization

For F03/F06/F07, an exact triple-common block of **924 qwords / 7392 bytes** was located by exact 307-qword window continuity and raw in-memory equality verification.

Public-safe qword starts:

- F03 CUBE: 442
- F06 CUBE_MAT2: 453
- F07 TWO_CUBES: 465

The same 7392-byte block occurs in V01 VRoid at qword **531781**, reinforcing the existing negative control that this shared block is not identifiable as cube geometry.

The common-block start shift relative to F03 is:

- F06: **+88 bytes**
- F07: **+184 bytes**

Therefore F07 vs F06 differs by exactly **+96 bytes** before the aligned shared region.

Separately, F06 and F07 have an exact same-phase suffix alignment:

- F06 start qword 445
- F07 start qword 457
- exact length 2118 qwords

Again, the variable-prefix delta is **96 bytes** and all aligned bytes after that boundary remain exact through the validated suffix.

## Refined cadence decomposition

Logical length deltas:

- F03 -> F06: **+2555 bytes**
- F03 -> F07: **+2651 bytes**
- F06 -> F07: **+96 bytes**

After subtracting the pre-common-block shift:

- F03 -> F06 post-common logical growth: **+2467 bytes**
- F03 -> F07 post-common logical growth: **+2467 bytes**

Both decompose identically as:

`2467 = 2456 cadence bytes + 11 other bytes`

Thus the prior `+13 qword` / `+25 qword` framed residual can be refined structurally:

- one additional render-part cadence contributes a shared **2456-byte** growth;
- both F06 and F07 also share **+11 logical bytes** outside that cadence after the common block;
- the material-partition vs second-object distinction is isolated to the pre-common-block prefix shift: **88 vs 184 bytes**, with F07 exceeding F06 by **96 bytes**.

This is structural localization only. It does not name the 88/184/96-byte regions as material/object records.

## Boundary-relative direct scalar negative control

A preregistered bounded scalar family was tested only in the last **2048 bytes before validated phase-core boundaries**.

Positive-contrast phase sets:

- phase 1: F06 render parts=2, F07=2, R03=1
- phase 3: R04=1, V01=8

Targets:

- `render_part_count`
- `cadence_count = render_part_count + 2`

Representations:

- u8
- u16 LE/BE
- u32 LE/BE
- every byte-relative start within the 2048-byte window

Candidate configurations evaluated: **40,928**
Hard passes: **0**

Therefore the following narrow family is rejected:

> a direct raw u8/u16/u32 scalar equal to render-part count or cadence count, stored at one common boundary-relative offset inside the last 2048 bytes before the validated phase-core boundary.

This does **not** reject transformed, encoded, indirect, variable-position, counted-record, or consumer-derived representations.

## State

- `TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE`: remains **Level 4**, refined but not promoted.
- direct boundary-relative count scalar: **bounded family rejected**
- geometry: UNRESOLVED
- index/topology: UNRESOLVED
- serializer field-read binding: UNRESOLVED
- controlled fixture -> consumer match: UNRESOLVED
- semantic promotion count: 0
- Blender emit: BLOCKED

## Reproducibility

Probe code is public-safe: it contains no raw fixture bytes and emits only hashes, lengths, offsets, counts and pass/fail summaries.

Public-safe derived aggregate SHA-256: `3a09ac35d40a254b6e6fc3bbf1e004505d02ca732eb931152fbc618c1df3fc66`
Probe SHA-256: `ce62ff38062ea3e90c61ac06528d255c4678498310d696954f73e657c1f35fe8`
