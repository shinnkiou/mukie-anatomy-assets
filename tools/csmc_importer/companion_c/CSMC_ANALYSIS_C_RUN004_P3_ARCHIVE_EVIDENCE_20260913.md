# CSMC Analysis Companion C — Run C-004 Historical P3 Controlled-Pair Evidence Availability

## QUESTION
Do existing historical P3 controlled-pair artifacts already contain an executed, interpretable cross-instance differential that can attach a semantic candidate to the Companion C IR without requesting any new runtime or MODELER action?

## HYPOTHESIS
At least one of `P3-CONTROL/CAMERA/BONE/TRANS/VARIANT/MATERIAL-001` has already been executed and durably stored with stage hashes plus a semantic differential.

## PROBE
Targeted archival search only. No runtime or application interaction.

Stores/naming checked:
- Google Drive: all six documented hyphen experiment IDs;
- Google Drive: all six recommended underscore artifact stems (`P3_CONTROL_001` etc.);
- fixed GitHub side snapshot: P3 runbook and manifest template;
- Supabase durable CSMC ledger: rows whose run key/notes contain P3 IDs;
- Base44 `ExperimentLineage`: experiment IDs/notes containing P3 IDs;
- Linear exact search context for `P3-CONTROL-001`.

`csmc_analysis_c_p3_artifact_evidence.py` treats runbooks/templates/mentions as `PLAN_ONLY`. Semantic promotion requires, at minimum, A0/C0/B0 stage hashes, a non-empty C0-vs-B0 differential, and `interpretable=true`.

## SYNTHETIC TEST
Three tests PASS:
1. template/runbook is never execution evidence;
2. A0/C0/B0 hashes + differential + interpretable verdict is classified as executed differential evidence;
3. a plan-only inventory cannot promote semantics.

## REAL AGGREGATE RESULT
- Drive hyphen-ID queries: 6/6 yielded only the canonical handoff plan reference; executed artifact count 0.
- Drive underscore artifact-stem queries: 6/6 returned zero results.
- GitHub runbook status: `READY_FOR_PRIVATE_TARGET_EXECUTION`.
- GitHub manifest: non-empty stage hashes = 0; non-null diffs = 0.
- Supabase matching P3 rows = 0.
- Base44 matching P3 records = 0.
- Linear exact search resolves to RIO-26 planning context; no separate executed-pair artifact was identified.
- Classifier candidates: 3/3 `PLAN_ONLY`; executed interpretable pair found = false; semantic promotion allowed = false.

## INTERPRETATION
Within the durable stores and documented naming conventions examined, P3 exists as an experiment design but not as a durable executed controlled-pair dataset. Therefore the Companion C lane cannot honestly attach camera/bone/transform/variant/material semantics to the IR from historical P3 evidence.

This is a scoped negative result: it does not claim that no private file ever existed anywhere; it says no durable executed pair was found in the project stores searched under the documented IDs/names.

The correct static-lane response is **not** to request a new save or runtime action. The semantic slots remain `UNRESOLVED`, and the lane moves to other existing static evidence.

## NEW INFORMATION
- Historical P3 controlled-pair execution evidence is not durably available in the examined project stores.
- The existing P3 artifacts are planning infrastructure, not semantic teacher-pair evidence.
- No current IR semantic slot may be promoted from P3 history.

## CLOSED HYPOTHESES
- `At least one documented P3 teacher pair is already durably executed and available for static differential analysis` — REJECTED for the examined stores/names.
- `Runbook/template existence is sufficient to support a semantic candidate` — REJECTED.

## CONFIDENCE CHANGES
- `cross-instance differential evidence currently available to Companion C`: UNKNOWN -> LOW/ABSENT IN DURABLE STORES.
- `geometry/index/transform/material/hierarchy can be promoted using existing P3 history`: LOW -> VERY LOW.
- `semantic slots should remain UNRESOLVED`: HIGH -> VERY HIGH.

## NEXT QUESTION
Do existing static code/findings already contain public-safe numeric-pattern evidence (float32/float16/vector/index/matrix/quaternion/weight/string/GUID/count-array) that can narrow a semantic slot without repeating any closed byte-search experiment?
