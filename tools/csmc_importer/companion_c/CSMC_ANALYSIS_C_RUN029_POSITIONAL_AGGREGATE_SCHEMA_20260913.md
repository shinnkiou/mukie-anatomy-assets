# Companion C — Run C-029

## QUESTION
What is the minimum public-safe positional aggregate needed to make record-family vs five-record-supergroup-slot correlation testable without retaining private payload bytes?

## HYPOTHESIS
Ordered structural metadata alone is sufficient if it preserves record order, complete-group membership, slot, and the two C-002 family axes.

## PROBE
Added `csmc_analysis_c_positional_aggregate.py` plus a machine-readable input specification.

Minimum per-record fields:
- `record_index`
- `supergroup_index` (or null for unassigned tail records)
- `slot_index` 0..4 (or null with no group)
- `length_blocks`
- `preserve_signature`

Minimum corpus metadata:
- `corpus_id`
- `provenance_hash`
- `container_route`
- `regime_id`

Raw bytes and absolute offsets are explicitly not required.

## SYNTHETIC TEST
PASS after correcting one initial fixture expectation before persistence of the findings. The corrected tests cover:
- a deterministic five-slot/five-family synthetic layout with four complete groups and two unassigned tail records
- detection of a structural family intentionally made to span multiple slots
- assigned/unassigned record accounting
- slot-determines-family and family-determines-slot classification

## REAL AGGREGATE RESULT
The current fixed Companion C snapshot does not contain these ordered positional rows, so no real slot-family mutual information is computed. The new schema defines the minimal missing aggregate that would make the question identifiable.

## INTERPRETATION
C-028's positional gap can be closed in the future without copying raw model bytes into public storage. The analyzer can compute slot-family contingency, mutual information, and deterministic mappings from a small public-safe ordered metadata table.

## NEW INFORMATION
- The minimum slot-correlation evidence does not need absolute offsets or raw bytes.
- `record_index + supergroup_index + slot_index + length_blocks + preserve_signature` is sufficient for the current structural question.
- The 22-record corpus can represent four complete groups plus two unassigned tail records without inventing group membership.
- Positional correlation can therefore be separated from binary decoding.

## CLOSED HYPOTHESES
- Absolute file offsets are required for supergroup-slot correlation: REJECTED.
- Raw payload bytes are required for this correlation: REJECTED.
- Family marginal counts alone are sufficient: REJECTED from C-028.

## CONFIDENCE CHANGES
- minimal positional aggregate schema sufficiency: VERY HIGH
- future public-safe slot-correlation feasibility: HIGH -> VERY HIGH
- current real slot-family mapping: remains UNRESOLVED because ordered rows are absent

## NEXT QUESTION
Can Companion C now assemble a complete analysis-package manifest that separates confirmed facts, rejected hypotheses, candidate grammar, structural maps, reusable parser code, current blockers, and exact future evidence contracts for an optional non-merged handoff?
