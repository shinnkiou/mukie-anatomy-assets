# Companion C — Run C-039 — I2 minimal-gap reconstruction

## QUESTION
How much of `I2_PUBLIC_SAFE_POSITIONAL_AGGREGATE` can be reconstructed deterministically from the already-durable public-safe +965 lattice, and what is the smallest remaining input?

## HYPOTHESIS
The durable lattice contains more positional information than C-028/C-029 used directly. In particular, ordered `length_blocks` plus per-record `same_position_matches`, combined with the already-verified q21..27 signature family catalog, may resolve many per-record `preserve_signature` labels without raw bytes.

## INPUTS
Public-safe aggregate only:
- `CSMC_P4_LATTICE_ANALYSIS_20260912.json`
- known family counts from C-002 / control-signature findings
- fixed structural grammar: q0..20 preserved; q21..27 control; q28+ rewritten inside each record

No private payload bytes, MODELER operation, runtime job, Worker, Canary, Control Gate, mainline mutation, or RIO-26 mutation.

## PROBE / IMPLEMENTATION
Added `csmc_analysis_c_i2_minimal_gap.py`.

For each record:
1. keep durable `record_index` and `length_blocks`;
2. derive four complete five-record groups from the ordered first 20 records only after verifying each sequential 5-record length sum is 242 qwords;
3. convert `same_position_matches - 21` into the number of preserved control bits;
4. intersect that count with the already-known `(length_blocks, preserve_signature)` family catalog;
5. emit a signature only when the candidate set is singleton; otherwise remain unresolved.

## SYNTHETIC TEST
3/3 PASS:
- expected 16 resolved / 6 ambiguous reconstruction;
- impossible same-position match count fails closed;
- broken 5-record cadence fails closed.

## REAL AGGREGATE RESULT
The durable lattice resolves substantially more of I2 than previously recognized:

- `record_index`: deterministic for all 22.
- `length_blocks`: durable for all 22.
- `supergroup_index / slot_index`: deterministic for records 0..19 after verifying the four sequential 242-qword groups. Records 20..21 remain unassigned tail rows exactly as allowed by C-029.
- `preserve_signature`: deterministic for 16/22 records.
- only six records remain ambiguous: **2, 3, 8, 14, 15, 21**.
- every ambiguous row is 48 blocks with 24 same-position matches and is exactly one of `0000111` or `0001110`.
- retained family marginals require the six ambiguous rows to split 3/3, leaving `C(6,3)=20` complete assignments, information lower bound `log2(20)=4.3219280949` bits.

The two ambiguous signatures differ at q24 and q27. Therefore a simple public-safe discriminator is enough:
- report q24 equality for the six ambiguous record indices (or equivalently q27), corpus-bound by provenance hash;
- all six bits is the recommended fail-closed artifact;
- if the durable 3/3 family quota is treated as a trusted constraint, five observed bits determine the sixth, but this is not the recommended transport contract.

## PROVENANCE / ROUTE FIELDS
The durable lattice itself contains source kinds and source blob hashes. The input file SHA-256 is used as `provenance_hash`; `container_route=character` and `regime_id=plus965` are already independently durable. No raw bytes or absolute offsets are needed for the reconstructed rows.

## NEW INFORMATION
`I2_PUBLIC_SAFE_POSITIONAL_AGGREGATE` is not missing 22 per-record signatures. The remaining structural evidence gap is a **six-record one-bit discriminator problem**. Six q24 equality bits plus a provenance hash are sufficient to complete the missing signature labels without reacquiring or publishing payload bytes.

## CLOSED HYPOTHESES
- all 22 `preserve_signature` values must be re-extracted from raw payload: REJECTED.
- `supergroup_index = record_index // 5` is merely an unsupported guess: REJECTED for records 0..19 after validating the four sequential 242-qword groups; records 20..21 remain explicitly unassigned.
- current durable aggregate provides no per-record signature information: REJECTED; it resolves 16/22 labels.
- family marginals alone identify all six remaining labels: REJECTED; 20 assignments remain.

## CONFIDENCE CHANGES
- reconstructability of I2 from public-safe aggregates: HIGH -> VERY HIGH.
- minimum remaining signature input: UNKNOWN -> six fixed q24/q27 equality observations (VERY HIGH sufficiency).
- current semantic binding: unchanged; `STRUCTURAL_ONLY`.
- Blender mesh/scene emission: unchanged / BLOCKED.

## NEXT QUESTION
Can the four I1-I4 intake classes be validated fail-closed before future artifacts arrive, including provenance binding, malformed-input rejection, and raw-byte leakage rejection? Execute this next; do not stop at this report.
