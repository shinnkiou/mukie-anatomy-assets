# CSMC Structural IR v0.1 — 2026-09-13

Status: PUBLIC-SAFE SEMANTICS-FREE INTERMEDIATE REPRESENTATION / SYNTHETIC VALIDATION PASS.

The current file-side evidence is now strong enough to formalize a structural intermediate representation without inventing model semantics.

## Why this IR exists

Two independent results now constrain the representation:

1. boundary behavior is not one universal class. `+197→+195` is a local complete-extinction transition, the ~4.69M boundaries are mixed-reuse/repack transitions, and the sparse `+195→+194→+195` pair is a temporary small-delta excursion;
2. the 22 complete `+965` records cannot be losslessly collapsed into a single record-class variable. `length_blocks` and q21..27 `preserve_signature` must remain independent axes.

Therefore the IR stores structural facts rather than prematurely naming geometry, transforms, materials, hierarchy, or other semantic record types.

## Validator contract

`csmc_structural_ir.py` enforces:

- schema version `csmc_structural_ir_v0_1`;
- source identity by lower-case SHA-256 only; raw payload bytes are not embedded;
- independent IR axes `length_blocks` and `preserve_signature`;
- boundary classes: `local_extinction`, `mixed_reuse_repack`, `sparse_delta_excursion`, `unknown`;
- every boundary semantic owner remains explicitly `unresolved`;
- every record-family semantic type remains `unresolved`;
- geometry/index/UV/material/texture/bone/weight claims all remain `unresolved`;
- public-safe guardrails reject raw/private fields and forbid a premature Blender-import claim.

Synthetic tests also prove that:
- a valid semantics-free document passes;
- collapsing both structural axes into a single `record_class` fails;
- assigning geometry semantics fails;
- inserting a literal qword field fails;
- the observed shared signature `0000111` can coexist with both 48- and 49-block records.

## Current public-safe example

`CSMC_STRUCTURAL_IR_V01_CURRENT_EXAMPLE_20260913.json` validates PASS and contains only hashes/aggregate structural facts. It represents:

- `BND_197_TO_195` as `local_extinction`;
- the two ~4.69M boundaries as `mixed_reuse_repack`;
- `BND_195_TO_194` and `BND_194_TO_195` as `sparse_delta_excursion`;
- the five observed `(length_blocks, preserve_signature)` structural families from the +965 sample.

This is not a decoded model format and is not a Blender importer. It is a lossless-enough public structural contract for carrying evidence forward without silently turning correlations into semantics.

NEXT: use the IR as the output boundary for future file-side probes. A later semantic promotion should require independent evidence and should change only the specific `unresolved` field supported by that evidence.
