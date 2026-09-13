# CSMC ANALYSIS COMPANION C — RUN C-048

## QUESTION
Does the new mainline `next-evidence gate` compose cleanly with Companion C C-040/C-045/C-046/C-047, or is there a policy mismatch that could reopen a closed search, bypass an unlock validator, or indirectly reauthorize runtime?

## HYPOTHESIS
The mainline gate should be compatible with Companion C if it is treated strictly as a router over **already-present admissible evidence**. The only apparent difference — mainline requires a complete six-bit I2 discriminator artifact while C-047 also accepts a five-bit quota-assisted residual patch — should disappear if C-047 is understood as a pre-router normalizer rather than a direct mainline route.

## SOURCE
Reference-only public-safe mainline evidence:
- findings commit `dbc352fdff82024246057a48167e97f4ff455568`
- CI head `5c6a7e018ce5ef6a20c94a2c5ba6c2d218e00a6b`
- GitHub Actions run `34757907968`: SUCCESS
- router: `tools/csmc_importer/csmc_p4_next_evidence_gate.py`

The mainline router selects an action only for:
1. a complete six-row I2 discriminator artifact with validated provenance;
2. one or more genuinely new boundary-local decisive owner edges;
3. a validated I1-I4 static unlock class;
4. an already-present exact authorized `.clip` + `.csmc` pair matching established hashes.

With none present it returns `NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS`. It never sets runtime dispatch true.

## RECONCILIATION
### I2 route
No contradiction exists between mainline's six-bit requirement and C-047's five-bit quota-assisted option.

The valid composition is:

`five-bit partial artifact -> C-047 residual validator -> quota/provenance check -> normalized complete six-signature residual -> assemble existing 22-row I2 baseline -> C-040 full validator -> complete-I2 route`

A five-bit partial artifact is therefore **not** a direct input to the mainline route. It is only an input to C-047. Mainline correctly remains stricter at its routing boundary.

### Owner-edge route
Mainline accepts only the same three decisive edge classes left missing by C-045:
- `EXPLICIT_PARENT_RECORD_BOUNDARY`
- `EXPLICIT_PARENT_LENGTH_FIELD`
- `EXPLICIT_CONSUMER_CROSSREF`

A new edge triggers review of that edge only. It does not reopen the six-surface C-045 search.

### Validated I1-I4 route
Mainline's short `I1`..`I4` labels map one-to-one to the C-040 full unlock classes. Intake remains non-semantic.

### Exact authorized raw-pair route
This route is compatible only as an **external already-present input event**. Companion C is not allowed to seek, reacquire, request, or dispatch work to obtain the pair.

Companion-side prerequisite is stricter:
- external hash match already verified;
- C-040 I1 static validation accepted;
- then and only then the preregistered fixed-role probe may be run;
- no post-hoc window widening.

## IMPLEMENTATION
Added `csmc_analysis_c_next_evidence_router_adapter.py`.

It fails closed on:
- any evidence acquisition request;
- any runtime dispatch request;
- missing explicit `auto_semantic_promotion=false` or `auto_blender_emit=false`;
- an unvalidated complete I2 residual;
- an externally present pair without prior hash verification + I1 validation.

It emits only bounded static actions and always fixes:
- runtime_dispatch=false
- evidence_acquisition=false
- semantic_promotion=false
- blender_emit=false
- mainline_mutation=false
- rio26_mutation=false

## SYNTHETIC TEST
11/11 PASS against identical adapter logic:
- empty state -> no action
- complete C-047-normalized I2 -> assemble + full C-040 validation
- five-bit partial -> C-047 only, never direct mainline route
- unvalidated six-bit residual rejects
- valid new owner edge -> review only that edge
- short I3 alias normalizes to full C-040 class
- external pair without I1 validation rejects
- validated external pair -> preregistered fixed-role probe only
- runtime flag cannot reauthorize runtime
- acquisition request rejects
- multiple valid static inputs stay non-semantic/non-mutating

## NEW INFORMATION
- Mainline and Companion C now have a mechanically explicit composition boundary rather than two merely similar policy descriptions.
- C-047's five-bit assisted path is a pre-router normalization step, not a relaxation of mainline's complete-I2 gate.
- The external raw-pair route does not grant Companion C acquisition authority; it is legal only after an already-present artifact passes I1 validation.
- Current state across both routers is the same: `NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS` until genuinely new evidence appears.

## CLOSED HYPOTHESES
- C-047 five-bit support conflicts with mainline's six-bit requirement: REJECTED.
- Mainline exact-pair route authorizes Companion C to reacquire the pair: REJECTED.
- Runtime authorization metadata can be converted by the static router into runtime dispatch: REJECTED.
- A new owner edge should cause C-045's bounded search to rerun: REJECTED.
- Validated static intake may implicitly promote semantics or Blender emit: REJECTED.

## CONFIDENCE CHANGES
- cross-lane next-evidence routing consistency: HIGH -> VERY HIGH.
- fail-closed no-action state under current durable corpus: VERY HIGH -> EXTREMELY HIGH.
- I2 unlock state: remains `INCOMPLETE_WAITING_NEW_EQUALITY_BITS`.
- owner proof: remains 0/3 decisive boundary-local edges.
- pipeline: `STRUCTURAL_ONLY`; semantic promotion=0; Blender emit BLOCKED.

## NEXT
Do not manufacture another research run from the same corpus. Resume only when one of the router's accepted evidence events actually becomes present. Read-only monitoring may note a new event; Companion C must not create it through runtime or acquisition.
