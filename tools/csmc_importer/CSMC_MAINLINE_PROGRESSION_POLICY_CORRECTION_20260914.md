# CSMC MAINLINE PROGRESSION POLICY CORRECTION — 2026-09-14

## Canonical interpretation

`PHYSICAL_ORACLE_PENDING` and `EXPLICIT_SERIALIZER_FIELD_READ=UNRESOLVED` are **semantic-promotion gates**, not a global pause of the importer mainline.

Current state:

- mainline: `ACTIVE`
- structural development: `ACTIVE`
- semantic promotion: `CLOSED` / count `0`
- Blender emit: `BLOCKED`
- physical oracle: `PENDING_MANUAL_ORACLE`
- broad blind semantic expansion: `BLOCKED`
- oracle-independent importer / structural work: `AUTHORIZED`

## Block only these actions

- geometry/index semantic `CONFIRMED`
- UV/material/bone/weight semantic `CONFIRMED`
- Blender production emit
- visual result used as semantic proof
- Importer Lab score used as semantic proof
- blind Phase-10 or equivalent family expansion
- re-search of already rejected families without genuinely new independent evidence
- inference/fabrication of unobserved physical-oracle outcomes

## Continue these mainline actions

1. Importer intake / Structural IR bridge strengthening
2. fail-closed validation and regression tests
3. admission of new Structural Facts
4. non-semantic intake of Lab `STRUCTURAL_CANDIDATE` / `CODEC_CANDIDATE`
5. proof-grade evidence packet schema preparation
6. `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH` admission-gate implementation and validation
7. direct MODELER Static evidence admission-path preparation
8. same-identity fixture teacher/provenance/admission preparation
9. candidate -> discriminating-question handoff preparation
10. importer CI / smoke / guard strengthening

## Local blocking rule

When a task reaches a point that requires new semantic evidence, mark **that task only** `BLOCKED_BY_EVIDENCE` and continue with the next oracle-independent mainline task.

Do not lower the whole mainline to `maintenance-only` solely because the physical oracle or serializer-field proof is pending.

## Machine-enforced representation

`csmc_p4_next_evidence_gate.py` v4 now separates:

- `status` from `evidence_status`
- `mainline_state=ACTIVE`
- `structural_development=ACTIVE`
- `semantic_gate=CLOSED`
- `oracle_pending_is_global_pause=false`
- `maintenance_only=false`
- `oracle_independent_importer_structural_work=AUTHORIZED`
- `broad_blind_semantic_expansion=BLOCKED`

No semantic evidence, physical observation, Blender authorization, runtime dispatch, MODELER save/serialization action, Worker/Canary/Control Gate mutation, Production/STABLE mutation, or RIO-26 mutation is created by this policy correction.
