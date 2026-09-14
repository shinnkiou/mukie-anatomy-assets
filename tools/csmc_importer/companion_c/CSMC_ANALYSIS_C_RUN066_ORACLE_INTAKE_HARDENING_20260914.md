# CSMC ANALYSIS COMPANION C — RUN C-066
## F02 oracle-intake provenance hardening reconciliation — 2026-09-14

### Trigger

After C-065, the F02 read-only mutation-oracle intake lane gained a new public-safe provenance hardening. This is genuinely new infrastructure evidence, but it is **not** a physical oracle result and **not** a serializer semantic binding.

Source lane:
- branch `csmc-f02-mutation-oracle-intake-20260914`
- head `c25750fc3d91d97ffa79de95f583914d1294ee9f`
- raw-hash-bound CLI commit `5de3567ec683441717b39c4ace885563e9951ef2`
- CI coverage commit `d9e7948330f7bf3932387b75b56713ee9eed358f`
- CI `34826886335`: SUCCESS
- source Supabase row 176
- source Base44 `6aa7bcb72c955663a751d4c5`

### New guarantee

The intake CLI reads the exact public source-manifest bytes, computes SHA-256 first, and rejects the input unless that raw digest equals the preregistered manifest digest:

`751f05dfff9d5308dfd96421d5bce43e6785de2cb385fb28a8c97c565c6cc891`

Only after this raw-byte provenance check does it parse JSON and apply the existing fail-closed 30-variant observation contract. The receipt binds the source-manifest raw hash, observation raw hash, and a canonical public-projection hash while remaining diagnostic-only with semantic promotion and Blender emit both false.

This closes a provenance gap: semantically equivalent JSON with different raw bytes can no longer silently substitute for the preregistered public manifest at CLI intake.

### Physical evidence status

The Drive observation sheet was reread during C-066. All M01–M30 remain `PENDING_MANUAL_ORACLE`; physical observations acquired remain **0/30**.

Therefore this run does not establish load sensitivity, visible effect, process survival, serializer reads, geometry/index/material/object semantics, or controlled fixture → consumer binding.

### Safety interpretation

The hardening does not authorize MODELER launch, mutation generation, Save/Save As/Ctrl+S, serialization triggers, runtime dispatch, Worker/Canary/STABLE/Control Gate actions, RIO-26 mutation, mainline mutation, semantic promotion, Blender emit, or raw/private publication.

Pipeline remains `STRUCTURAL_ONLY`.

### Next admissible evidence

Resume substantive interpretation only on:
- a validated read-only F02 oracle observation admitted through the hardened intake;
- proof-grade `EXPLICIT_SERIALIZER_FIELD_READ` / destination data-flow evidence; or
- another genuinely independent constraint axis.

No new numbered semantic-analysis run should be created merely from the hardened infrastructure until one of those evidence classes appears.
