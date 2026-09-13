# Companion C — Run C-040 — static unlock validators

## QUESTION
Can future I1-I4 artifacts be accepted fail-closed the moment they arrive, without MODELER/runtime/mainline contact and without intake itself promoting semantics?

## IMPLEMENTATION
Added `csmc_analysis_c_unlock_validators.py`.

The validator is class-specific:
- `I1_ISOLATED_PLUS965_STATIC_REF`: requires isolated pre-existing reference, SHA-256 provenance, storage reference, `character` route, and `plus965` regime.
- `I2_PUBLIC_SAFE_POSITIONAL_AGGREGATE`: requires 22 ordered rows with `record_index / supergroup_index / slot_index / length_blocks / preserve_signature`, four complete groups for records 0..19, and unassigned tail rows 20..21.
- `I3_INTERPRETABLE_CONTROLLED_PAIR_OR_LABELED_DIFFERENTIAL`: requires two artifact hashes, controlled variable, expected relation, bounded observed-difference summary, interpretable=true, and same serializer route.
- `I4_CURRENT_MODEL_NODE_MAPPING_ARTIFACT`: requires current model/mapping identity and an internally closed node/parent mapping with source references.

Common fail-closed checks reject runtime/MODELER/Worker/Control-Gate acquisition modes, invalid provenance hashes, recursive raw/private payload fields, automatic semantic promotion, and automatic Blender emission.

## SYNTHETIC TEST
10/10 PASS:
- one valid example for each I1-I4;
- runtime acquisition rejected;
- raw payload field rejected;
- malformed provenance hash rejected;
- incomplete I2 row set rejected;
- non-interpretable I3 rejected;
- unresolved-parent I4 rejected.

## CURRENT I2 STATUS
C-039 remains authoritative:
- all 22 `record_index` and `length_blocks` are durable;
- `supergroup_index / slot_index` are deterministic for 0..19 and null for tail rows 20..21;
- `preserve_signature` is resolved for 16/22;
- unresolved rows remain exactly 2, 3, 8, 14, 15, 21;
- each unresolved row is one of `0000111` / `0001110`;
- one q24 (or q27) equality bit per unresolved row is sufficient.

The obsolete Drive control-zone-grammar ID currently returns 404 and no replacement was found by exact title search. This is recorded as missing-field provenance; no raw reacquisition was attempted.

## NEW INFORMATION
I1-I4 readiness is now independently machine-checkable. Intake acceptance does not imply codec binding, semantic confirmation, or Blender readiness.

## CLOSED HYPOTHESES
- one generic static-intake manifest is enough to prove I1-I4 completeness: REJECTED.
- missing I2 signatures should be guessed from family marginals: REJECTED.
- validator acceptance may auto-promote semantics: REJECTED.

## CONFIDENCE CHANGES
- future unlock input validation: HIGH -> VERY HIGH.
- current I2 completeness: remains INCOMPLETE by six one-bit observations.
- semantic state: unchanged `STRUCTURAL_ONLY`.
- Blender mesh/scene emit: BLOCKED.
