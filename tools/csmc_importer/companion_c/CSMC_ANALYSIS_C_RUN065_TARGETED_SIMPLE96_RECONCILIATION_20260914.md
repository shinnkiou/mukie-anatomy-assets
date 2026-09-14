# CSMC ANALYSIS COMPANION C — RUN C-065
## Targeted simple-96 rejection / frontier-pause reconciliation — 2026-09-14

### Why this is a new run

C-064 admitted a genuinely new positive structural localization: the F06/F07 pre-common boundary differs by 96 bytes while both retain the same refined Level-4 2456-byte cadence relationship. Mainline then used that independent constraint for one preregistered targeted test. C-065 reconciles the result without reopening blind enumeration.

### Source result

Source mainline:
- branch `csmc-importer-experimental-20260902`
- head `874a5d3f9a9d302b1c599ccc188f5527b87366e6`
- public-safe aggregate commit `2ba1bd94b0cf8d35864eba11e12bffc7d35ccae4`
- source Supabase row 173

Preregistered question:
Can the F07 pre-common prefix be reduced to the F06 pre-common prefix by deleting exactly one contiguous 96-byte span?

Frozen scopes:
1. `FULL_PRE_COMMON`
2. `TRAILING_2048_PLUS_INSERTION` — 2048 bytes in F06 versus 2144 bytes in F07

Rules were exact one-span deletion, 96 bytes, zero tolerance, no multiple deletion and no semantic scoring.

Result:
- FULL_PRE_COMMON hits = 0
- TRAILING_2048_PLUS_INSERTION hits = 0
- `TARGETED_SIMPLE_96B_INSERTION_FAMILY_REJECTED`

### Companion C interpretation

This closes only the simple model in which the entire F07-vs-F06 pre-common difference is one literal 96-byte insertion into otherwise byte-identical F06 content in either preregistered scope.

It does not reject multiple edits, replacement-plus-growth, encoded or transformed records, variable headers, indirect structures, consumer-derived state, or any semantic interpretation.

The C-064 evidence remains intact:
- shared exact block = 7392 bytes
- F06 shift vs F03 = +88 bytes
- F07 shift vs F03 = +184 bytes
- F07 vs F06 = +96 bytes
- render-part residual candidate = `LEVEL_4_REFINED_NOT_PROMOTED`

No names are assigned to the 88/184/96-byte regions.

### Frontier state

Because this one justified targeted resume produced no positive binding, Companion C aligns with mainline:

`RETURN_TO_PAUSED_WAITING_NEW_INDEPENDENT_EVIDENCE`

Resume only on one of:
- actual read-only F02 MODELER mutation-oracle observations;
- proof-grade explicit serializer field-read / destination data-flow evidence;
- another genuinely independent constraint axis.

Do not widen the failed simple-insertion family post hoc.

### Gate

`STRUCTURAL_ONLY`; semantic promotion=0; Blender emit blocked; runtime dispatch=false; MODELER/Worker/Canary/Control Gate/RIO-26/mainline mutation=0; automatic integration=false; no raw/private bytes published.
