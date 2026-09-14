# CSMC F02 Mutation 30 Structural Map v1

- Source batch: `CSMC_F02_SINGLE_BYTE_XOR01_30_20260914`
- Source public manifest SHA-256: `751f05dfff9d5308dfd96421d5bce43e6785de2cb385fb28a8c97c565c6cc891`
- Map JSON SHA-256: `18d4916bc040c3d624b003cf469470e7643a76017a6a0815ba00d166037d8ab1`
- Classification: `STRUCTURAL_ONLY`
- Physical MODELER oracle: `0/30 PENDING_MANUAL_ORACLE`
- `semantic_promotion=false`, `blender_emit=false`, `runtime_dispatch=false`

## Confirmed frame

- payload offset: `65`
- logical length: `17687`
- proven invariant start: `3216`
- alignment extension start: `17687`
- framing remainder start: `17688`

## Observation firewall

Prediction and observation are separate. No unobserved MODELER load/visual/process result is asserted.
All 30 observations remain pending; Save/Save As/edit/serialization remains outside this offline map.

## Discrimination questions

### Q-BND-01
- A: `BOUNDARY_TRANSITION_IS_STRUCTURALLY_SPECIAL`
- B: `NO_BOUNDARY_TRANSITION_EFFECT`
- property: Whether the variable→proven-invariant transition has a distinct oracle response relative to immediate flanks.
- primary mutations: `M13, M14, M15`
- static evidence target: A direct consumer read/data-flow that crosses or terminates at the same boundary would independently support localization.
- result: `UNRESOLVED`

### Q-BND-02
- A: `BOUNDARY_EFFECT_IS_LOCALIZED`
- B: `BOUNDARY_EFFECT_EXTENDS_ACROSS_NEIGHBORHOOD`
- property: Width/locality of any response change around the boundary.
- primary mutations: `M11, M12, M13, M14, M15, M16, M17`
- static evidence target: Loop/count/allocation/read span that establishes a bounded consumer scope around this neighborhood.
- result: `UNRESOLVED`

### Q-INV-01
- A: `INVARIANT_CORE_HAS_CONSISTENT_SENSITIVITY`
- B: `INVARIANT_CORE_CONTAINS_LOCAL_SUBSTRUCTURE`
- property: Whether widely separated invariant-interior mutations behave uniformly or partition into subregions.
- primary mutations: `M18, M19, M20, M21`
- static evidence target: Independent direct-read destinations or loop scopes at one or more corresponding offsets.
- result: `UNRESOLVED`

### Q-PFX-01
- A: `VARIABLE_PREFIX_INTERIOR_UNIFORM`
- B: `VARIABLE_PREFIX_CONTAINS_LOCAL_SUBSTRUCTURE`
- property: Whether prefix-interior responses remain uniform across increasing offsets.
- primary mutations: `M01, M02, M03, M04, M05, M06, M07, M08, M09, M10`
- static evidence target: Direct read/allocation/copy evidence mapping any prefix subrange to a destination.
- result: `UNRESOLVED`

### Q-TERM-01
- A: `ALIGNMENT_EXTENSION_IS_DISTINCT_FROM_FRAMING_REMAINDER`
- B: `TERMINAL_EXTENSION_AND_REMAINDER_BEHAVE_UNIFORMLY`
- property: Whether the single alignment-extension byte differs from the framing remainder.
- primary mutations: `M22, M23, M24, M25, M26, M27, M28, M29, M30`
- static evidence target: Direct length/alignment/read-bound evidence distinguishing logical end handling from frame remainder handling.
- result: `UNRESOLVED`

## Companion C preregistration reconciliation

Supabase row `186` / Companion commit `66b2599be5398e53f9c783497414746e83c5dbbd` already freezes the Sentinel-9 evaluator order:

`M01 -> M10 -> M13 -> M14 -> M15 -> M18 -> M22 -> M23 -> M30`

This map is supplemental. Its offline information-gain ranking does **not** replace that preregistered evaluator order and does not create a physical observation. If physical intake proceeds through that frozen Companion path, its fail-closed order/receipt rules remain authoritative.

## Adaptive oracle ranking

This is an information-gain proxy only, not a semantic truth score.

| Rank | Mutation | Structural location | Questions |
|---:|---|---|---|
| 1 | M14 | PROVEN_INVARIANT_BOUNDARY_EXACT @ 3216 | Q-BND-01, Q-BND-02 |
| 2 | M13 | VARIABLE_TO_INVARIANT_BOUNDARY_APPROACH @ 3215 | Q-BND-01, Q-BND-02 |
| 3 | M15 | PROVEN_INVARIANT_BOUNDARY_DEPARTURE @ 3217 | Q-BND-01, Q-BND-02 |
| 4 | M11 | VARIABLE_TO_INVARIANT_BOUNDARY_APPROACH @ 3200 | Q-BND-02 |
| 5 | M12 | VARIABLE_TO_INVARIANT_BOUNDARY_APPROACH @ 3208 | Q-BND-02 |
| 6 | M16 | PROVEN_INVARIANT_BOUNDARY_DEPARTURE @ 3224 | Q-BND-02 |
| 7 | M17 | PROVEN_INVARIANT_BOUNDARY_DEPARTURE @ 3232 | Q-BND-02 |
| 8 | M22 | ALIGNMENT_EXTENSION @ 17687 | Q-TERM-01 |
| 9 | M23 | FRAMING_REMAINDER @ 17688 | Q-TERM-01 |
| 10 | M18 | PROVEN_INVARIANT_INTERIOR @ 3728 | Q-INV-01 |
| 11 | M19 | PROVEN_INVARIANT_INTERIOR @ 7312 | Q-INV-01 |
| 12 | M20 | PROVEN_INVARIANT_INTERIOR @ 11408 | Q-INV-01 |
| 13 | M21 | PROVEN_INVARIANT_INTERIOR @ 15216 | Q-INV-01 |
| 14 | M24 | FRAMING_REMAINDER @ 17689 | Q-TERM-01 |
| 15 | M25 | FRAMING_REMAINDER @ 17690 | Q-TERM-01 |
| 16 | M26 | FRAMING_REMAINDER @ 17691 | Q-TERM-01 |
| 17 | M27 | FRAMING_REMAINDER @ 17692 | Q-TERM-01 |
| 18 | M28 | FRAMING_REMAINDER @ 17693 | Q-TERM-01 |
| 19 | M29 | FRAMING_REMAINDER @ 17694 | Q-TERM-01 |
| 20 | M30 | FRAMING_REMAINDER @ 17695 | Q-TERM-01 |
| 21 | M01 | VARIABLE_PREFIX_CANDIDATE_REGION @ 8 | Q-PFX-01 |
| 22 | M02 | VARIABLE_PREFIX_CANDIDATE_REGION @ 64 | Q-PFX-01 |
| 23 | M03 | VARIABLE_PREFIX_CANDIDATE_REGION @ 128 | Q-PFX-01 |
| 24 | M04 | VARIABLE_PREFIX_CANDIDATE_REGION @ 256 | Q-PFX-01 |
| 25 | M05 | VARIABLE_PREFIX_CANDIDATE_REGION @ 512 | Q-PFX-01 |
| 26 | M06 | VARIABLE_PREFIX_CANDIDATE_REGION @ 1024 | Q-PFX-01 |
| 27 | M07 | VARIABLE_PREFIX_CANDIDATE_REGION @ 1536 | Q-PFX-01 |
| 28 | M08 | VARIABLE_PREFIX_CANDIDATE_REGION @ 2048 | Q-PFX-01 |
| 29 | M09 | VARIABLE_PREFIX_CANDIDATE_REGION @ 2560 | Q-PFX-01 |
| 30 | M10 | VARIABLE_PREFIX_CANDIDATE_REGION @ 3072 | Q-PFX-01 |

## Closed exact scopes retained

The map does not reopen or widen the already rejected exact Phase-7/8/9 families or the simple 96-byte literal insertion model.

## Mutation map

| Mutation | Offset | mod8 | Class | Structural region | Align relation | Frame relation |
|---|---:|---:|---|---|---|---|
| M01 | 8 | 0 | VARIABLE | VARIABLE_PREFIX_CANDIDATE_REGION | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M02 | 64 | 0 | VARIABLE | VARIABLE_PREFIX_CANDIDATE_REGION | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M03 | 128 | 0 | VARIABLE | VARIABLE_PREFIX_CANDIDATE_REGION | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M04 | 256 | 0 | VARIABLE | VARIABLE_PREFIX_CANDIDATE_REGION | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M05 | 512 | 0 | VARIABLE | VARIABLE_PREFIX_CANDIDATE_REGION | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M06 | 1024 | 0 | VARIABLE | VARIABLE_PREFIX_CANDIDATE_REGION | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M07 | 1536 | 0 | VARIABLE | VARIABLE_PREFIX_CANDIDATE_REGION | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M08 | 2048 | 0 | VARIABLE | VARIABLE_PREFIX_CANDIDATE_REGION | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M09 | 2560 | 0 | VARIABLE | VARIABLE_PREFIX_CANDIDATE_REGION | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M10 | 3072 | 0 | VARIABLE | VARIABLE_PREFIX_CANDIDATE_REGION | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M11 | 3200 | 0 | VARIABLE | VARIABLE_TO_INVARIANT_BOUNDARY_APPROACH | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M12 | 3208 | 0 | VARIABLE | VARIABLE_TO_INVARIANT_BOUNDARY_APPROACH | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M13 | 3215 | 7 | VARIABLE | VARIABLE_TO_INVARIANT_BOUNDARY_APPROACH | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M14 | 3216 | 0 | INVARIANT | PROVEN_INVARIANT_BOUNDARY_EXACT | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M15 | 3217 | 1 | INVARIANT | PROVEN_INVARIANT_BOUNDARY_DEPARTURE | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M16 | 3224 | 0 | INVARIANT | PROVEN_INVARIANT_BOUNDARY_DEPARTURE | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M17 | 3232 | 0 | INVARIANT | PROVEN_INVARIANT_BOUNDARY_DEPARTURE | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M18 | 3728 | 0 | INVARIANT | PROVEN_INVARIANT_INTERIOR | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M19 | 7312 | 0 | INVARIANT | PROVEN_INVARIANT_INTERIOR | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M20 | 11408 | 0 | INVARIANT | PROVEN_INVARIANT_INTERIOR | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M21 | 15216 | 0 | INVARIANT | PROVEN_INVARIANT_INTERIOR | BEFORE_ALIGNMENT_EXTENSION | BEFORE_FRAMING_REMAINDER |
| M22 | 17687 | 7 | TERMINAL_EXTENSION | ALIGNMENT_EXTENSION | AT_ALIGNMENT_EXTENSION_START | BEFORE_FRAMING_REMAINDER |
| M23 | 17688 | 0 | TERMINAL_FRAMING | FRAMING_REMAINDER | AFTER_ALIGNMENT_EXTENSION | AT_FRAMING_REMAINDER_START |
| M24 | 17689 | 1 | TERMINAL_FRAMING | FRAMING_REMAINDER | AFTER_ALIGNMENT_EXTENSION | INSIDE_FRAMING_REMAINDER |
| M25 | 17690 | 2 | TERMINAL_FRAMING | FRAMING_REMAINDER | AFTER_ALIGNMENT_EXTENSION | INSIDE_FRAMING_REMAINDER |
| M26 | 17691 | 3 | TERMINAL_FRAMING | FRAMING_REMAINDER | AFTER_ALIGNMENT_EXTENSION | INSIDE_FRAMING_REMAINDER |
| M27 | 17692 | 4 | TERMINAL_FRAMING | FRAMING_REMAINDER | AFTER_ALIGNMENT_EXTENSION | INSIDE_FRAMING_REMAINDER |
| M28 | 17693 | 5 | TERMINAL_FRAMING | FRAMING_REMAINDER | AFTER_ALIGNMENT_EXTENSION | INSIDE_FRAMING_REMAINDER |
| M29 | 17694 | 6 | TERMINAL_FRAMING | FRAMING_REMAINDER | AFTER_ALIGNMENT_EXTENSION | INSIDE_FRAMING_REMAINDER |
| M30 | 17695 | 7 | TERMINAL_FRAMING | FRAMING_REMAINDER | AFTER_ALIGNMENT_EXTENSION | INSIDE_FRAMING_REMAINDER |

## Current result

The 30-mutation batch is no longer an undifferentiated waiting set: it is mapped to five bounded structural contrasts.
The highest first physical observation is `M14` (exact invariant boundary), followed by immediate flanks `M13` / `M15`.
This prioritization does **not** assert what MODELER will do; it only minimizes observations needed to discriminate competing structural explanations.
