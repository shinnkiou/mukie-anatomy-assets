# CSMC Controlled Fixture Mainline Findings — 2026-09-14

## QUESTION
Can the new 13-fixture controlled corpus convert the previous no-new-evidence state into admissible file-side evidence and advance Structural IR/importer work without runtime?

## INTAKE

- Corpus: `CSMC_CONTROLLED_FIXTURES_20260914`
- Fixture count: 13
- ZIP SHA-256: `be6132ef83959167ffd19218810e099f0bd164714fbd1ec4770f9296b38643b6`
- Raw CSMC policy: private only; never commit raw bytes to public GitHub.
- All fixtures are valid SQLite databases containing one `character` table row.
- No `scene` table is present in this corpus.

## FRAME RESULT

- The earlier wording “65 fixed bytes” is corrected: **bytes 0..56 (57 bytes) are byte-identical across 13/13**.
- Bytes 57..60 are a little-endian logical length.
- Bytes 61..64 are a little-endian stored length.
- The variable payload begins at byte 65.
- The previously suspected 16-byte rounding does **not** hold across the corpus.
- Exact relation on 13/13, including VRoid: `stored_length = align8(logical_length) + 8`.
- The bytes between logical and stored boundaries are non-zero/high-entropy and are therefore kept as `TAIL_BETWEEN_LOGICAL_AND_STORED`; they are not called literal padding.
- Same logical-length remainder classes show repeated terminal 8-byte blocks in multiple fixtures. This supports an 8-byte block-aligned deterministic transform/serializer phase candidate, but no cipher/codec name is assigned.

## CONFOUNDER SEPARATION

- Exact UTF-8/UTF-16LE searches do not expose fixture IDs, `BONE_001`, `BONE_002`, `MAT_A`, `MAT_B`, `UV_MAIN`, or `Face` as trustworthy plaintext inside the character BLOB.
- Therefore identity/name metadata cannot yet be localized and removed. It remains an uncontrolled confound inside the opaque variable region.
- Direct numeric coincidences for known VRoid counts or f32 0/0.5/1.0 are not treated as semantic evidence.

## GEOMETRY FAMILY

- `CSMC_F01_TRIANGLE`: vertices=3, triangles=1, logical_length=17674
- `CSMC_F02_QUAD`: vertices=4, triangles=2, logical_length=17687
- `CSMC_F03_CUBE`: vertices=8, triangles=12, logical_length=17942
- `CSMC_F04_CUBE_SUBDIV`: vertices=26, triangles=48, logical_length=18551
- Logical length rises monotonically across F01→F02→F03→F04, so `GEOMETRY_COMPLEXITY_CORRELATION` is accepted at confidence Level 1.
- Pre-registered whole-length laws using vertex/triangle strides 4/8/12/16 (and triangle-corner strides 2/4/8/12/16) produce **no exact law across all four fixtures**. Therefore no vertex/index stream is promoted from total size.
- F02→F03 also changes Blender construction route (`from_pydata` → primitive cube) and potentially primitive defaults; it is not a pure geometry-only pair.

## UV PAIR

- `F03_CUBE ↔ F05_CUBE_UV` is accepted as an **I3_PARTIAL UV-layout differential**, not an UV ON/OFF proof. F05 explicitly runs Smart Project and renames the active layer `UV_MAIN`; F03 was not explicitly stripped of primitive UV defaults.
- Logical delta: +55 bytes. Stable exact 8-byte substructure remains, but no UV field is localized. Confidence: Level 2 candidate; semantic promotion remains false.

## MATERIAL PAIR

- `F03_CUBE ↔ F06_CUBE_MAT2`: adds two material definitions and polygon material assignments. Logical delta: +2,555 bytes.
- Strong exact block reuse coexists with new/shifted regions, showing deterministic segmented serialization. Material definition vs per-face assignment is not separated. Confidence: Level 2 candidate.

## OBJECT / CONTAINER PAIR

- `F03_CUBE ↔ F07_TWO_CUBES`: adds a second object and duplicates cube geometry. Logical delta: +2,651 bytes.
- Object-wrapper and geometry-volume effects are inseparable in this pair. Confidence: Level 2 candidate, not I4 closure.

## RIG / WEIGHT FAMILY

- `CSMC_R01_CUBE_B1_W0`: bones=1, weight_assignments=0, logical_length=17855
- `CSMC_R02_CUBE_B1_W100`: bones=1, weight_assignments=8, logical_length=18117
- `CSMC_R03_CUBE_B2_W100`: bones=2, weight_assignments=8, logical_length=18185
- `CSMC_R04_CUBE_B2_SPLIT`: bones=2, weight_assignments=8, logical_length=18243
- `CSMC_R05_CUBE_B2_MIX50`: bones=2, weight_assignments=16, logical_length=18234
- R01→R02 (+262): weight-presence/assignment candidate.
- R02→R03 (+68): bone-count/hierarchy candidate.
- R03→R04 (+58): assignment-target pattern candidate at fixed 2-bone count and fixed assignment count.
- R04→R05 (**−9**): assignment count doubles 8→16 while payload shrinks. This is a useful negative control: whole payload size cannot be a monotonic proxy for weight-assignment count.
- No localized same-position scalar field responding 1.0→0.5 has yet been proven; `weight_scalar` remains Level 2 candidate only.

## VROID INDEPENDENT VALIDATION

- Teacher labels: meshes=2, vertices=10,567, triangles=17,944, bones=59, weight assignments=17,680, UV layers=2, material slots=8, shape keys=58.
- The simple-fixture **envelope grammar predicts VRoid without modification**: same 57-byte fixed prefix, same length-field offsets, same payload offset 65, same `align8(logical)+8` relation. This independently validates the container/envelope parser.
- No simple-fixture content semantic law currently predicts VRoid vertex/index/bone/weight counts. Therefore no content semantic reaches Level 4.
- Shape-key/morph remains candidate-only because there is no morph-only controlled pair.

## I3 EVALUATION

- All 10 preregistered primary pairs have hashes, provenance, reproducible reads, and an interpretable intended change.
- All 10 are currently `I3_PARTIAL`, not `I3_VALID`, because fixture/file/object identities differ and that metadata cannot yet be isolated from the opaque payload.
- This corpus is still **genuinely new admissible structural evidence**; I3_PARTIAL prevents direct semantic unlock, not structural analysis.

## NEXT-EVIDENCE GATE

- Previous `NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS` applied to the old corpus.
- A validated controlled-fixture intake should route as `NEW_ADMISSIBLE_CONTROLLED_EVIDENCE`.
- Existing I1/I2/I3/I4/raw-pair routes remain intact.
- Runtime dispatch remains false; semantic promotion remains false unless a separate confidence validator authorizes it.

## STRUCTURAL IR INTEGRATION

- Preserve Structural IR v0.1 meanings unchanged.
- Add controlled-evidence metadata in a separate optional document/schema rather than relabeling existing qword families.
- Suggested fields: `evidence_source`, `controlled_fixture_ids`, `relationship_type`, `negative_control_ids`, `candidate_semantic`, `confidence_level`, `validation_status`.

## IMPORTER NEXT ACTIONABLE SLOT

- **Outer controlled-envelope parser is now implementable and independently validated**: SQLite `character` route, magic/kind/version, logical/stored lengths, offset 65, `align8(logical)+8` invariant.
- Geometry/index mesh emit remains blocked because vertex/index streams are not confirmed.
- The practical next importer step is therefore safe container parsing + evidence attachment, not Blender mesh generation.

## REJECTED EXPLANATIONS

- Rejected: “all 65 header bytes are constant”.
- Rejected: “stored payload is 16-byte rounded”.
- Rejected: “total payload size directly equals weight-assignment count”.
- Rejected: numeric coincidence alone as semantic proof.
- Not established: AES/Blowfish/any named cipher or compression codec.

## CURRENT MAINLINE STATE

- Pipeline: `STRUCTURAL_ONLY`
- Semantic promotion count: 0
- Blender emit: BLOCKED
- MODELER/runtime/Worker operations during this analysis: 0
