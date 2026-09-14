# CSMC ANALYSIS COMPANION C — Importer Lab M1 acceptance v2 state update — 2026-09-14

Status: `STATE_UPDATE_NOT_NUMBERED_C_RUN`

This checkpoint is intentionally **not C-068**. It records a cross-lane Importer Lab infrastructure change that arrived after the prior external-current pointer. It does not add semantic evidence.

## External source

- Supabase row: `187`
- run: `CSMC_IMPORTER_LAB_M1_ACCEPTANCE_V2_20260914`
- status: `M1_ACCEPTANCE_V2_20_OF_20_PASS_PRIVATE_GEN0_ELIGIBLE`
- Base44: `6aa7cd2c673a123a0ff3923a`
- Importer Lab branch: `csmc-importer-experimental-20260902`
- source head: `f69ae5c784526024549784b96e442d1c75b154d4`
- lab CI: `34833496373` SUCCESS
- importer smoke: `34833496409` SUCCESS
- Linear RIO-58 source comment: `925ef78d-522e-4037-b668-df6ca993ca87`

The source changed only the synthetic timeout-isolation acceptance threshold (`SLEEP 1.20s`, timeout `0.50s`) so the intentionally slow worker remains isolated without timing out the healthy synthetic worker. The core engine and semantic firewall were not loosened.

## Companion interpretation

M1 acceptance v2 = 20/20 PASS. This opens **bounded private GEN0 eligibility in the Importer Lab lane only**.

It does not authorize Companion C to run private GEN0, inspect private bytes, mutate mainline, or dispatch runtime work. It also does not override the earlier resource-allocation pause by itself: `broad_static_hypothesis_expansion=false` remains explicit, while `targeted_consumer_static_analysis=true` means only already-justified targeted consumer work may proceed in its owning lane.

This state update therefore changes infrastructure readiness but not evidence classification.

- latest numbered Companion run remains `C-067`
- pipeline `STRUCTURAL_ONLY`
- physical F02 oracle `0/30`, `PENDING_MANUAL_ORACLE`
- `EXPLICIT_SERIALIZER_FIELD_READ` UNRESOLVED
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH` UNRESOLVED
- semantic promotion `0`
- Blender emit BLOCKED
- runtime dispatch false
- Companion MODELER/Worker/Canary/Control Gate actions `0`
- RIO-26 mutation `0`
- mainline mutation `0`
- automatic integration false
- raw/private publication false

## Resume rule

Do not create C-068 from M1 acceptance infrastructure alone. A new numbered Companion run still requires genuinely new evidence: a sealed blind consumer result, validated F02 physical observations, actual admitted C-051 source/control evidence, or another independent public-safe constraint that changes a live hypothesis.
