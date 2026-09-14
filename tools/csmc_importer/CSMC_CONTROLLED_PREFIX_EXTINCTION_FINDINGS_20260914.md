# CSMC Mainline — Phase-3 VRoid Holdout + Variable-Prefix Exact-Qword Negative Control — 2026-09-14

## QUESTION

After the phase-normalized invariant-region result, can a previously unused same-phase class provide independent structural support, and does exact 8-byte reuse remain useful inside the bounded variable prefixes?

## METHOD

The six previously published same-phase invariant intervals are validated at their published coordinates; they are not rediscovered. A seventh pair, R04 CUBE_B2_SPLIT ↔ V01 VROID_BODY_BASE, is used as a mod-3 holdout because mod 3 was absent from the prior six same-phase selected comparisons. The holdout suffix search is bounded to trailing budgets {1,2}, inherited from the prior observed same-phase runs. The probe then compares only the prefixes before each exact invariant core and emits counts only, never qword values or raw CSMC bytes.

## OBSERVED STRUCTURAL RESULT

### Phase-3 VRoid holdout

R04 ↔ V01:

- both `logical_length mod 8 = 3`
- R04 qword count: **2,282**
- V01 qword count: **535,742**
- exact suffix core: **1,800 qwords = 14,400 bytes**
- invariant start: R04 qword **480**, V01 qword **533,940**
- trailing qwords after core: **2 / 2**

Classification: `PHASE3_VROID_HOLDOUT_INVARIANT_SUFFIX_VALIDATION`.

This strengthens the existing `STRUCTURAL_PHASE_CLASS_CANDIDATE` with a substantially larger independent teacher fixture. It does not assign semantics to the core and does not establish a globally necessary/sufficient phase rule.

### Variable-prefix exact-qword overlap

Across all seven bounded same-phase comparisons (the six published pairs plus the mod-3 VRoid holdout):

- distinct exact qwords shared between the two variable prefixes: **0 / 7 pairs**
- multiset exact-qword overlap between the two variable prefixes: **0 / 7 pairs**

This includes R04's 480-qword prefix against V01's 533,940-qword prefix.

Classification: `PHASE_NORMALIZED_PREFIX_EXACT_QWORD_REUSE_NOT_OBSERVED`.

## CONFOUNDERS / NEGATIVE CONTROL

Fixture identity/name/construction-route confounds remain. The earlier source-name literal probe rejected straightforward ASCII/UTF-16 name carving, but did not prove names absent. VRoid is an independent scale/control fixture, not a same-identity semantic control.

The zero-overlap result is negative evidence against continuing exact-qword identity hunting inside these bounded variable prefixes. It does not reject transformed relationships, size/count laws, owner/container relationships, or smaller-width numeric structure. No codec, cipher, encryption, compression, checksum, or hash algorithm is inferred.

## FRAMING NOTE

The validated outer relation remains `stored_length = align8(logical_length) + 8`. Structurally this permits a length-only decomposition into the logical region, `align8(logical)-logical` alignment-extension bytes, and a final 8-byte framing remainder. The alignment-extension bytes are not labeled padding, and the final 8 bytes are not labeled checksum/hash.

## IMPORTER CONSEQUENCE

A new public-safe `csmc_pair_search_mask.py` converts validated pair-invariant evidence into a fail-closed structural search mask:

- EXCLUDE the exact invariant core;
- INCLUDE the variable prefix;
- INCLUDE the small terminal remainder after the core.

The mask is structural metadata only. It cannot promote semantics or authorize Blender emission.

## CONFIDENCE / GATE

- phase-class structural behavior: strengthened, non-semantic
- geometry direct field: UNRESOLVED
- index/topology direct field: UNRESOLVED
- UV/material/bone/weight direct fields: UNCONFIRMED
- I3_VALID pairs: 0
- semantic promotion count: 0
- Blender emit: BLOCKED
- runtime dispatch: false
- MODELER/runtime/Worker/Canary/Control Gate actions: 0
- raw/private CSMC publication: false

## NEXT ACTION

Stay file-side. Stop whole-prefix exact-qword reuse hunting for the tested pairs. Use the structural search mask and test a small preregistered set of size/stride/count relationships against known teacher quantities, with VRoid reserved for independent validation. Request a new same-identity fixture only when one specific missing discriminator is demonstrated.
