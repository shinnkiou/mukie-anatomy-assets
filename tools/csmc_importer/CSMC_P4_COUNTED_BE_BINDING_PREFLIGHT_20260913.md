# CSMC P4 counted-BE fixed-role binding preflight — 2026-09-13

Status: `FIXED_SCAN_PROTOCOL_READY__BE_F64_SHAPE_EXCLUDED_FOR_PREDECLARED_ROLES`

This checkpoint is file-side/static only. It uses the already verified `+965` variable-record grammar and contains no purchased payload bytes, decoded model content, credentials, or runtime dump bytes.

## Why this pass exists

Companion C reduced the remaining codec-binding gap to recurrent exact fits at the same current-payload structural role. C-017 also required a fixed scan protocol and an explicit multiple-testing budget rather than post-hoc window selection.

The mainline now has a bounded probe for exactly that question: `csmc_p4_counted_be_binding_probe.py`.

It does **not** scan arbitrary offsets. It tests only four roles that were independently bounded before this codec test:

1. `record_whole` — the verified 48/49-qword record boundary;
2. `stable_prefix_0_20` — 21-qword / 168-byte stable prefix;
3. `control_zone_21_27` — 7-qword / 56-byte equality-control zone;
4. `preserved_island_25_26` — 2-qword / 16-byte always-preserved island.

For the known 22 complete records and two corresponding serializations this defines 176 eligible fixed-role codec opportunities after shape filtering. No post-hoc windows are added after observing bytes.

## Shape-only narrowing before reading payload values

CELSYS counted numeric encoding is independently confirmed as:

`u32 big-endian count + count × big-endian numeric value`

For the four predeclared roles, all region sizes are multiples of 8. After removing the 4-byte count prefix, every region is therefore `4 mod 8` bytes long.

Result: **BE-f64 is structurally impossible for every one of these fixed roles.**

BE-f32 remains shape-compatible, with the exact expected counts fixed in advance:

| Structural role | Region bytes | Expected BE-f32 count |
|---|---:|---:|
| 48-qword whole record | 384 | 95 |
| 49-qword whole record | 392 | 97 |
| stable prefix `0..20` | 168 | 41 |
| control zone `21..27` | 56 | 13 |
| preserved island `25..26` | 16 | 3 |

This is a codec-shape result only. It does not establish that any role is actually a counted vector.

## Probe contract

For each complete +965 record and each of the two mapped payload surfaces, the probe:

- extracts only the four predeclared roles;
- checks the leading BE u32 against the exact count implied by region length;
- unpacks only when the length/count relation is exact;
- reports encoding/count/finite-value aggregate metadata, never raw values;
- groups exact fits by `surface + role + encoding`;
- marks same-role recurrence only when at least two distinct records fit;
- keeps semantic and geometry binding explicitly `false` even if codec recurrence is found.

A recurrent exact fit can promote only the **codec binding** question. Semantic promotion still requires independent controlled evidence.

## False-positive guardrail

The protocol records the number of eligible fixed opportunities and a nominal uniform-32-bit-prefix union bound. This is only a search-budget guardrail; it is not asserted to model the real serializer and does not assume trial independence.

Because shape filtering removes BE-f64 for these roles, the real-target protocol has one eligible width per fixed opportunity rather than two.

## Validation

Synthetic test: `test_csmc_p4_counted_be_binding_probe_synthetic.py`

Validated behavior:

- BE-f64 shape exclusion for 48/49-qword records and all fixed subroles;
- expected BE-f32 counts `95/97/41/13/3`;
- exact count-3 BE-f32 decoding for a synthetic 16-byte q25–26 island;
- recurrence requires two distinct records at the same role;
- semantic/geometry gates remain closed;
- post-hoc window search remains disabled.

Local synthetic result before commit: `PASS`.

## Current execution ceiling

The exact authorized `.clip` / `.csmc` raw inputs used by the earlier P4 analysis are not embedded in the durable report bundles and are not present in the current execution container. The existing private runtime diagnostic ZIPs also intentionally contain no payload bytes.

Therefore this checkpoint does **not** claim a real-target counted-BE hit or miss. It converts the remaining test into a deterministic one-command check for the next authorized raw-input availability, without requiring MODELER, Worker mutation, V4.4, or a new runtime experiment.

## Next decision

When the same authorized raw pair is available, run the fixed-role probe using the already durable lattice JSON. Then:

- `0` recurrent roles → counted-BE does not bind these four independently bounded +965 roles; move to the next independently justified codec/owner hypothesis without widening windows post-hoc.
- `>=1` recurrent role → candidate `CONFIRMED_CODEC_BINDING` review under the Companion C BindingEvidence contract; do **not** infer vertex/index/bone/transform semantics from codec recurrence alone.
