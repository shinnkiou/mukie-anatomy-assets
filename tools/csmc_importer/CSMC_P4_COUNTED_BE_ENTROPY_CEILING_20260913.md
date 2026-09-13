# CSMC P4 counted-BE entropy multiplicity ceiling — 2026-09-13

Status: `REGIME_GLOBAL_COUNTED_BE_F32_BINDING_EXCLUDED_FOR_FIXED_ROLES__MINORITY_RECURRENCE_OPEN`

This pass uses only already durable aggregate metadata from the verified `+965` 48/49-qword lattice. It does not reread private target bytes and performs no MODELER/runtime/Worker action.

## Question

The fixed-role preflight left counted BE-f32 shape-compatible at four independently bounded role starts. Can counted BE-f32 be the **regime-global codec** used by all 22 +965 records at any of those starts?

An exact counted-BE f32 region must begin:

`00 00 00 XX`

because the predeclared expected counts are all below 256 (`95/97`, `41`, `13`, `3`). Therefore every exact-fit row contributes three zero bytes plus one constrained count byte in the first qword of that role.

The prior lattice analysis already saved aggregate byte entropy for the corresponding relative qwords across all 22 records. We can therefore bound how many rows could possibly carry such a fixed prefix, without knowing any private byte value.

## Conservative entropy bound

For a proposed number `k` of exact-fit rows, maximize entropy adversarially:

- keep only the bytes forced by counted-BE fixed;
- assign every other unconstrained byte a distinct byte value not equal to the fixed symbols.

There are only 176 bytes in 22 qwords, so the 256-symbol byte alphabet is large enough for this construction. This yields a genuine upper bound: if the observed entropy is higher than the maximum possible entropy for `k` fits, then `k` or more fits are impossible.

For the whole-record role, the count byte may be `95` or `97` according to the verified 48/49-qword length class. The bound maximizes over every feasible split under the known class counts `13 × 48` and `9 × 49`.

## Result

| Role start | Surface | Observed byte entropy | Maximum exact-fit rows compatible with entropy |
|---|---|---:|---:|
| whole record q0 | clip | 6.80011855035714 | **7 / 22** |
| whole record q0 | CSMC | 6.80011855035714 | **7 / 22** |
| stable prefix q0 | clip | 6.80011855035714 | **7 / 22** |
| stable prefix q0 | CSMC | 6.80011855035714 | **7 / 22** |
| control zone q21 | clip | 6.868300368538958 | **6 / 22** |
| control zone q21 | CSMC | 6.945060453790815 | **5 / 22** |
| preserved island q25 | clip | 6.838498592983068 | **6 / 22** |
| preserved island q25 | CSMC | 6.838498592983068 | **6 / 22** |

Therefore **none of the four predeclared role starts can carry counted BE-f32 across all 22 +965 records.** The candidate is no longer a plausible regime-global codec binding at these role starts.

This does **not** close the Companion C binding question, because C-014 requires recurrence at the same structural role, not universal coverage. The entropy bound still permits a minority recurrent subset: at most 5–7 rows depending on role/surface.

## Interpretation boundary

Safe claim:

- regime-global counted BE-f32 binding is excluded for these four fixed role starts;
- if counted BE-f32 binds here at all, it must be a **minority/subfamily phenomenon**, not a universal +965 record grammar.

Not claimed:

- no actual target bytes were decoded in this pass;
- no exact-fit row identity is known;
- no semantic field, vertex, index, transform, bone, weight, material, texture, compression, encryption, or DRM meaning is assigned;
- Blender import is not proven.

## Next action

When the same authorized raw `.clip` / `.csmc` pair is available, run the fixed-role exact-fit probe. The entropy ceiling gives a fail-closed cross-check: any claimed result exceeding these per-role maxima is invalid. A recurrent minority exact fit may be reviewed for `CONFIRMED_CODEC_BINDING`; universal/regime-global binding at these starts is already excluded.
