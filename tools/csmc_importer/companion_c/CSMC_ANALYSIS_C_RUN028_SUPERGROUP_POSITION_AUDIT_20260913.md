# Companion C — Run C-028

## QUESTION
Can the four complete five-record / 1,936-byte supergroups be correlated to record-family slot positions using only the retained public-safe aggregate evidence?

## HYPOTHESIS
If the retained aggregate preserves ordered per-record family identity or group/slot indices, family-to-slot correlation can be tested without raw payload bytes.

## PROBE
Audit only the fixed Companion C aggregate artifacts already retained from C-002 and C-011. No raw payload read, no cadence fitting, no boundary refit, no canonical repoll.

Retained facts:
- 22 complete +965 records
- five joint `(length_blocks, preserve_signature)` families with counts 7 / 3 / 3 / 3 / 6
- four complete five-record groups, each 242 qwords = 1,936 bytes
- all current records belong to the character external-payload comparison surface

Missing from the retained public-safe aggregate:
- ordered family label for each record index
- supergroup index for each record
- slot index 0..4 inside each complete supergroup
- explicit mapping from record index to one of the four complete supergroups

## REAL AGGREGATE RESULT
The slot-correlation question is not identifiable from the current retained marginals. Family counts plus a known 5-record periodic group size do not uniquely determine the ordered family sequence or family-to-slot mapping. Multiple different record sequences can have the same five family counts and the same number/size of complete supergroups.

No internal section/owner claim is promoted.

## INTERPRETATION
This is a retention-granularity gap, distinct from the private-binary input gap identified in C-016/C-027. Raw bytes are not necessarily required to answer this question; an ordered public-safe positional aggregate would be sufficient.

## NEW INFORMATION
- The current public-safe retention is sufficient for family-count statistics but insufficient for family-vs-supergroup-slot correlation.
- A new evidence-gap class exists: `POSITIONAL_AGGREGATE_GAP`.
- The missing information can be supplied as public-safe metadata; raw model bytes are not intrinsically required for this particular correlation test.

## CLOSED HYPOTHESES
- Five-record periodicity plus the five family marginal counts uniquely determines slot mapping: REJECTED.
- The retained C-002/C-011 aggregate already contains enough positional information to infer internal owner/child slots: REJECTED.
- Raw payload bytes are strictly necessary for a future slot-correlation test: REJECTED; ordered aggregate metadata would suffice.

## CONFIDENCE CHANGES
- named internal owner/section from supergroup periodicity: remains VERY LOW / UNRESOLVED
- `POSITIONAL_AGGREGATE_GAP` diagnosis: VERY HIGH
- feasibility of future slot correlation from aggregate-only metadata: HIGH

## NEXT QUESTION
What is the minimum public-safe positional aggregate schema that would make family-to-supergroup-slot correlation testable without storing private payload bytes?
