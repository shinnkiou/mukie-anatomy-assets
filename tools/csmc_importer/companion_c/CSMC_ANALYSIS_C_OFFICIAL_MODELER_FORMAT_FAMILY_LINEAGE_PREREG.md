# CSMC ANALYSIS COMPANION C — OFFICIAL MODELER FORMAT-FAMILY LINEAGE PREREGISTRATION V2

Status: UNNUMBERED / REFERENCE-ONLY / NOT C-069
Pipeline: STRUCTURAL_ONLY

## Official generation constraints

CELSYS official CLIP STUDIO MODELER release notes establish multiple product-generation boundaries relevant to future control-corpus design.

### Ver.1.6.0 family genesis

As CLIP STUDIO COORDINATE functionality was integrated, the following MODELER-side file formats were introduced/changed together:

- `csmf` — MODELER shape file
- `csmc` — MODELER character file
- `csmo` — MODELER object file
- `csms` — MODELER background file

The same official note records a compatibility boundary: character-format `cmo` files from Ver.1.0.2 and earlier cannot be read as character files by Ver.1.6.0, while older non-character CMO files can be opened and registered into the new-format material path.

### Ver.1.6.3 object-branch complexity change

Official release notes state that the object setup screen gained support for multiple 3D models and editable node parent-child relationships. This is a product-level feature boundary only; it does not by itself prove a serialized field or grammar change.

### Ver.1.8.0 object/background material integration

Official release notes state that 3D object materials and 3D background materials were integrated into 3D object materials and the background setup screen was merged into the object setup screen. They also state that 3D object materials created by MODELER Ver.1.8.0 or later cannot be read by pre-1.8.0 PAINT/MODELER, while 3D character materials and 3D shape materials remain readable by pre-1.8.0 versions.

This is a material/product compatibility boundary. It must NOT be restated as proof that `csmo`, `csms`, `csmc`, or `csmf` byte grammar changed at that version unless actual bytes demonstrate it.

Official source: https://www.clipstudio.net/ja/modeler/

## Why this is new but not evidence-grade

Existing project material already records role-level facts such as MODELER opening/saving `csmc`, `csmo`, `csms`, and the `csmc`↔`cs3c` project/export distinction. Those facts are not re-counted.

The registered constraint is the product lineage and compatibility stratification. It makes sibling formats and producer-version cohorts legitimate future controls, but it does NOT prove a shared serializer, container grammar, record layout, encryption/packing scheme, field identifiers, offsets, or semantic payloads.

## Frozen future control design

Every future sibling/target fixture admitted to this axis must record at minimum:

- exact extension / artifact class
- producer MODELER version when known
- source/provenance and content identifier
- acquisition route and license/usage constraints
- exact byte size and SHA-256 after legitimate acquisition
- whether the sample predates or postdates the Ver.1.8.0 object/background material integration boundary
- feature usage relevant to object hierarchy where known

Do not combine pre/post generation cohorts as equivalent controls without first testing version sensitivity.

H0: no reproducible format-family structural scaffold exists beyond generic/coincidental file structure.

H1: at least two independently acquired fixtures show reproducible family-shared structural relationships that survive fixture variation and can be separated from format-specific regions.

Permitted observations are structural only: file framing, deterministic outer markers, alignment/cadence, stable container/table relationships, repeated family-level metadata patterns, and bounded cross-format invariants.

Forbidden inference from sibling agreement alone: geometry, vertex/index semantics, bone/weight semantics, material/UV semantics, serializer-field meaning, owner/consumer identity, or CSMC importer readiness.

## Public acquisition candidates — discovery only

These are NOT acquired fixtures and MUST NOT be counted as evidence.

1. CLIP STUDIO ASSETS Content ID `1681090` (`瓶02_V2`): public page is Free and states output/setup with MODELER Ver.1.6.0 in `csmf` format.
2. CLIP STUDIO ASSETS Content ID `2192736` (`Male Body - Gakuran Suit B`): public page is Free and explicitly states that it is a `.csmc` character file.
3. CLIP STUDIO ASSETS Content ID `2299006` (`Signboard`): public page is Free and states an approximate `.csmo` file size.

No candidate above has been downloaded or byte-inspected by this Companion lane. `Free` does not mean public-domain or freely redistributable. Any later acquisition must use the authorized CLIP STUDIO route and respect the material's current usage terms. Raw asset bytes must not be mirrored into public research artifacts.

A bounded public search found no comparable `csms` candidate suitable for automatic acquisition. Absence from that search is not evidence that none exists.

## Admission contract

A future sibling/target-format result may become a numbered Companion run only if all of the following hold:

1. actual fixture bytes are legitimately acquired and provenance-recorded;
2. license/usage constraints allow the intended local analysis and no prohibited redistribution occurs;
3. the result is reproducible across more than one independent fixture where the claim requires cross-fixture stability;
4. producer-version effects are controlled or explicitly bounded;
5. the observation changes, rejects, or materially constrains a live CSMC structural hypothesis;
6. public format names and public candidate descriptions do not guide or score the already-sealed blind F02 consumer-discovery lane;
7. no semantic promotion is inferred from family-level structural similarity.

Until then:

- sibling/target public fixture bytes acquired = 0
- sibling cross-format observations = 0
- public candidate byte inspections = 0
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
