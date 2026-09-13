# Companion C — Run C-042 — synthetic +965-like property suite

## QUESTION
Can the structural parser contract be stress-tested without proprietary bytes while failing closed on the known error classes?

## IMPLEMENTATION
Added `csmc_analysis_c_synthetic_property_suite.py`.

The corpus uses synthetic integers only. It models the five known joint structural families:
- 48 / `0000110`
- 48 / `0000111`
- 48 / `0001110`
- 49 / `0000111`
- 49 / `1000111`

Synthetic records enforce:
- q0..20 stable;
- q21..27 controlled by the seven-bit preserve signature;
- q22..23 rewritten;
- q25..26 preserved;
- q28+ rewritten;
- route remains `character`;
- owner and semantic state remain `UNRESOLVED`;
- scan protocol is preregistered/fixed, never post-hoc.

## SYNTHETIC TEST
10/10 PASS:
- all five joint families retained;
- family collapse detected;
- wrong record width/length rejected;
- wrong route rejected;
- invented owner rejected;
- false semantic promotion rejected;
- post-hoc window selection rejected;
- preserve-signature mismatch rejected;
- stable-prefix violation rejected;
- public-safe export contains no raw/private byte field.

## NEW INFORMATION
The core +965 structural grammar can now be regression-tested independently of CSMC payload possession. Structural hardening no longer requires repeating private-file experiments.

## CLOSED HYPOTHESES
- proprietary bytes are required to test family branching: REJECTED.
- parser tests may silently collapse the two axes `(length_blocks, preserve_signature)`: REJECTED.
- unresolved route/owner/semantics can default to guessed names in test fixtures: REJECTED.

## CONFIDENCE CHANGES
- synthetic structural regression coverage: HIGH -> VERY HIGH.
- semantic binding: unchanged.
- Blender mesh/scene emit: BLOCKED.
