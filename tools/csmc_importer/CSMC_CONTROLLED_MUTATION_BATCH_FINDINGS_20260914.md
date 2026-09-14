# CSMC Mainline — Controlled Mutation Batch v1 — 2026-09-14

## PURPOSE

Prepare a bounded Modeler-oracle experiment without assigning semantics to opaque CSMC bytes.

Base fixture: `CSMC_F02_QUAD.csmc`

Verified base SHA-256: `d7b36076348035a6965890ee19c00f5487de94aa6db5b23ff2459b75ae815eab`

The base is part of the authorized controlled fixture corpus. The generated raw mutation files are kept private and are not committed to public GitHub.

## PREREGISTERED STRUCTURAL LANDMARKS

- logical length: 17,687 bytes
- stored length: 17,696 bytes
- payload offset in character BLOB: 65 bytes
- proven same-phase invariant start: payload byte 3,216 (`qword 402`)
- aligned logical length: 17,688 bytes
- final framing remainder: payload bytes 17,688..17,695

No semantic meaning is assigned to the invariant core, the alignment-extension byte, or the final 8-byte framing remainder.

## MUTATION RULE

Exactly 30 variants were generated.

Each variant changes **exactly one byte of the extracted `character.character` BLOB** by XOR `0x01` and keeps:

- SQLite container readable
- character row count = 1
- BLOB length unchanged
- logical/stored length fields unchanged
- validated `stored = align8(logical) + 8` arithmetic unchanged

The generator verifies by readback that the extracted character BLOB differs from the base at exactly one byte.

## MUTATION GROUPS

- 10 × `PREFIX_INTERIOR`
- 7 × `INVARIANT_BOUNDARY`
- 4 × `INVARIANT_INTERIOR`
- 1 × `ALIGNMENT_EXTENSION`
- 8 × `FRAMING_REMAINDER`

This is a bounded structural sensitivity screen, not a semantic field claim.

## MODELER ORACLE CLASSES

For each variant record only observable outcomes:

- `LOAD_REJECTED`
- `LOAD_OK_VISUAL_SAME`
- `LOAD_OK_VISUAL_CHANGED`
- optional save-normalization result if a re-save is performed

Do not infer vertex/index/bone/material meaning from one accepted or rejected byte by itself. Repeated regional behavior is required before promoting any hypothesis.

## PUBLIC / PRIVATE SPLIT

Public GitHub contains only:
- generator code
- public-safe manifest with offsets/hashes/categories
- this findings note

Private Drive contains:
- 30 mutated `.csmc` files
- the public-safe manifest bundled beside them

No proprietary raw CSMC bytes are committed to public GitHub.

## GATE

- pipeline: `STRUCTURAL_ONLY`
- semantic promotion count: 0
- Blender emit: BLOCKED
- runtime dispatch: false
- Modeler results: PENDING
