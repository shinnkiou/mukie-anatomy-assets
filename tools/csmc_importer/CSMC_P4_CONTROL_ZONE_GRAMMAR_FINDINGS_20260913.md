# CSMC P4 control-zone equality grammar — 2026-09-13

Public-safe aggregate findings only. No purchased model bytes, payload qwords, texture bytes, or decoded private content are included here.

## Scope

This refines the already verified `+965` qword correspondence island containing 22 complete variable-length records (13 × 48 qwords, 9 × 49 qwords). The comparison asks only whether the aligned qword at a given relative record position is byte-identical across the two authorized serializations.

This is **structural correspondence**, not field semantics.

## Stable prefix and control zone

Across all 22 complete records:

- relative qwords `0..20` (168 bytes) are identical across the two serializations for every record;
- qwords `22` and `23` are rewritten for all 22 records;
- qwords `25` and `26` are preserved for all 22 records;
- qwords `21`, `24`, and `27` are conditional;
- qword `28` onward enters the previously documented rewritten tail until the next record boundary, where the 21-qword preserved prefix starts again.

Therefore the compact equality-control zone is qwords `21..27`.

## Equality signatures for qwords 21..27

Using `1 = exact across serializations` and `0 = different`, the observed signatures are:

| Record length | Signature | Count |
|---|---:|---:|
| 48 qwords | `0000110` | 7 |
| 48 qwords | `0001110` | 3 |
| 48 qwords | `0000111` | 3 |
| 49 qwords | `1000111` | 6 |
| 49 qwords | `0000111` | 3 |

The pattern `0000111` is deliberately shown in both classes: it is ambiguous in this sample and must not be promoted into a complete record-length decoder.

## One-way structural markers

Three conditional positions provide useful one-way rules on the observed sample:

- qword 21 preserved → 49-qword record
  - support 6
  - precision 6/6 = 1.0
  - recall 6/9 ≈ 0.667
- qword 24 preserved → 48-qword record
  - support 3
  - precision 3/3 = 1.0
  - recall 3/13 ≈ 0.231
- qword 27 rewritten → 48-qword record
  - support 10
  - precision 10/10 = 1.0
  - recall 10/13 ≈ 0.769

These are correspondence classifiers only. In particular, qword 27 **preserved** is not sufficient to identify a 49-qword record because three 48-qword records also preserve it.

## Negative result: no obvious one-bit length flag in the stable prefix

The 21-qword fully preserved prefix contains 1,344 individual bits per record. A simple exhaustive check found **no single bit position** whose 0/1 value perfectly separates the 13 short records from the 9 long records in this 22-record sample.

This is useful negative evidence against an overly simple "one preserved flag bit directly stores 48 vs 49" hypothesis. It does **not** prove that the stable prefix carries no length/class information; multi-bit or transformed relationships remain possible.

## Parser consequence

The safest current record grammar is:

1. preserved 21-qword prefix;
2. seven-qword mixed control zone (`21..27`);
3. rewritten tail beginning at qword 28;
4. exact preserved-prefix restart at the observed next boundary (48 or 49 qwords).

The control-zone mask can partially classify branch behavior, but the ambiguous `0000111` family means the current evidence does not justify deriving every record boundary from one control bit or signature alone.

## Guardrails

- No geometry/material/rig semantics are assigned to these positions.
- No encryption/compression/DRM conclusion follows from the equality mask.
- The observed one-way markers are empirical rules for this authorized target, not a claimed universal CELSYS format specification.
- A future parser should validate boundary restart and size/stride evidence instead of trusting a single marker.

## Public-safe tooling

`csmc_p4_control_zone_grammar_probe.py` reproduces this style of aggregate equality grammar from caller-supplied aligned payloads and record metadata. Its synthetic test contains no proprietary bytes.
