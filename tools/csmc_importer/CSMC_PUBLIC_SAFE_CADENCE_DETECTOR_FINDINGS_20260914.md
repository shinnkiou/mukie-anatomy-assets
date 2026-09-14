# CSMC Public-Safe Cadence Detector Findings — 2026-09-14

## Question

Can the C-050 2456-byte / 307-qword cadence be detected by mainline Importer code without publishing or depending on the private-derived motif bytes used by Companion C?

## Method

The detector compares only qword equality at a bounded lag. For each payload it:

1. compares `qword[i] == qword[i + 307]`;
2. finds consecutive equality runs of at least 10 qwords;
3. groups runs whose start positions are at most 250 qwords apart;
4. accepts an even run-count cluster of at least four runs;
5. derives a structural cadence-count candidate as `run_count / 2 + 1`.

No qword values are emitted. Public output contains positions, run lengths, counts, fixture hashes, and aggregate relationships only.

## Controlled-corpus result

The detector reproduces the previously published C-050 cadence counts for **13/13** fixtures:

- F01/F02/F03/F04/F05: cadence 3
- F06/F07: cadence 4
- R01/R02/R03/R04/R05: cadence 3
- V01 VRoid: cadence 10

When compared with known controlled render-part cardinality, all 13 satisfy the existing candidate relationship:

`cadence_count = 2 + render_part_count`

This does not confirm the semantic binding. It makes the structural cadence detectable by public-safe importer code.

## Negative lag control

A bounded lag sweep from **280 through 330 qwords** was run with the same detector. Only lag **307** reproduced the teacher relationship for all 13 fixtures.

- full-match lags: `[307]`
- maximum teacher-relation matches for any non-307 lag: `0/13`
- maximum number of fixtures producing any eligible detection at a non-307 lag: `1/13`

This materially weakens the explanation that the result is a generic consequence of trying many nearby lag values.

## Parameter robustness

A small preregisterable neighborhood around the detector thresholds was checked:

- minimum equality run: 8, 9, 10, 11, 12 qwords
- maximum cluster-start gap: 225, 230, 240, 250, 260, 280, 300 qwords

All **35/35** parameter combinations reproduced the same 13/13 cadence relationship.

Caveat: these threshold parameters were explored on the current corpus, so V01 is not claimed as a fresh independent holdout for this new public-safe detector. The independent VRoid semantic consistency remains the previously established C-050 evidence.

## Importer integration

`csmc_import_intake_v0_4` now exposes structural cadence metadata when detected:

- detector schema
- 307-qword / 2456-byte period
- equality-run cluster count
- cadence-count candidate
- cluster qword bounds

The intake deliberately labels this `STRUCTURAL_CADENCE_CANDIDATE_ONLY` and does not emit a confirmed material/render-part field.

The existing controlled evidence gate can represent `TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE` at **Level 4 / I3_PARTIAL**, but semantic promotion remains false.

## Scout toolbox decision

The Scout numeric candidate probe remains unused. This cadence detector already creates a narrower, explicit structural search target without dtype guessing. Numeric probing becomes useful only after a local sub-block inside the cadence/prefix candidate region is isolated such that numeric type plausibility can discriminate competing hypotheses.

## Gate

- pipeline: `STRUCTURAL_ONLY`
- semantic promotion: 0
- geometry: UNRESOLVED
- index/topology: UNRESOLVED
- render-part cardinality: Level 4 CANDIDATE_ONLY
- Blender emit: BLOCKED
- MODELER/runtime/Worker actions: 0

## Next action

Use the now-public-safe cadence bounds as anchors for **local boundary/sub-block analysis**. Do not return to whole-prefix exact-qword search or whole-prefix size fitting. Additional physical fixtures are not requested yet.
