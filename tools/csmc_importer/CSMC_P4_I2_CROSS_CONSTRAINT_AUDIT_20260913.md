# CSMC P4 I2 cross-constraint audit — 2026-09-13

Status: **PUBLIC-SAFE STATIC PASS / ZERO MODELER / ZERO RUNTIME / NO SEMANTIC PROMOTION**

## Question

Can the six unresolved `I2_PUBLIC_SAFE_POSITIONAL_AGGREGATE` preserve signatures be reduced further by combining all already-durable constraints, without reacquiring raw payload bytes or guessing from marginals?

Authoritative unresolved rows from Companion C C-039:

- record indices: `2, 3, 8, 14, 15, 21`
- each row: 48 qwords / 24 same-position matches
- each candidate set: `{0000111, 0001110}`
- trusted family quota across those six: 3 / 3

## Direct combinatorial result

A fail-closed enumerator was added in `csmc_p4_i2_cross_constraint_audit.py`.

Under the only durable constraint that directly restricts these preserve-signature assignments — the 3/3 family quota — exactly:

`C(6,3) = 20`

complete assignments remain.

For every one of the six ambiguous record indices, both candidate signatures occur among the 20 admissible assignments. Therefore:

- forced rows: **0 / 6**
- deterministic assignment reduction: **none**
- remaining complete assignments: **20**

## Why the other durable facts do not reduce the 20 assignments

### Five-record / 242-qword cadence

The four verified supergroups constrain ordered record lengths and group sums. They do not establish a preserve-signature composition rule or a q24/q27 equality rule per slot. Companion C C-028 explicitly found family-to-slot mapping non-identifiable from the retained aggregate.

### Character route correlation

C-011 establishes that the +965 family corpus belongs to the `catalog_character/character` comparison surface. It does not map individual preserve signatures to internal owner positions or supergroup slots.

### Counted-BE entropy ceilings

The entropy ceilings constrain how many rows could exact-fit a counted-BE f32 codec at fixed role starts. They do not determine whether q24 or q27 is cross-serialization equal for any individual ambiguous record. Equality/preservation and codec identity remain separate axes.

Therefore none of these orthogonal facts may be converted into a signature constraint without introducing a new unsupported assumption.

## Exact remaining evidence contract

The previous C-039 transport contract remains unchanged:

- recommended: six corpus-bound q24 equality bits for records `2,3,8,14,15,21` (or q27 equivalents), plus provenance hash;
- quota-assisted theoretical minimum: five such bits only if the 3/3 family quota remains trusted;
- do not guess the sixth or any other signature from visual pattern, slot aesthetics, or marginal frequencies alone.

## Closed hypotheses

- existing supergroup locality forces one or more of the six signatures: **REJECTED**;
- route ownership forces one or more signatures: **REJECTED**;
- counted-BE family/entropy constraints determine q24/q27 equality: **REJECTED**;
- the six-bit I2 gap can be reduced deterministically from the current durable corpus: **REJECTED**.

## Consequence

The I2 gap is now independently cross-checked as a genuine new-evidence boundary, not an overlooked algebraic deduction. Repeating static recombination of the same corpus has no justified path to resolve the six bits.

This does not authorize raw-byte reacquisition, MODELER interaction, runtime tracing, Save/Ctrl+S, Worker mutation, semantic promotion, or Blender emission.
