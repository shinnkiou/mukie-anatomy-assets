# CSMC Mainline — Controlled Phase-Class Localization — 2026-09-14

## Question

Can the new controlled corpus reduce the opaque payload search space for future geometry/index localization without repeating Companion C C-050's all-pair semantic comparison?

## Hypothesis

The earlier observation that exact 8-byte reuse depends strongly on fixture pair may reflect a serializer/transform **phase class** related to `logical_length mod 8`. If true, same-phase pairs should preserve a large exact region even when their modeled content differs.

This run is structural only. It does not name a codec/cipher and does not assign vertex/index/material/bone semantics.

## Method

The probe compares only a bounded set of 8-byte token sequences and emits aggregate positions/counts, never literal qword values.

Discovery pair:
- F02 QUAD ↔ F04 CUBE_SUBDIV (`logical mod 8 = 7/7`)

Independent/contrast validation pairs:
- F02 ↔ R01 (`7/7`)
- F05 ↔ R02 (`5/5`)
- F06 ↔ F07 (`1/1`)
- F01 ↔ R05 (`2/2`)
- F06 ↔ R03 (`1/1`, different render-part count)

Different-mod controls:
- F03 ↔ F04 (`6/7`)
- F03 ↔ F05 (`6/5`)
- R04 ↔ R05 (`3/2`)
- R03 ↔ R04 (`1/3`)

## Observed result

Every tested same-mod pair has **one giant contiguous exact qword run**:

| Pair | mod8 | longest run | fraction of shorter payload | trailing qwords after run |
|---|---:|---:|---:|---:|
| F02 ↔ F04 | 7/7 | 1809 qwords | 81.7812% | 1 / 1 |
| F02 ↔ R01 | 7/7 | 1809 | 81.7812% | 1 / 1 |
| F05 ↔ R02 | 5/5 | 1808 | 80.3199% | 2 / 2 |
| F06 ↔ F07 | 1/1 | 2118 | 82.6053% | 1 / 1 |
| F01 ↔ R05 | 2/2 | 1808 | 81.7730% | 2 / 2 |
| F06 ↔ R03 | 1/1 | 1801 | 79.1648% | 1 / 1 |

Across these six selected same-mod pairs:
- minimum longest run = **1801 qwords = 14,408 bytes**
- minimum exact-sequence match fraction = **79.1648%**

For each pair, the giant run ends the same number of qwords from the stored payload end on both fixtures. Therefore the **entire stored-length delta is before the giant invariant run** for these same-phase comparisons.

## Negative controls

Different-mod controls do not reproduce the same >1800-qword invariant tail:

- F03 ↔ F04: longest 18 qwords; total exact-sequence match 3.7879%
- F03 ↔ F05: longest 18; 4.0553%
- R04 ↔ R05: longest 18; 3.6388%
- R03 ↔ R04: longest **306**; 18.9890%

The R03↔R04 306-qword run is an important counterexample to any naive rule that “different mod means no reuse”. It is much smaller than the same-mod invariant runs and is close to the already-known 307-qword cadence scale, so this run is retained as a distinct structural reuse phenomenon rather than forced into the phase-class model.

## Interpretation

Accepted as a **STRUCTURAL_PHASE_CLASS_CANDIDATE**:

- `logical_length mod 8` is a strong predictor of whether very large exact 8-byte runs can be directly compared in this corpus.
- Same-mod comparisons are therefore preferred for literal block localization.
- This is a comparison-normalization rule, not content semantics.
- No AES/Blowfish/codec/encryption/compression claim is made.
- Same mod is not claimed to be necessary or sufficient outside the tested corpus.

A second structural candidate follows:

**PHASE_NORMALIZED_VARIABLE_PREFIX_CANDIDATE**

For tested same-mod pairs, roughly 79–83% of the shorter payload can be excluded from the first search for changed content because it is one exact invariant run. The changed-length budget is localized before that run, with only 1–2 trailing qwords outside it.

This does not prove that every semantic value lives in the prefix; it only localizes where the controlled serialization changes can occur in these pairs.

## Importer consequence

Future geometry/index localization should no longer treat the whole opaque payload uniformly.

Preferred order:
1. group controlled pairs by `logical_length mod 8`;
2. identify the giant invariant run;
3. mark it `EXACT_INVARIANT_REGION` for that pair;
4. concentrate differential segmentation on the variable prefix and trailing 1–2 qwords;
5. keep identity/name metadata as an unresolved confounder;
6. require independent controlled relationship before semantic promotion.

For the F02↔F04 geometry contrast specifically, the giant exact run starts at qword 402 in F02 and 510 in F04 and spans 1809 qwords. This reduces the direct changed-region search from the whole payload to the prefix plus one trailing qword, but does **not** make the pair I3_VALID.

## Gate state

- pipeline: `STRUCTURAL_ONLY`
- semantic promotion count: 0
- geometry: UNRESOLVED
- index/topology: UNRESOLVED
- Blender emit: BLOCKED
- MODELER/runtime/Worker/Canary/Control Gate actions: 0

## Next action

Integrate phase-class/invariant-region metadata into the importer intake as an **optional evidence sidecar**, not as a semantic field. Then use the phase-normalized prefix as the bounded search space for geometry/index candidate localization.
