# CSMC Mainline — Controlled Name-Literal Confounder Probe — 2026-09-14

## Question

Can the known Blender-side source identifiers in the 12 scripted controlled fixtures be separated from geometry/rig differences as literal plaintext name metadata inside the CSMC file?

## Preregistered teacher identifiers

The probe uses only identifiers known from the fixture generator: model/object names, mesh names, armature names, `BONE_001` / `BONE_002`, `MAT_A` / `MAT_B`, and `UV_MAIN` where applicable.

It does not mine arbitrary printable strings and does not post-hoc select coincidental text.

- fixtures tested: **12**
- exact teacher identifiers: **53**
- encodings: ASCII, UTF-16LE, UTF-16BE
- search surfaces: full SQLite file bytes and the `character` BLOB
- exact literal searches: **318**

VRoid is excluded from this literal-name control because the same scripted canonical identifier inventory is not available for all of its imported source internals.

## Observed result

**0 literal occurrences** across all preregistered teacher identifiers, all three encodings, and both search surfaces.

Per-fixture result is also 0/0 for full file and character BLOB.

## Interpretation

Accepted negative-control result:

`SOURCE_IDENTIFIER_PLAINTEXT_ASCII_UTF16_NOT_OBSERVED`

This rejects a narrow explanation: the known source identifiers are not present as straightforward ASCII / UTF-16LE / UTF-16BE literals in these 12 CSMC fixtures.

It does **not** prove names are absent from the serialization. They may be transformed, compressed/encoded, remapped, omitted, or stored under Modeler-generated identities. No codec/cipher claim is made.

## Confounder consequence

- Random printable runs in the opaque payload must not be labeled `NAME_METADATA` just because they look textual.
- Current source-name confounders cannot be removed by simple plaintext string carving.
- Pair differences remain potentially contaminated by identity/name effects until a same-identity control or stronger owner/consumer relation exists.
- Therefore current `I3_PARTIAL` pairs stay partial.

This result narrows the confounder-separation strategy: use controlled same-identity fixtures and structural relationship evidence, not arbitrary string extraction.

## Gate state

- pipeline: `STRUCTURAL_ONLY`
- semantic promotion count: 0
- name metadata region confirmed: false
- geometry/index: unresolved
- Blender emit: blocked
- MODELER/runtime/Worker/Canary/Control Gate actions: 0
