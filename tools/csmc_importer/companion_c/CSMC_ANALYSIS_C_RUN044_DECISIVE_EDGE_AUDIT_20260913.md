# Companion C — Run C-044 — decisive owner-edge audit

## QUESTION
After outer-route reconciliation, do existing public-safe route/schema facts satisfy any of the three decisive owner edges for `BND_197_TO_195`?

Required decisive edges from the current owner-scope matrix:
- `EXPLICIT_PARENT_RECORD_BOUNDARY`
- `EXPLICIT_PARENT_LENGTH_FIELD`
- `EXPLICIT_CONSUMER_CROSSREF`

## STATIC EVIDENCE AUDIT
Existing useful references were classified by scope rather than by name similarity.

### `Canvas3DModelBank.FirstLoaderIndex -> Canvas3DModelLoader`
This is a **live explicit container-level cross-reference** and closes the BankData route question. It does not identify a consumer of the local `+197 -> +195` boundary. Therefore it cannot satisfy `EXPLICIT_CONSUMER_CROSSREF` for that boundary.

### `ModelInfo3D.ModelNodeInfoFirstIndex -> ModelNodeInfo3D`
This is a useful historical/schema relationship, but both `ModelInfo3D` and `ModelNodeInfo3D` are `SCHEMA_ONLY` in the exact target. It is not a live boundary-local parent record edge.

### `ModelInfo3D.ModelNodeInfoCount`
This is a schema-only cardinality field, not a verified length field enclosing the `+197/+195` local barrier.

### Current result
Satisfied decisive owner edges: **0 / 3**.

Missing remains exactly:
- `EXPLICIT_PARENT_RECORD_BOUNDARY`
- `EXPLICIT_PARENT_LENGTH_FIELD`
- `EXPLICIT_CONSUMER_CROSSREF`

The important narrowing is that generic container linkage is no longer confused with a boundary-local consumer cross-reference.

## IMPLEMENTATION
Added `csmc_analysis_c_decisive_edge_audit.py`.

A decisive edge is counted only when it is:
1. one of the three preregistered edge types;
2. explicitly tied to `BND_197_TO_195`;
3. `LIVE_BOUNDARY_LOCAL` evidence;
4. explicit rather than inferred from names or schema registration.

## SYNTHETIC TEST
7/7 PASS:
- current container-level Bank->Loader crossref is rejected as boundary-decisive;
- schema-only ModelInfo first-index is rejected as boundary-decisive;
- schema-only ModelInfo count is rejected as boundary-decisive;
- current satisfied edge set remains empty;
- all three missing edges remain explicit;
- owner/semantic state stays unresolved and no runtime dispatch is requested;
- a synthetic truly live boundary-local parent-length edge is recognized.

## NEW INFORMATION
Outer route exhaustion and boundary-owner exhaustion are separate. File-route discovery is closed, but the owner-scope static gate still has three precisely named missing edges.

## CLOSED HYPOTHESES
- any explicit cross-reference in the 3D schema satisfies the local consumer edge: REJECTED.
- `ModelNodeInfoFirstIndex` can be imported as live parent evidence despite schema-only status: REJECTED.
- `ModelNodeInfoCount` can be treated as the parent length of the +197/+195 barrier without a live binding: REJECTED.
- route closure itself proves owner scope: REJECTED.

## CONFIDENCE CHANGES
- distinction between container-route crossref and boundary-consumer crossref: HIGH -> VERY HIGH.
- owner-scope proof: remains INCOMPLETE, 0/3 decisive edges.
- semantic owner: UNRESOLVED.
- runtime dispatch requested: false.
- Blender emit: BLOCKED.
