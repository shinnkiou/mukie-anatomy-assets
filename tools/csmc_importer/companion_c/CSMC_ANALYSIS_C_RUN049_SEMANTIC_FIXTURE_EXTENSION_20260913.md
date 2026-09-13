# CSMC ANALYSIS COMPANION C — RUN C-049

## QUESTION
Can the existing public-safe fixture library close C-041's known calibration gaps for normal/tangent while adding layout negative controls for interleaved, sparse, and multi-material data, without changing any CSMC semantic state?

## HYPOTHESIS
C-041 already contains normal/tangent rules but its three original fixtures did not directly calibrate those two slots. Exact-hashed Khronos Asset Generator fixtures can extend detector calibration while testing that dense-contiguous layout is not a required semantic precondition.

## PUBLIC-SAFE INPUT
Drive resource index `16GgICogyj5xj5nHp9nELIov14yJGzHsAjtSuDroy_i4` provides acquired/hash metadata for four MIT Khronos fixtures: `Buffer_Interleaved_00`, `Accessor_Sparse_00`, `Mesh_PrimitiveAttribute_06`, and `Material_Mixed_02`. Existing fingerprint library: `1v1KPLyRWJKXrviNQQ5jBn7NQaX2mUfiR`.

No fixture bytes or private CSMC bytes are stored in this run; only public-safe metadata/hashes and synthetic observations are used.

## IMPLEMENTATION
Added `csmc_analysis_c_semantic_fixture_extension.py`. It reuses C-041 detector scoring while independently validating exact fixture ID + SHA-256 + declared ground-truth semantic. C-041 itself is not modified or given a broader trusted-source registry. Fixture ground truth remains calibration evidence only and `csmc_semantic_promotion=false` is hard-coded.

## SYNTHETIC / KNOWN-FIXTURE TEST
12/12 PASS.

HIGH cases:
- normal and tangent on `Mesh_PrimitiveAttribute_06`;
- vertex/index/UV on `Buffer_Interleaved_00`;
- vertex on `Accessor_Sparse_00` without a dense-contiguous premise;
- material routing on `Material_Mixed_02`.

Negative controls:
- normal/tangent numeric shape without relationship evidence remains MEDIUM, not HIGH;
- wrong fixture hash rejects;
- semantic not declared for that fixture rejects;
- CSMC semantic promotion remains false.

## RESULT
- normal/tangent move from rule-only/unexercised in C-041 to directly calibrated on an exact-hashed public fixture;
- interleaved 32-byte stride is compatible with high-confidence vertex/index/UV calibration when relationship evidence is present;
- sparse accessor layout is compatible with high-confidence vertex calibration when topology relationship evidence is present;
- multi-primitive/multi-material context strengthens material-binding calibration;
- no CSMC geometry/index/normal/tangent/material semantic is promoted.

## CLOSED HYPOTHESES
- normal/tangent calibration requires new private CSMC evidence: REJECTED;
- high-confidence vertex detection requires one dense contiguous float array: REJECTED;
- interleaving alone invalidates vertex/index/UV relationships: REJECTED;
- numeric vector shape alone is enough for HIGH normal/tangent confidence: REJECTED;
- public fixture calibration may promote CSMC semantics: REJECTED.

## CONFIDENCE CHANGES
- known-fixture normal/tangent detector calibration: UNCALIBRATED -> HIGH;
- interleaved/sparse layout robustness: MEDIUM -> HIGH;
- material binding-context calibration: HIGH -> VERY HIGH;
- current CSMC pipeline: unchanged `STRUCTURAL_ONLY`;
- semantic promotion count: 0;
- Blender emit: BLOCKED.

## NEXT
Use the expanded fixtures only for detector calibration/negative control. Continue on another independent public-safe/static axis or genuinely new I1-I4 input; no runtime/MODELER/Worker activity.
