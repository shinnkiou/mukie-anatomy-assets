# CSMC ANALYSIS COMPANION C — OFFICIAL MODELER FORMAT-FAMILY LINEAGE PREREGISTRATION

Status: UNNUMBERED / REFERENCE-ONLY / NOT C-069
Pipeline: STRUCTURAL_ONLY

## New public-safe constraint

CELSYS official CLIP STUDIO MODELER release notes for Ver.1.6.0 state that, as CLIP STUDIO COORDINATE functionality was integrated, the following MODELER-side file formats were introduced/changed together:

- `csmf` — MODELER shape file
- `csmc` — MODELER character file
- `csmo` — MODELER object file
- `csms` — MODELER background file

The same official note also records a generation boundary: character-format `cmo` files from Ver.1.0.2 and earlier cannot be read as character files by Ver.1.6.0, while older non-character CMO files can be opened and registered into the new-format material path.

Official source: https://www.clipstudio.net/ja/modeler/
Relevant section: Ver.1.6.0 release notes, lines describing `csmf`, `csmc`, `csmo`, `csms`, and the old `cmo` compatibility boundary.

## Why this is new but not evidence-grade

Existing project material already records role-level facts such as MODELER opening/saving `csmc`, `csmo`, `csms`, and the `csmc`↔`cs3c` project/export distinction. This preregistration does not re-count those facts.

The new constraint is narrower: the four MODELER project/setup formats share a documented product-generation event in Ver.1.6.0. This makes sibling formats a legitimate future control-corpus design axis, but it does NOT prove they share a serializer, container grammar, record layout, encryption/packing scheme, field identifiers, offsets, or semantic payloads.

## Frozen future test

If legally usable, independently acquired sibling-format fixtures become available, test the following without modifying the existing sealed F02 blind lane.

H0: no reproducible format-family structural scaffold exists beyond generic/coincidental file structure.

H1: at least two sibling MODELER formats exhibit reproducible family-shared structural relationships that survive independent fixtures and can be separated from format-specific regions.

Permitted observations are structural only: file framing, deterministic outer markers, alignment/cadence, stable container/table relationships, repeated family-level metadata patterns, and bounded cross-format invariants.

Forbidden inference from sibling agreement alone: geometry, vertex/index semantics, bone/weight semantics, material/UV semantics, serializer-field meaning, owner/consumer identity, or CSMC importer readiness.

## Admission contract

A future sibling-format result may become a numbered Companion run only if all of the following hold:

1. actual fixture bytes are legitimately acquired and provenance-recorded;
2. the result is reproducible across more than one independent fixture where the claim requires cross-fixture stability;
3. the observation changes, rejects, or materially constrains a live CSMC structural hypothesis;
4. public format names do not guide or score the already-sealed blind F02 consumer-discovery lane;
5. no semantic promotion is inferred from family-level structural similarity.

Until then:

- sibling bytes acquired = 0
- sibling cross-format observations = 0
- direct CSMC evidence added = false
- proof-grade consumer edges added = 0
- EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED
- CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED
- F02 physical observations = 0/30
- semantic promotion count = 0
- Blender emit = BLOCKED
- runtime dispatch = false
- C-069 authorized = false

## Isolation

No MODELER execution, Save/Save As/Ctrl+S, serialization trigger, Windows Worker, Canary, Control Gate, Production/STABLE, mainline, or RIO-26 mutation is authorized or performed by this preregistration. No raw/private CSMC bytes are published.
