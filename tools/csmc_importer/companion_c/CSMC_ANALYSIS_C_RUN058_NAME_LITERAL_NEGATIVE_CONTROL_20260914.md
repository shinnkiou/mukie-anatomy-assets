# CSMC ANALYSIS COMPANION C — RUN C-058

## QUESTION
Can the new mainline controlled name-literal probe narrow C-056/C-057 confounder handling without promoting name/material/object semantics?

## SOURCE
Reference-only mainline input:
- commit `684c210f933803b16b80f5ba6dcb56186a162223`
- Supabase row 147
- Drive findings `1CULtcjqzUpHyPmG9YHZSAv3y_1RfreIf`
- Drive aggregate `1uPek8ajbYZBOQlGp92WM5X_5RS_sLHIA`

The source preregistered 53 Blender-side identifiers over 12 controlled fixtures and searched exact ASCII / UTF-16LE / UTF-16BE representations across the full SQLite file and character BLOB: 318 searches, 0 literal occurrences.

## RESULT
Classification: `PLAINTEXT_SOURCE_NAME_CONFOUNDER_NEGATIVE_CONTROL`.

Accepted conclusion is narrow: known source identifiers were not observed as straightforward plaintext in these 12 fixtures. Therefore arbitrary printable runs must not be called `NAME_METADATA` without relationship evidence, and simple source-name carving cannot currently remove identity/name confounding.

Not concluded:
- names are absent from serialization;
- names are encrypted/compressed;
- any name codec is identified;
- the C-056 localized prefix is material or object metadata;
- I3_PARTIAL becomes valid.

## IMPLEMENTATION / TEST
`csmc_analysis_c_name_literal_negative_control_c058.py` consumes public-safe aggregate counts/flags only. It never reads CSMC bytes. Local synthetic/fail-closed suite: **11/11 PASS**.

Rejects altered search totals, positive literal-hit claims under this exact source record, semantic/name-region promotion, raw-value embedding, non-STRUCTURAL pipeline, runtime dispatch, Blender emit, or raw-private publication.

## NEW INFORMATION
Name-like plaintext is no longer a valid shortcut for explaining the current controlled-pair differentials. Confounder separation must use same-identity controls or stronger owner/consumer relationships.

## CONFIDENCE
- plaintext-source-name absence in the preregistered search surface: VERY HIGH negative-control result
- names absent globally: UNPROVEN
- name codec/cipher: UNPROVEN
- material/object owner: UNRESOLVED
- I3: PARTIAL unchanged

## ISOLATION
`STRUCTURAL_ONLY`; semantic promotion=0; Blender emit=BLOCKED; runtime dispatch=false; runtime/MODELER/Worker/Canary/Control Gate/mainline/RIO-26 mutation=0; automatic integration=false; raw/private payload publication=false.

## NEXT
Prefer real C-051 same-identity material/object controls or a different genuinely new public-safe relationship artifact. Do not infer semantic ownership from printable strings.
