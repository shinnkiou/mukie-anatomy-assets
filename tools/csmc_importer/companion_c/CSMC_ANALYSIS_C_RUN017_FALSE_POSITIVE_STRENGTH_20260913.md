# CSMC ANALYSIS COMPANION C — RUN C-017 — counted-BE recurrent-fit false-positive strength

Status: STATIC MATHEMATICAL GUARDRAIL PASS / NO TARGET BYTES / ZERO MODELER / ZERO RUNTIME

## QUESTION
Without target bytes, how much stronger is the C-014 requirement of two recurrent same-role counted-BE exact fits than a single exact fit under a conservative high-entropy null?

## PROBE
For a **fixed bounded region**, counted-BE exact-length decoding requires the first 32-bit big-endian count to equal the count implied by the region length. If both f32 and f64 widths are considered, at most two 32-bit count values can satisfy the same bounded size.

Conservative per-trial upper bound under a uniform 32-bit-prefix null:

`p <= 2 / 2^32 = 2^-31 ≈ 4.6566e-10`

For 22 same-role trials (matching the current +965 record-instance count), an independent-binomial order-of-magnitude model gives:
- at least one accidental exact fit: ~`1.02445e-8`;
- at least two accidental exact fits: ~`5.00901e-17`;
- at least three accidental exact fits: ~`1.55500e-25`.

The model deliberately does **not** use float-value plausibility, finiteness, range constraints, or cross-record value structure, so it is conservative relative to a stricter numeric validator.

## INTERPRETATION
The large strength jump from one to two recurrent exact fits supports C-014's decision to keep a single opaque-region fit at `CANDIDATE_CODEC_BINDING` and require recurrence for `CONFIRMED_CODEC_BINDING`.

This is not a probability claim about the real CELSYS serializer. Its data are structured and trials may not be independent. The calculation is a guardrail against accidental 32-bit count matches, not a format proof.

## NEW INFORMATION
- A single exact counted-BE fit is already rare under a uniform-prefix null, but it remains vulnerable to multiple-testing and serializer structure.
- Two same-role exact fits reduce the independent high-entropy null tail to about `5e-17` across 22 trials.
- Three same-role fits would reduce that null tail to about `1.6e-25`.
- C-014's recurrent-fit threshold is statistically well-motivated as a conservative promotion gate.

## CLOSED HYPOTHESES
- One and two exact fits provide roughly comparable accidental-match protection: REJECTED.
- Requiring recurrence has no quantitative benefit: REJECTED.
- This null calculation by itself proves a real codec binding: REJECTED.

## CONFIDENCE CHANGES
- two-fit recurrent-role threshold as a safe codec-binding guardrail: HIGH -> VERY HIGH.
- one-fit opaque-region promotion to CONFIRMED_CODEC_BINDING: LOW -> VERY LOW.
- current real counted-BE/+965 binding: remains NO_BINDING because no side-lane input bytes exist.

## NEXT QUESTION
Can the binding contract be strengthened further without target bytes by defining a **multiple-testing budget and scan protocol** (fixed roles/regions before decoding, no post-hoc window selection) so that future static scans do not inflate false-positive confidence?

## Guardrails
- Independence/uniformity assumptions are explicitly approximate.
- No target payload is read.
- No semantic slot is promoted.
