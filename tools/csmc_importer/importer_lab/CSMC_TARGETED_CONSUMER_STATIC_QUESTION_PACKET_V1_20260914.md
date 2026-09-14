# CSMC Targeted Consumer Static Question Packet v1

Status: `PREREGISTERED_QUESTION_PACKET_NOT_PROOF`

This packet converts the already-verified Importer Lab / F02 structural results into **bounded consumer-static questions**. It does **not** add a new importer hypothesis family and does not claim a consumer proof edge.

## Source state

- M1 acceptance v2: **20/20 PASS** — Supabase row 187
- private GEN0 `LOCAL_BOUNDED_STRIDE_PERIODICITY`: **32 tested / 0 cross-fixture survivors** — row 191
- F02 30-mutation structural map: 5 discrimination questions, physical oracle still **0/30** — row 190
- Companion structural-contrast preregistration: row 186, Sentinel-9 order preserved
- Static evidence validator v2: row 182, new proof-grade consumer edges = 0
- public `.clip` architecture prior: row 184, `STRONG_PUBLIC_ARCHITECTURE_PRIOR_NOT_CSMC_PROOF`

## Blind-stage firewall

The next static pass must remain blind to semantic-looking public names.

Forbidden for target selection:
- public `.clip` table/column/class names
- semantic guesses such as geometry/material/index/UV/rig/weight
- oracle outcomes that do not yet exist

Required evidence for a proof-grade field-read candidate:
- direct input-read primitive
- bound function / instruction address
- read width
- endianness
- count or length source
- destination
- upstream/downstream data-flow summary
- negative control
- provenance hash

Admission contract: `CSMC_MODELER_STATIC_EVIDENCE_SLICE_CONTRACT_V2`.

## Five bounded discrimination questions

### Q-BND-01 — boundary transition
Payload-relative offsets: `3215 / 3216 / 3217`

Question: does one direct consumer read/data-flow cross, terminate at, or change behavior at the variable→invariant boundary?

### Q-BND-02 — boundary locality
Payload-relative offsets: `3200, 3208, 3215, 3216, 3217, 3224, 3232`

Question: is this neighborhood consumed by one bounded loop/read span, or partitioned into multiple scopes?

### Q-INV-01 — invariant-core partition
Payload-relative offsets: `3728, 7312, 11408, 15216`

Question: do separated invariant-core positions flow through the same direct consumer loop/destination, or distinct substructure consumers?

### Q-PFX-01 — variable-prefix partition
Payload-relative offsets: `8, 64, 128, 256, 512, 1024, 1536, 2048, 2560, 3072`

Question: is the variable prefix consumed uniformly by one direct read path, or partitioned into local subranges?

### Q-TERM-01 — logical end vs framing remainder
Payload-relative offsets: `17687..17695`

Question: does the consumer distinguish the alignment-extension byte at `17687` from the framing remainder beginning at `17688`?

## Post-blind corroboration gate

Only **after a blind result is sealed** may the public `.clip` architecture prior be compared against it. That prior remains non-proof corroboration and cannot upgrade any CSMC claim without a direct CSMC consumer edge.

## Hard guards

- broad static hypothesis expansion = false
- semantic promotion = 0
- Blender emit = blocked
- runtime dispatch = false
- MODELER execution = 0
- Save / Ctrl+S / serialization trigger = 0
- Worker / Canary / Control Gate actions = 0
- RIO-26 mutation = 0
- raw private CSMC bytes published = false

## Resume rule

A new proof run is authorized only when an **instruction-level private static slice/package** or another concrete direct consumer edge becomes available. This packet by itself is **not evidence**.

Machine-readable JSON SHA-256: `6bc38a6189b6ca3035fb03d3beff473daf5444a6a6c6c246fd406c2f4c55c646`
