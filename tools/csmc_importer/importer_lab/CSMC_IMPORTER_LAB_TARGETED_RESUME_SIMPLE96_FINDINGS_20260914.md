# CSMC Importer Lab — Targeted Resume: Simple 96-byte Insertion Rejection — 2026-09-14

## Trigger
A new independent structural constraint arrived after the static GEN0 pause: the existing Level-4 `TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE` was refined with a 7392-byte exact F03/F06/F07 common block, pre-common shifts of +88 / +184 bytes, and an F07-vs-F06 excess of exactly +96 bytes.

This justified one targeted resume. It did not justify reopening blind GEN0 enumeration.

## Preregistered question
Can the F07 pre-common prefix be reduced to the F06 pre-common prefix by deleting exactly one contiguous 96-byte span?

Two scopes were fixed before private-byte inspection:

1. `FULL_PRE_COMMON`
2. `TRAILING_2048_PLUS_INSERTION` — F06 final 2048 pre-common bytes versus F07 final 2144 pre-common bytes.

Rules:
- exactly one deletion
- deletion length exactly 96 bytes
- exact byte equality only
- no tolerance
- no multiple deletions
- no semantic label or score

## Result
- full pre-common exact single-insertion hits: **0**
- trailing-scope exact single-insertion hits: **0**
- classification: `TARGETED_SIMPLE_96B_INSERTION_FAMILY_REJECTED`

Therefore the +96-byte F07-vs-F06 pre-common difference is **not** explainable, in either frozen scope, as one literal 96-byte insertion into otherwise byte-identical F06 content.

## Preserved evidence
The prior structural localization remains valid:
- exact shared block: 7392 bytes
- F06 pre-common shift vs F03: +88 bytes
- F07 pre-common shift vs F03: +184 bytes
- F07 vs F06 shift: +96 bytes
- shared post-common growth: 2456 + 11 bytes
- Level-4 render-part cardinality candidate remains refined but **not promoted**

No name is assigned to the 88/184/96-byte regions.

## Frontier decision
The targeted resume did not produce a new positive binding. Static enumeration returns to:

`PAUSED_WAITING_NEW_INDEPENDENT_EVIDENCE`

Resume on:
1. read-only F02 MODELER mutation-oracle observations; or
2. proof-grade direct serializer field-read / destination data-flow evidence; or
3. another genuinely independent constraint axis.

Do not widen the simple-insertion test post hoc.

## Safety
- `STRUCTURAL_ONLY`
- semantic promotion = 0
- Blender emit = BLOCKED
- no runtime dispatch
- no Worker / Canary / STABLE / Control Gate mutation
- no raw CSMC bytes or literal private payload values published
