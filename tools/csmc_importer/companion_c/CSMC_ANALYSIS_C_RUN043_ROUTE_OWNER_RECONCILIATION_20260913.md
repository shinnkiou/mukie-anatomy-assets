# Companion C — Run C-043 — route / owner reconciliation

## QUESTION
Does newer public-safe P1/P2 evidence close the two external-route unknowns retained by C-006, and if so does that also identify the internal owner at `BND_197_TO_195`?

## INPUTS
Reference-only cross-lane evidence; no mainline mutation:
- Supabase durable row 16 `CSMC_REAL_TARGET_P1_P2_COMPLETE_20260912`.
- GitHub checkpoint commit `84ac3d83a3ccca9ec545374b11e4b585c018e287`.
- public-safe P4 owner-scope row 118 / findings `CSMC_P4_OWNER_SCOPE_MATRIX_20260913`.

## REAL STATIC RESULT
Fresh target P1/P2 had already closed the C-006 route gap:

1. `Canvas3DModelLoader.ModelData`
   - `LIVE_ROWS`
   - direct `catalog_character` CELSYS route.
2. `Manager3DOd.SceneData`
   - `LIVE_ROWS`
   - direct `scene` CELSYS route.
3. `ModelData3D.Layer3DModelData`
   - `ModelData3D` is registered only in schema;
   - physical table absent;
   - row count 0;
   - classification `SCHEMA_ONLY`;
   - therefore no live `Layer3DModelData` route exists in this target.
4. `Canvas3DModelBank.BankData`
   - `Canvas3DModelBank` has one live row;
   - physical `BankData` column is absent;
   - `FirstLoaderIndex=1` points to the existing `Canvas3DModelLoader` row;
   - therefore BankData is not an independent live payload route.

The exact target therefore has two independent direct CELSYS payload routes: character and scene. The formerly unresolved Layer3D/BankData branches do not add a third route.

Separately, the current public-safe P4 owner matrix classifies `BND_197_TO_195` as:
- outer route: `character`;
- owner scope: `SAME_HIGHER_LEVEL_OWNER_FAVORED_NOT_PROVEN`;
- consumer scope: `DISTINCT_LOCAL_CHILD_GRAMMAR_CANDIDATE_INSIDE_CHARACTER_ROUTE`;
- semantic owner: `UNRESOLVED`;
- consumer function: `UNRESOLVED`.

## IMPLEMENTATION
Added `csmc_analysis_c_route_owner_reconciliation.py` so route closure and owner inference cannot collapse into one state.

## SYNTHETIC TEST
7/7 PASS:
- both direct payload routes verified;
- independent route count remains exactly two;
- Layer3D route classified schema-only/no-live-route;
- BankData classified as live indirection to existing loader route;
- same-higher-level-owner remains only favored/not proven;
- semantic owner remains unresolved;
- semantic promotion remains 0 and Blender emit remains blocked.

## NEW INFORMATION
C-006's two unresolved outer-route entries are stale and can be retired. File-route discovery for this exact target is complete enough to say there is no additional independent Layer3D/BankData CELSYS payload route.

This does **not** close the internal owner question around `BND_197_TO_195`. Route identity and semantic owner are distinct axes.

## CLOSED HYPOTHESES
- `Layer3DModelData` is a live third payload route in this target: REJECTED.
- `Canvas3DModelBank.BankData` carries an independent live payload in this target: REJECTED.
- resolving all outer routes identifies the `+197/+195` semantic owner: REJECTED.
- a live bank row implies a live BankData payload column: REJECTED.

## CONFIDENCE CHANGES
- exact-target outer 3D route graph completeness: HIGH -> VERY HIGH.
- unresolved outer-route count: 2 -> 0.
- `BND_197_TO_195` same-higher-level owner continuity: remains FAVORED_NOT_PROVEN.
- semantic owner / consumer function: unchanged UNRESOLVED.
- pipeline: unchanged `STRUCTURAL_ONLY`; Blender emit BLOCKED.
