# Companion C — Run C-021

## QUESTION
Should counted-codec recurrence be required to occur inside the same joint record family `(length_blocks, preserve_signature)`, or should same-role recurrence across families also count?

## INPUT
C-002 established five joint families among 22 records with sizes 7, 3, 3, 3, and 6.

## PROBE
For one fixed side+structural role there are C(22,2)=231 possible record pairs.
- pairs inside the same joint family: 45
- pairs crossing distinct joint families: 186

Thus 80.52% of possible same-role record pairs cross family boundaries.

## INTERPRETATION
Making same-family recurrence mandatory would discard most possible recurrence evidence and would assume, without proof, that codec behavior cannot generalize across serializer-family variants.

A better evidence taxonomy is:
1. `RECURRENT_ROLE_BINDING`: at least two exact fits in distinct records for the same side+structural role. This is the baseline codec-binding condition from C-018/C-020.
2. `FAMILY_LOCAL_SUPPORT`: those recurrent fits also share the same `(length_blocks,preserve_signature)` family. This supports a family-local codec instance.
3. `CROSS_FAMILY_SUPPORT`: recurrent fits occur in distinct joint families while preserving side+structural role. This supports a codec rule that survives structural-family variation and is therefore broader evidence, not weaker evidence.

No semantic meaning is assigned by any tier.

## NEW INFORMATION
- Same-family pairs account for only 19.48% of possible same-role pairs; cross-family pairs account for 80.52%.
- Record-family identity should refine the scope of a codec binding, not gate whether a same-role recurrent binding exists at all.
- Cross-family recurrence can be interpreted as generalization evidence across serializer-family variants.

## CLOSED HYPOTHESES
- Confirmed codec binding must require recurrence inside exactly one joint record family: REJECTED.
- Cross-family recurrence is inherently weaker than same-family recurrence: REJECTED.
- Record-family identity can be ignored after a binding is found: REJECTED; it remains useful for scope classification.

## CONFIDENCE CHANGES
- baseline same-role recurrence rule: VERY HIGH, unchanged
- same-family recurrence as mandatory gate: MEDIUM -> LOW
- family identity as binding-scope annotation: MEDIUM -> VERY HIGH
- cross-family recurrence as generalization evidence: LOW -> HIGH

## NEXT QUESTION
Can the parser IR encode codec-binding scope (`role-level`, `family-local`, `cross-family-generalized`) without changing any semantic slot or Blender emission gate?
