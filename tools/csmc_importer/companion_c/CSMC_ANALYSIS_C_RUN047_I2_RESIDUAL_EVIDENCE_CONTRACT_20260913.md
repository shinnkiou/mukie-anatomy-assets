# CSMC ANALYSIS COMPANION C — RUN C-047

## QUESTION
Does the new public-safe mainline I2 cross-constraint audit change the C-040 unlock boundary, and can its exact residual evidence requirement be converted into a fail-closed transport contract without reacquiring raw bytes?

## HYPOTHESIS
If all current durable constraints leave 20 complete 3/3 assignments and force 0/6 ambiguous rows, no further static recombination can legitimately fill the six preserve signatures. The useful next step is therefore not another inference pass, but a machine-checkable residual patch contract for the genuinely missing q24/q27 equality observations.

## NEW CROSS-LANE INPUT
Reference-only evidence from `csmc-importer-experimental-20260902`:
- findings commit `98bf20e5b1380832343146b37515bb5a837608b6` — `Record I2 cross-constraint closure`
- CI-enabling commit `08919bd359fa29749125f771cd570667edde3361`
- GitHub Actions run `34757761870` — SUCCESS

Mainline result:
- ambiguous indices = `2,3,8,14,15,21`
- each candidate set = `{0000111, 0001110}`
- trusted quota across six = 3 / 3
- complete assignments under direct signature constraints = `C(6,3)=20`
- forced rows = `0/6`
- five-record cadence, character route correlation, and counted-BE ceilings do not logically constrain the missing q24/q27 equality bits.

## PROBE / IMPLEMENTATION
Added `csmc_analysis_c_i2_residual_patch.py` on the isolated Companion C branch.

The contract accepts only corpus-bound public-safe equality observations for the fixed residual set. It understands the two equivalent discriminators encoded by the known signatures:
- q24: `0 -> 0000111`, `1 -> 0001110`
- q27: `1 -> 0000111`, `0 -> 0001110`

Two gap-closing modes are permitted:
1. **Recommended six-bit mode** — exactly one q24 or q27 equality bit for each of the six residual indices. The observed six signatures must agree with the trusted 3/3 family quota.
2. **Quota-assisted five-bit mode** — exactly five distinct residual observations plus the trusted 3/3 quota and a separate quota provenance hash. The sixth signature is derived only when the remaining quota forces exactly one value.

This is a residual-patch validator only. It does **not** replace the C-040 full 22-row I2 validator. A closed residual gap is marked `full_i2_assembly_ready=true`, after which the existing baseline plus the six resolved signatures must still be assembled and passed through C-040.

## SYNTHETIC TEST
11/11 PASS against identical contract logic:
- six q24 observations close the gap
- six q27 observations are equivalent
- five observations + trusted quota derive a unique sixth signature
- five observations without quota assistance reject
- bad quota provenance rejects
- duplicate residual index rejects
- non-residual index rejects
- boolean/non-bit equality value rejects
- raw payload field rejects
- bad corpus provenance rejects
- six observations conflicting with the 3/3 quota reject

## INTERPRETATION
The new mainline audit does **not** provide the missing I2 bits and therefore does not unlock I2 by itself. It does something different and useful: it closes the possibility that the six bits can be recovered from already-durable cadence/route/codec facts without a new observation.

C-040's substantive boundary is strengthened:
- current I2 remains incomplete by six record-local equality observations;
- five observations are only sufficient if the existing 3/3 quota remains trusted and independently provenance-bound;
- any attempt to infer a row from supergroup position, visual pattern, route owner, or counted-BE compatibility is rejected as unsupported cross-axis leakage.

## NEW INFORMATION
- The I2 gap is now independently proven to have 20 admissible complete assignments under the current direct signature constraints and 0 forced rows.
- The six missing signatures are a genuine new-evidence boundary rather than an overlooked combinatorial deduction.
- A precise public-safe transport contract now exists for closing that gap without raw bytes: six equality bits recommended; five plus trusted quota/provenance is the theoretical assisted minimum.
- q24 and q27 are formally interchangeable discriminators for the two remaining signatures under the known seven-bit preserve grammar.

## CLOSED HYPOTHESES
- Existing five-record cadence forces at least one ambiguous preserve signature: REJECTED.
- Character route ownership forces at least one ambiguous preserve signature: REJECTED.
- C-046 counted-BE family compatibility can determine q24/q27 equality: REJECTED.
- Recombining the current durable corpus can reduce the six-bit I2 gap deterministically: REJECTED.
- Five equality bits are sufficient without a trusted 3/3 quota: REJECTED.
- A residual patch can bypass the full C-040 22-row validator: REJECTED.

## CONFIDENCE CHANGES
- I2 residual-gap diagnosis: VERY HIGH -> EXTREMELY HIGH within current public-safe corpus.
- exact residual evidence contract: HIGH -> VERY HIGH.
- I2 unlock state: remains INCOMPLETE.
- codec binding: remains UNCONFIRMED.
- semantic state: unchanged `STRUCTURAL_ONLY`; semantic promotion count=0.
- Blender emit: BLOCKED.

## NEXT QUESTION
Wait for a genuinely new public-safe I2 equality-bit artifact or another I1/I3/I4 unlock. Do not repeat static recombination of the same six-row corpus. Do not request MODELER/runtime/Save/Worker activity from Companion C.
