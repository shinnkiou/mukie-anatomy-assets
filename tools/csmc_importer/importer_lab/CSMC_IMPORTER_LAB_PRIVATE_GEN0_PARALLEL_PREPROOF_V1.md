# CSMC Importer Lab — Private GEN0 Parallel Pre-Proof v1

Status: `COMPLETE__0_SURVIVORS__STRUCTURAL_ONLY`

- Family: `LOCAL_BOUNDED_STRIDE_PERIODICITY`
- Corpus ZIP SHA-256: `be6132ef83959167ffd19218810e099f0bd164714fbd1ec4770f9296b38643b6`
- Aggregate JSON SHA-256: `389960fbc943dfdf4781f79c054fcb88b11943d02eb6e721ed3d930b1b9def8f`
- Generated candidates: `32`
- Deduped candidates: `32`
- Logical maximum: `50`
- Filler candidates: `0`
- Cross-fixture hard pass: `0`
- Cross-fixture hard fail: `32`
- Physical oracle: `0/30 PENDING_MANUAL_ORACLE`
- `semantic_promotion=false`
- `blender_emit=false`
- `runtime_dispatch=false`

## Frozen scope

Only the last 1024 bytes before the validated exact invariant core of the phase-7 fixtures were examined:

- F02 QUAD — TRAIN — core starts at payload offset 3216
- F04 CUBE_SUBDIV — TRAIN — core starts at payload offset 4080
- R01 CUBE_B1_W0 — VALIDATION — core starts at payload offset 3384

Candidates were byte strides 1..32. For each stride, the evaluator counted exact equality of byte pairs separated by that stride. A fixture-local hit required an exact binomial upper-tail probability below 0.001 under the null equality probability 1/256. A hard pass required the same stride to hit in both TRAIN fixtures and the VALIDATION fixture.

## Result

Only F04 had one fixture-local event (stride 30, 12 equal pairs at the frozen threshold). F02 and R01 had no fixture-local hit, so there were **zero cross-fixture survivors**.

Classification:

`GEN0_PARALLEL_PREPROOF_LOCAL_BOUNDED_STRIDE_PERIODICITY_REJECTED_PHASE7`

This is a structural rejection only. It does not identify or reject geometry, topology, material, UV, rig, weight, codec, cipher, or any semantic field.

## Non-widening rule

The previous exact rejected scopes remain closed. This generation does not reopen:

- Phase-7 raw contiguous u16/u32 BE/LE reference-domain arrays
- Phase-8 exact local count-to-anchor extent
- Phase-9 exact two-stage local length chain
- simple literal 96-byte insertion before the common block

This new stride family is also closed at the frozen scope above. No post-hoc widening is authorized.

## Next evidence

The private generation completed, but it produced no structural survivor. Therefore the next useful work is not another blind static family. The Track-D discrimination questions should be converted into bounded consumer-static questions, especially direct read width/endianness/count/length/destination evidence around known framing and loader paths.

Raw/private CSMC bytes are not included in this artifact.
