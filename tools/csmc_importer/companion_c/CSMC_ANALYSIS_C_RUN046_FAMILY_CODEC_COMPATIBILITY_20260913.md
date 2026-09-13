# CSMC ANALYSIS COMPANION C — RUN C-046

## QUESTION
Can the new post-C-045 public-safe counted-BE exact-fit ceilings reduce the admissible +965 **family-wide** codec-binding interpretations without raw bytes, changing the preregistered C-018 trial surface, or promoting semantics?

## HYPOTHESIS
For a cross-surface family-wide counted-BE f32 binding at a fixed structural role, every record in the family must fit on both surfaces. Therefore a necessary condition is:

`family_size <= min(surface_A_exact_fit_ceiling, surface_B_exact_fit_ceiling)`

This can eliminate family-wide interpretations, but it must not be used to delete C-018 scan cells because C-021 explicitly permits cross-family same-role recurrence.

## PROBE / IMPLEMENTATION
Consumed only the new public-safe cross-lane aggregate:
- Drive: `CSMC_P4_FAMILY_COMPATIBILITY_AND_PARENT_EDGE_INVENTORY_20260913`
- Drive ID: `1flgIummgLY4MNVMdZ3KW0wU2yD5YKfe7NBY4fi_EIlU`
- referenced mainline parent-edge commit: `5ae93bbc20fb26c62a1629455ed5690164db932a`

Known family sizes from C-002:
- `F48_0000110` = 7
- `F48_0000111` = 3
- `F48_0001110` = 3
- `F49_0000111` = 3
- `F49_1000111` = 6

New aggregate f32 exact-fit ceilings:
- whole record q0: A<=7, B<=7
- stable prefix q0: A<=7, B<=7
- control zone q21: A<=6, B<=5
- preserved island q25: A<=6, B<=6

Implemented `csmc_analysis_c_family_codec_compatibility.py` as a one-way necessary-condition classifier. It emits `binding_confirmed=false`, `semantic_promotion=false`, and `primary_preregistered_scan_surface_reduced=false` by construction.

## SYNTHETIC TEST
9/9 PASS against identical classifier logic:
- q21 keeps exactly the three size-3 families
- q25 excludes only the size-7 family
- both q0 roles keep all five families
- compatibility never confirms binding/semantics
- C-018 primary scan is never reduced
- missing surface, negative/boolean ceiling, and invalid family size reject fail-closed

## PUBLIC-SAFE RESULT
### CONTROL_ZONE_Q21
Effective cross-surface ceiling = 5.

Family-wide compatible:
- `F48_0000111` (3)
- `F48_0001110` (3)
- `F49_0000111` (3)

Family-wide impossible under the new ceiling:
- `F48_0000110` (7)
- `F49_1000111` (6)

Thus only 9/22 records belong to families still compatible with a **complete family-wide q21 binding** hypothesis.

### PRESERVED_ISLAND_Q25
Effective cross-surface ceiling = 6.

Family-wide impossible:
- `F48_0000110` (7)

The three size-3 families plus `F49_1000111` (6) remain aggregate-compatible: 15/22 records.

### WHOLE_RECORD_Q0 / STABLE_PREFIX_Q0
Effective cross-surface ceiling = 7. No known family is eliminated by family size alone.

## INTERPRETATION
The new input narrows **binding scope interpretation**, not the primary preregistered trial family.

C-018 remains unchanged because its 132-cell scan was preregistered before this evidence and C-021 rejected same-family identity as a mandatory recurrence gate. Individual exact fits in the size-6/7 families and cross-family same-role recurrence therefore remain admissible observations.

The new rule is useful after or alongside the scan: a q21 recurrence cannot legitimately be promoted to a complete `F48_0000110` or `F49_1000111` family-wide codec binding. At q25, the size-7 family-wide interpretation is excluded. Compatibility for size-3/6 families is still only a necessary-condition pass, not positive binding evidence.

The fixed-role BE-f64 candidate remains shape-incompatible from prior evidence; C-046 does not reopen that closed hypothesis.

## NEW INFORMATION
- Aggregate exact-fit ceilings can prune `FAMILY_LOCAL` / family-wide codec-scope hypotheses without raw bytes.
- q21 family-wide candidate set shrinks from five known families to three size-3 families.
- q25 family-wide candidate set shrinks from five to four families.
- equality/preservation family identity and counted-BE codec identity are now more sharply separated: preservation at q21 does not imply family-wide counted-BE f32 compatibility.
- The correct place for this evidence is the binding-scope layer, not the C-018 cell-selection layer.

## CLOSED HYPOTHESES
- The new ceiling permits shrinking the preregistered C-018 primary scan surface: REJECTED.
- A family that passes the ceiling is codec-bound: REJECTED.
- q21 preservation implies q21 counted-BE f32 family-wide binding: REJECTED.
- The six-member `F49_1000111` can be 6/6 counted-BE f32 at q21 on both surfaces: REJECTED by aggregate ceiling.
- The seven-member `F48_0000110` can be family-wide counted-BE f32 at q21 or q25 on both surfaces: REJECTED by aggregate ceiling.

## CONFIDENCE CHANGES
- family-size ceiling as a necessary-condition filter: HIGH -> VERY HIGH.
- q21 size-6/7 family-wide incompatibility: VERY HIGH.
- q25 size-7 family-wide incompatibility: VERY HIGH.
- codec binding itself: remains UNCONFIRMED.
- semantic state: unchanged `STRUCTURAL_ONLY`; semantic promotion count=0.
- Blender emit: BLOCKED.

## NEXT QUESTION
Use future public-safe aggregate evidence only if it changes the compatibility/binding graph. Do not repeat C-045 owner-edge search or C-018 byte scan without an actual I1/static reference. Continue monitoring for genuinely new I1-I4 or cross-lane public-safe evidence; no runtime dispatch or mainline mutation from Companion C.
