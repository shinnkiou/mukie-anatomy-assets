# CSMC Analysis Companion C — Run C-001 Boundary Motif Generality

## QUESTION
Is `phase reuse -> extinction/rewrite -> new phase reuse` a general boundary grammar, or is complete extinction specific to `+197 -> +195` in the currently durable aggregate evidence?

## HYPOTHESIS
If complete extinction is general, independent 4.69M transitions should also have zero old/new-delta matches inside the barrier and zero cross-serialization survival of barrier qwords.

## PROBE
`csmc_analysis_c_boundary_motif_classifier.py` consumes only the existing public-safe aggregate boundary comparison JSON. It does not read raw model/payload bytes.

## SYNTHETIC TEST
`test_csmc_analysis_c_boundary_motif_classifier.py` verifies a clean-extinction fixture and a mixed-reuse fixture. PASS locally before persistence.

## REAL AGGREGATE RESULT
- `BND_197_TO_195`: `LOCAL_EXTINCTION_CANDIDATE`, cross-serialization survival distinct=0, old/new barrier match density=0, net=-16 B.
- `BND_4693615_TO_4692559`: `MIXED_REUSE_REPACK_CANDIDATE`, survival distinct=40, old/new densities about 0.00679/0.00528, net=-8448 B.
- `BND_4692559_TO_4697174`: `MIXED_REUSE_REPACK_CANDIDATE`, survival distinct=308, old/new densities about 0.00196/0.00364, net=+36920 B.

Class counts: 1 local-extinction / 2 mixed-reuse-repack. Universal complete-extinction grammar is not supported by these three boundaries.

## INTERPRETATION
The evidence strengthens the specificity of `+197 -> +195`. It remains the best current candidate for a locally bounded serializer-owned length-changing child/subunit. The 4.69M transitions retain old/new-phase and global reuse and fit broader repack/reorder mixing better. No Mesh/Index/UV/Material/Bone/Weight semantics are assigned.

## NEW INFORMATION
- Complete qword extinction is not a general property of the current major boundary candidates.
- Current boundary taxonomy has at least two structural classes: local extinction vs mixed reuse/repack.

## CLOSED HYPOTHESES
- `all major delta transitions use the +197 -> +195 complete-extinction grammar` — REJECTED on current evidence.

## CONFIDENCE CHANGES
- `+197 -> +195 is a local serializer-owned child/subunit boundary`: MEDIUM -> MEDIUM-HIGH.
- `4.69M transitions are local analogues`: LOW -> VERY LOW.
- `4.69M transitions are section-level repack/reorder boundaries`: MEDIUM -> MEDIUM-HIGH.

## NEXT QUESTION
Can the established +965 record family be represented losslessly by one record-class variable, or are record length and control-zone preservation signature independent structural axes?
