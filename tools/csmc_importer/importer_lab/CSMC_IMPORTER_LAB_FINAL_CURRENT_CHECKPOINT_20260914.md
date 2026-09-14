# CSMC IMPORTER LAB — Final Current Checkpoint — 2026-09-14

Status: `TARGETED_RESUME_COMPLETE__COMPANION_RECONCILED__STATIC_FRONTIER_PAUSED__PHYSICAL_ORACLE_PENDING`

## CANONICAL STATE
- Mainline branch: `csmc-importer-experimental-20260902`
- Mainline head before this checkpoint file: `874a5d3f9a9d302b1c599ccc188f5527b87366e6`
- CSMC importer smoke `34826186684`: SUCCESS
- Importer Lab synthetic smoke `34826186597`: SUCCESS
- Pipeline: `STRUCTURAL_ONLY`
- semantic promotion count: 0
- Blender emit: blocked
- runtime dispatch: false

## EVIDENCE LEDGER
- row 167 — GEN0 Phase-7 `LOCAL_INDEX_RANGE_BLOCK`: bounded family rejected.
- row 168 — GEN0 Phase-8 `LOCAL_COUNT_TO_ANCHOR_EXTENT`: bounded family rejected.
- row 169 — F02 mutation-oracle intake: VERIFIED, 18/18 contract tests; physical observations=0, pending.
- row 170 — GEN0 Phase-9 `LOCAL_LENGTH_CHAIN`: bounded family rejected.
- row 171 — static GEN0 pause after three consecutive generations without validation-frontier improvement.
- row 172 — independent render-part residual localization:
  - exact F03/F06/F07 common block 7392 B
  - pre-common shifts +88/+184 B vs F03; F07-F06 = +96 B
  - shared post-common growth = 2456 + 11 B
  - Level-4 render-part cardinality candidate refined, not promoted
  - direct common boundary-relative raw count scalar family rejected in tested scope
- row 173 — targeted resume `SIMPLE_96B_SINGLE_INSERTION_BEFORE_COMMON_BLOCK`:
  - full pre-common hits=0
  - trailing 2048/2144 scope hits=0
  - simple literal one-span 96 B insertion model rejected
  - return to PAUSED
- row 174 — Companion C C-064 independent reconciliation:
  - `RENDER_PART_RESIDUAL_LOCALIZATION_RECONCILED_LEVEL4_NOT_PROMOTED`
  - geometry/index unresolved
  - explicit serializer field read unresolved
  - controlled fixture -> consumer match unresolved
  - no runtime/MODELER/Worker/Canary/Control Gate/RIO-26/mainline mutation

## CURRENT INTERPRETATION
The render-part residual evidence is stronger and more localized than before, but it still does not identify geometry/index/material/object field semantics. The F07-vs-F06 +96 B difference is not a single literal 96-byte insertion into otherwise identical pre-common content under either preregistered scope.

The appropriate state is therefore not “keep enumerating.” The static frontier remains paused until a genuinely new evidence axis arrives.

## RESUME GATES
1. RIO-59 read-only F02 MODELER mutation-oracle observations (M01-M30).
2. Proof-grade `EXPLICIT_SERIALIZER_FIELD_READ` / destination data-flow evidence.
3. Another independently justified source producing a new structural constraint.

Do not post-hoc widen Phase-7/8/9 or the simple-96B insertion model.

## DURABLE REFERENCES
Targeted resume:
- GitHub findings commit: `874a5d3f9a9d302b1c599ccc188f5527b87366e6`
- Drive aggregate: `1l0QDmynelYf7ISC639gmgv4aH7VMa355`
- Drive findings: `12Kt6y1VfUIluSTkD-xhuKCIw6KdUzcTZ`
- Supabase: row 173
- Base44: `6aa7b9545e8a9e7d244ced7c`
- Linear: RIO-58

Companion reconciliation:
- Supabase: row 174
- Companion branch: `csmc-analysis-companion-c-20260913`
- Companion head: `ce58c86b65429cb6c4da21e8f6277b850b189cb6`
- Companion CI: `34826138838`
- Linear: RIO-48
- Base44: `6aa7b971bd4986b177a91cd7`

Physical oracle lane:
- Supabase: row 169
- Linear: RIO-59
- Base44: `6aa7b7acf722c811b4a51c6e`
- status: `PENDING_MANUAL_ORACLE`

Final checkpoint mirror:
- Drive: `1dLLmAGM2dnmIfk4pnS1S6rTa8fzfmuoX`
- SHA-256: `4e8c54e8a256578e049600c19a24bbfd7c096bef6a482897f14d78c0c495e9ef`

## SAFETY
No raw private CSMC bytes are included. No semantic promotion, Blender emit, runtime dispatch, Worker/Canary/STABLE/Control Gate mutation was performed by this lane.

## NONCANONICAL SIDE BRANCH
`research-lab-m1-20260914` remains a duplicate reconciliation prototype and is not canonical. Do not merge without a separate review.
