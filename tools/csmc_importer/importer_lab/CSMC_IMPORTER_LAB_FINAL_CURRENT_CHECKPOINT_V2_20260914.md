# CSMC IMPORTER LAB — Final Current Checkpoint v2 — 2026-09-14

Status: `TARGETED_RESUME_COMPLETE__COMPANION_RECONCILED__ORACLE_INTAKE_HARDENED__STATIC_FRONTIER_PAUSED__PHYSICAL_ORACLE_PENDING`

## CANONICAL STATE
- Mainline branch: `csmc-importer-experimental-20260902`
- Mainline checkpoint commit: `ac521bc061aa0e489650a1495886b7b14d81e370`
- CSMC importer smoke `34827179764`: SUCCESS
- Importer Lab synthetic smoke `34827179829`: SUCCESS
- Oracle intake branch: `csmc-f02-mutation-oracle-intake-20260914`
- Oracle intake hardened head: `c25750fc3d91d97ffa79de95f583914d1294ee9f`
- Oracle intake CI `34826886335`: SUCCESS
- Pipeline: `STRUCTURAL_ONLY`
- semantic promotion count: 0
- Blender emit: blocked
- runtime dispatch: false

## EVIDENCE LEDGER
- row 167 — GEN0 Phase-7 `LOCAL_INDEX_RANGE_BLOCK`: bounded family rejected.
- row 168 — GEN0 Phase-8 `LOCAL_COUNT_TO_ANCHOR_EXTENT`: bounded family rejected.
- row 169 — F02 mutation-oracle intake contract: VERIFIED, physical observations 0/30.
- row 170 — GEN0 Phase-9 `LOCAL_LENGTH_CHAIN`: bounded family rejected.
- row 171 — static GEN0 pause after three consecutive generations without validation-frontier improvement.
- row 172 — independent render-part residual localization: Level-4 refined candidate, not promoted.
- row 173 — targeted resume `SIMPLE_96B_SINGLE_INSERTION_BEFORE_COMMON_BLOCK`: rejected; returned to PAUSE.
- row 174 — Companion C C-064 reconciliation: Level-4 residual localization reconciled without promotion.
- row 175 — first final-current checkpoint after targeted resume + Companion reconciliation.
- row 176 — oracle-intake provenance hardening:
  - raw public manifest SHA-256 is computed before JSON parsing;
  - intake fails closed unless it exactly matches the preregistered digest;
  - existing observation contract remains unchanged;
  - MODELER launch, mutation generation, save/serialization trigger, semantic promotion, Blender emit, and runtime dispatch remain prohibited;
  - physical observations remain 0/30.

## CURRENT INTERPRETATION
The render-part residual evidence remains stronger and more localized than before but still does not identify geometry/index/material/object field semantics. The simple literal 96-byte insertion explanation is rejected in the preregistered scopes.

The oracle intake path is now stronger on provenance, but this is infrastructure evidence only. It does not itself add a physical oracle observation or serializer semantic binding.

Therefore the static frontier remains:

`PAUSED_WAITING_NEW_INDEPENDENT_EVIDENCE`

## RESUME GATES
1. RIO-59 read-only F02 MODELER mutation-oracle observations (M01-M30), now ingested through the raw-hash-bound fail-closed CLI.
2. Proof-grade `EXPLICIT_SERIALIZER_FIELD_READ` / destination data-flow evidence.
3. Another independently justified source producing a genuinely new structural constraint.

Do not post-hoc widen Phase-7/8/9 or the simple-96B insertion family.

## DURABLE REFERENCES
Mainline final checkpoint v1:
- GitHub checkpoint commit: `ac521bc061aa0e489650a1495886b7b14d81e370`
- Drive: `1dLLmAGM2dnmIfk4pnS1S6rTa8fzfmuoX`
- Supabase: row `175`
- Base44: `6aa7bc21ccdb807b3e3902fb`

Oracle intake hardening:
- GitHub head: `c25750fc3d91d97ffa79de95f583914d1294ee9f`
- CLI commit: `5de3567ec683441717b39c4ace885563e9951ef2`
- CI coverage commit: `d9e7948330f7bf3932387b75b56713ee9eed358f`
- CI run: `34826886335` SUCCESS
- Drive hardening checkpoint: `1K5nkUZwhqmmbsPS_LG7jxZYLlvK-R6a8`
- Drive hardening SHA-256: `7bab409be4cd416955a3c4623b6e1453dc256c414a50b7e28b9f0f6ea204573f`
- Supabase: row `176`
- Base44: `6aa7bcb72c955663a751d4c5`
- Linear: RIO-59

Targeted resume:
- Supabase: row `173`
- Base44: `6aa7b9545e8a9e7d244ced7c`
- Linear: RIO-58

Companion reconciliation:
- Supabase: row `174`
- Base44: `6aa7b971bd4986b177a91cd7`
- Linear: RIO-48

## SAFETY
No raw private CSMC bytes are included. No semantic promotion, Blender emit, runtime dispatch, Worker/Canary/STABLE/Control Gate mutation is authorized by this checkpoint.

## NONCANONICAL SIDE BRANCH
`research-lab-m1-20260914` remains a duplicate reconciliation prototype and is not canonical. Do not merge without separate review.
