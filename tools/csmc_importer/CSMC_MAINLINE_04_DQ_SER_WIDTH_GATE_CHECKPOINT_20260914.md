# CSMC MAINLINE 04 — DQ-SER-WIDTH-01 FAIL-CLOSED INTAKE GATE CHECKPOINT

Date: 2026-09-14 JST
Role: mainline incremental structural checkpoint
Base canonical handoff: `CSMC_MAINLINE_04_HANDOFF_COMPLETE_20260914.md`
Base Supabase current pointer: row 212
Base importer pointer before this change: `43efa387e9ddf390bf5366e461155cdf1e2aef55`
Static lane head read back: `fa3c3a7af57342eee9178cd78a65c11a83f8c471`

## Purpose

Advance the mainline without guessing the answer to `DQ-SER-WIDTH-01`.

The current static corpus still does **not** prove whether the bounded consumer-side direct reader is 16-bit or 32-bit. `EXPLICIT_SERIALIZER_FIELD_READ` remains UNRESOLVED. The generic direct byte-read primitive `0x1408c27c0` is not sufficient to answer width/endian/count/destination for F02.

This checkpoint therefore adds a machine-checkable, fail-closed intake gate so that a future proof-grade static evidence slice can constrain Importer Lab candidates immediately without automatic semantic promotion.

## New mainline artifacts

- `tools/csmc_importer/importer_lab/CSMC_DQ_SER_WIDTH_GATE_V1.json`
- `tools/csmc_importer/importer_lab/csmc_serializer_field_read_gate.py`
- `tools/csmc_importer/importer_lab/test_csmc_serializer_field_read_gate.py`
- updated `.github/workflows/csmc-consumer-constrained-lab-smoke.yml`

Implementation commits:
- gate spec: `f348fa72218b809995b474066449e5a0f9ce9ecf`
- gate implementation: `b6f77bffe4f96ac0d842da74b743f12359050135`
- synthetic tests: `2ff173006aa4d2b613d3970afd53854854fcfeb7`
- CI wiring / tested code head: `e7cb837dce73a726d0e800b54940d5ba7d262f03`

## Gate semantics

The gate separates two claims that must never be conflated:

1. `DQ-SER-WIDTH-01` structural answer is available only when a MODELER static evidence slice is `EXPLICIT_SERIALIZER_FIELD_READ`, `CONFIRMED`, exact-binary-bound, direct-read/data-flow evidence, and contains explicit reader primitive, effective width, endianness, count/length source, destination, upstream/downstream flow, negative control, provenance hash, and all safety guards false.
2. F02 Importer Lab candidate pruning is allowed only when that decisive evidence is additionally explicitly bound to controlled fixture `F02` and field label `F02_DATA2_VARIABLE_PREFIX`.

Therefore:
- no evidence -> no pruning;
- incomplete evidence -> no pruning;
- CANDIDATE/STRONG-only evidence -> no hard width pruning;
- wrong MODELER binary identity -> no pruning;
- CONFIRMED width evidence without explicit F02 binding -> DQ may be structurally resolved, but F02 candidate population remains unchanged;
- only CONFIRMED + F02-bound evidence may reject width-contradicting candidates, and only inside `MODELDATA_CONSUMER_PATH`;
- unrelated record-family candidates remain untouched as negative controls.

This is a falsification constraint, not a winner bonus. `consumer_bonus=0`, `visual_score_delta=0`, `semantic_promotion=false`, `blender_emit=false`, `runtime_dispatch=false`.

## CI readback

GitHub Actions run `34858073131` = **SUCCESS** on tested code head `e7cb837dce73a726d0e800b54940d5ba7d262f03`.

Observed synthetic outputs:
- existing consumer-constrained population: `50 input / 43 unique survivor / 3 hard reject / 4 duplicate`;
- synthetic F02-bound 16-bit proof: `25 survivor`;
- synthetic F02-bound 32-bit proof: `27 survivor`;
- M1 acceptance v2: PASS.

The 25/27 counts are **only synthetic gate behavior tests**. They do not indicate that real CSMC uses 16-bit or 32-bit reads.

## Current proof state

Unchanged:
- `MAINLINE ACTIVE`
- `STRUCTURAL_ONLY`
- semantic gate CLOSED
- semantic promotion = 0
- geometry = UNRESOLVED
- index/topology = UNRESOLVED
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`
- F02 physical MODELER oracle = 0/30
- Blender emit = BLOCKED
- runtime dispatch = false
- MODELER Save / serialization trigger / hook / injection / patch = 0

The two existing proof-grade architecture edges remain the only CONFIRMED consumer constraints used by mainline:
- `ExternalChunk.Offset lookup @ 0x140d175d0`
- `ModelData -> Canvas3DModelLoader @ 0x140d45d30`

## Read-only external checks

Linear RIO-56 was read back and still reports `DQ-SER-WIDTH-01` as the highest-priority direct field-read discriminator with no newer proof slice.
Gmail was checked read-only; no new proof-grade MODELER/static evidence was found.
Google Calendar was checked for 2026-09-14 through 2026-09-16; no CSMC/MODELER event was found.
No email/calendar mutation was performed.

## Next action

Do not broaden static exploration from mainline.

Wait for a new validated MODELER static slice or other direct consumer proof. When one arrives:
1. validate against the existing static V2 contract;
2. pass it through `DQ-SER-WIDTH-01` gate;
3. if width is decisive but F02-unbound, record the structural result but do not prune F02;
4. if explicitly F02-bound, apply scope-aware width contradiction pruning to current consumer-constrained survivors;
5. then continue narrowly to endian -> count/bound source -> destination -> internal construction -> independent controlled-fixture-to-consumer validation.

No semantic promotion or Blender production emit is authorized by this checkpoint.
