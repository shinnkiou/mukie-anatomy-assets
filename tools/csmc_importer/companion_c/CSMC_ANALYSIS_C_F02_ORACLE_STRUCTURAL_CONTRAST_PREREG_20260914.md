# CSMC ANALYSIS COMPANION C — F02 physical-oracle structural contrast preregistration

Status: `PREREGISTERED_INTERPRETATION_GATE_NOT_C067`

This is an **unnumbered preparation artifact**, not a physical observation and not C-067. It freezes how future admitted F02 physical-oracle public projections may be summarized before any outcome is known.

## Upstream prerequisites

Input is accepted only as the paired output of oracle-intake v2:

- public projection schema `csmc_f02_mutation_oracle_30_public_v1`;
- receipt schema `csmc_f02_mutation_oracle_intake_receipt_v2`;
- exact source manifest SHA-256 `751f05dfff9d5308dfd96421d5bce43e6785de2cb385fb28a8c97c565c6cc891`;
- receipt canonical SHA must match the supplied public projection;
- upstream validation must be accepted;
- every row entering structural contrast analysis must already be a resolved `DIRECT_PHYSICAL_OBSERVATION` with offset-aware timestamp;
- zero unresolved rows in the v2 physical completion gate.

The evaluator does not read raw/private CSMC bytes and cannot launch MODELER or trigger Save/serialization.

## Fixed structural regions

The 30 preregistered XOR01 variants remain assigned exactly to:

- M01–M10: `PREFIX_INTERIOR`
- M11–M17: `INVARIANT_BOUNDARY`
- M18–M21: `INVARIANT_INTERIOR`
- M22: `ALIGNMENT_EXTENSION`
- M23–M30: `FRAMING_REMAINDER`

Offsets are fixed in code from the already-durable public source manifest/sheets. Region or offset mismatch rejects fail-closed.

## Sentinel-9 preregistration

The first-pass operator subset remains exactly:

`M01 -> M10 -> M13 -> M14 -> M15 -> M18 -> M22 -> M23 -> M30`

This subset may produce only a partial structural checkpoint. It cannot claim completion or semantics.

## Preregistered structural flags

The evaluator may emit only the following predeclared structural candidates:

1. `BOUNDARY_TRIPLET_LOAD_DISRUPTION_CANDIDATE`
   - M10 and M18 are `LOAD_ACCEPTED`; and
   - at least two of M13/M14/M15 are load-disruptive (`LOAD_REJECTED`, `PARTIAL_LOAD`, `ERROR_DIALOG`, `CRASH`, or terminated process).
2. `BOUNDARY_TRIPLET_VISIBLE_DIVERGENCE_CANDIDATE`
   - M10 and M18 load accepted with visible model unchanged; and
   - at least one of M13/M14/M15 loads accepted but changes the visible model.
3. `FRAMING_EDGE_LOAD_DISRUPTION_CANDIDATE`
   - M22 loads accepted; and
   - M23 or M30 is load-disruptive.
4. `FRAMING_SENTINEL_DISAGREEMENT`
   - M23 and M30 have different load-result classes.
5. `PREFIX_SENTINEL_DISAGREEMENT`
   - M01 and M10 have different load-result classes.

These flags indicate only **load/visibility sensitivity at tested offsets**. They do not identify geometry, index, material, UV, rig, weight, owner, codec, or field meaning.

## Complete-batch behavior

A complete 30-row analysis additionally requires the upstream v2 receipt to state `physical_complete=true`. Output includes region-level counts/histograms and the same frozen flags. No post-hoc flag family expansion is allowed within this preregistration.

## Fail-closed guards

Reject:

- public projection hash mismatch;
- wrong batch/source manifest;
- unknown/duplicate variant IDs;
- wrong preregistered offset/region;
- non-direct or UNKNOWN physical classifications;
- unresolved completion-gate rows;
- malformed provenance hashes/timestamps;
- semantic/raw/private payload fields;
- complete projection without upstream physical completion;
- semantic promotion or Blender emit declarations.

Every successful output fixes:

- `interpretation_scope=STRUCTURAL_LOAD_VISIBILITY_ONLY`
- `semantic_promotion=false`
- `blender_emit=false`
- `runtime_dispatch=false`
- `numbered_run_auto_authorized=false`
- `diagnostic_only=true`
- `not_semantic_proof=true`

A real future result must still be reviewed as a genuinely new evidence event before opening a numbered Companion run.
