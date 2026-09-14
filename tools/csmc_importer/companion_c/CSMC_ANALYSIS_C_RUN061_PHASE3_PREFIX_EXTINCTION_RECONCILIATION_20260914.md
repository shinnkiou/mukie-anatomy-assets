# CSMC Analysis Companion C — C-061 — Phase-3 Holdout / Prefix Negative-Control Reconciliation — 2026-09-14

## Source event
This run consumes only newly published public-safe mainline metadata. It does not reacquire or rescan private CSMC bytes.

New source sequence:
- `7ab466ac495cbb09792fad20f0d30e2bb4ed551a` — phase-3 VRoid holdout and bounded prefix exact-qword negative control.
- `c591741eabacfaf3d983328b8065dfab9b53a675` — importer intake v0.3 arithmetic framing exposure.
- Supabase rows 152 and 153.
- Drive findings `13LN932sx-a4OUm8gfqcVEAppCzWt-7bE`; aggregate `1N6bRQIswV6d6EeVrgAKs8LfQmTfPGxeh`.

## New structural information
R04↔V01 supplies a previously unused same-phase holdout:
- logical mod8 = 3
- invariant suffix core = 1,800 qwords / 14,400 bytes
- R04 start = 480
- V01 start = 533,940
- terminal qwords = 2 each

This is independent structural support, not a same-identity semantic control.

Across the six prior same-phase pairs plus this holdout, 7/7 bounded prefix comparisons show zero distinct exact-qword overlap and zero multiset exact-qword overlap. For this tested scope, exact 8-byte token reuse is therefore not a productive current localization method. Smaller-width relationships, size/count laws, owner/container relations and same-identity controls remain open.

## Search-policy reconciliation
C-060 already excluded proven invariant cores for six fixtures. The new mainline result converges on the same fail-closed policy:
- exclude validated invariant core;
- include variable prefix;
- include terminal remainder;
- stop whole-prefix exact-qword reuse hunting for these tested pairs;
- next use preregistered bounded size / stride / count relationship probes.

No semantic owner is inferred from invariance.

## Importer v0.3 framing
Validated relation: `stored_length = align8(logical_length) + 8`.

Importer v0.3 now exposes:
- `aligned_logical_length`
- `alignment_extension_length`
- `framing_remainder_length = 8`

These are structural lengths only. The alignment-extension bytes and final 8-byte remainder remain semantically unresolved.

## Validation
- local self-test: 10/10 PASS
- local pytest: 2/2 PASS
- source controlled CI: 34804715191
- source importer CI: 34804715117

## Classification
`PHASE3_HOLDOUT_PREFIX_EXACT_QWORD_NEGATIVE_CONTROL_RECONCILED`

## Gate state
`STRUCTURAL_ONLY`; semantic binding unresolved; I3_VALID=false; semantic promotion=0; Blender emit blocked; runtime dispatch=false; MODELER/runtime/Worker/Canary/Control Gate actions=0; RIO-26 mutations=0; mainline mutations=0; automatic integration=false; raw/private CSMC publication=false.

## Next
Do not repeat old exact-qword searches. Continue only from genuinely new public-safe structural evidence or an admitted same-identity controlled-evidence event. The next useful file-side family is a preregistered bounded size/stride/count relationship probe over the masked variable-prefix surface.
