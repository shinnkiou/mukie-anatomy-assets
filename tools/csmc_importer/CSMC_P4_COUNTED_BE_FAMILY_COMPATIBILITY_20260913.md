# CSMC P4 counted-BE family compatibility — 2026-09-13

Status: **PUBLIC-SAFE AGGREGATE STATIC PASS / ZERO MODELER ACTIONS / ZERO RUNTIME JOBS**

This pass combines two already-verified aggregate results without reading target payload bytes:

1. the +965 structural family partition across 22 complete records;
2. the entropy-based maximum number of records that could satisfy the predeclared counted-BE f32 fixed-role shape on each serialization surface.

It does not claim a codec binding. It asks only whether an **entire known structural family** could still be uniformly bound to counted-BE f32 at each fixed role.

## Structural families

| Family | Length | Preserve signature q21..q27 | Count |
|---|---:|---|---:|
| `F48_0000110` | 48 qwords | `0000110` | 7 |
| `F48_0000111` | 48 qwords | `0000111` | 3 |
| `F48_0001110` | 48 qwords | `0001110` | 3 |
| `F49_0000111` | 49 qwords | `0000111` | 3 |
| `F49_1000111` | 49 qwords | `1000111` | 6 |

Total = 22 records.

## Existing entropy ceilings

Maximum counted-BE f32 exact-fit rows compatible with observed qword byte entropy:

| Fixed role | Surface A | Surface B | Cross-surface family ceiling |
|---|---:|---:|---:|
| whole record start q0 | 7 | 7 | 7 |
| stable prefix start q0 | 7 | 7 | 7 |
| control-zone start q21 | 6 | 5 | **5** |
| preserved-island start q25 | 6 | 6 | **6** |

The predeclared exact-fit counts remain:
- whole 48-qword record: counted BE-f32 count 95
- whole 49-qword record: count 97
- 168-byte stable prefix: count 41
- 56-byte control zone: count 13
- 16-byte preserved island: count 3

BE-f64 was already shape-excluded for these roles.

## New family-level exclusions

### Control-zone role q21..27

A whole family can be uniformly counted-BE f32 across both surfaces only if its size is <= 5.

Therefore complete-family binding at this role is excluded for:

- `F48_0000110` — 7 records
- `F49_1000111` — 6 records

Only the three 3-record families remain size-compatible with uniform counted-BE f32 at the control-zone role.

There is a stronger structural consequence for `F49_1000111`: its first signature bit is `1`, so q21 is preserved in all six members of this family. Yet Surface B's entropy allows at most **five** counted-BE control-role fits. Therefore:

> `F49_1000111` cannot be a six-of-six universal counted-BE f32 control-zone family, even though q21 itself is preserved in all six records.

This separates **cross-serialization preservation** from **codec binding**: equality at a control position is not sufficient to establish counted-BE semantics.

### Preserved-island role q25..26

Cross-surface ceiling = 6.

Therefore only the 7-record family `F48_0000110` is excluded from being uniformly counted-BE f32 across the entire family at this role. The 6-record and 3-record families remain size-compatible.

### Whole-record and stable-prefix roles

Cross-surface ceiling = 7, so family size alone does not exclude any individual family. This is not positive evidence for a binding; it only means the aggregate entropy bound cannot reject an entire family at those two starts.

## Interpretation

The earlier result already rejected counted-BE f32 as a regime-global 22/22 codec. This pass narrows the surviving hypothesis further:

- at q21/control-zone start, any uniform family-level counted-BE binding is restricted to the 3-record families;
- the 6-record q21-preserved family is specifically ruled out as universally counted-BE at that role;
- at q25/island start, a 7-record universal family is ruled out;
- any surviving codec relation is therefore a minority/subfamily or mixed-role phenomenon, not a simple preservation-family identity.

No raw values, geometry semantics, owner names, vertex/index claims, codec confirmation, or Blender-import claim are made.

## Next use

If the authorized raw pair becomes available again, the fixed-role binding probe should test the already-predeclared roles only and report hits by structural family. The aggregate exclusions above are fail-closed cross-checks: a claimed result that violates these maxima is invalid.

Until then, continue public-safe static work on owner/parent edges and structural-family relations. V4.4/no-change Save remains inert.
