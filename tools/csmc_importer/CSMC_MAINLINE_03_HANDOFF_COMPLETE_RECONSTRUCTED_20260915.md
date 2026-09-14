# CSMC MAINLINE 03 — COMPLETE HISTORICAL HANDOFF / RECONSTRUCTION — 2026-09-15

Status: `HISTORICAL_RECONSTRUCTION_VERIFIED__MAINLINE03__DO_NOT_SUPERSEDE_MAINLINE04`

This file reconstructs the final durable state of CSMC Mainline03 from GitHub, Google Drive, Base44, Supabase, Linear, Gmail, and Google Calendar records. It is a restart/handoff artifact for Mainline03 only. It does not replace or roll back the later Mainline04 canonical state.

## 0. Canonical boundary

Mainline03 has two distinct end markers and they must not be conflated.

### Mainline03 code endpoint
- Repository: `shinnkiou/mukie-anatomy-assets`
- Historical importer branch: `csmc-importer-experimental-20260902`
- Final Mainline03 importer code HEAD: `7f7632d1894c36d5a9802b19f7150b820a6b4601`
- Commit message: `CI: guard non-semantic Lab candidate intake`
- Endpoint chain:
  - `a2b4ed8a0b81974a9d5a32f50f298b7cbce39fed` — fail-closed Lab candidate intake implementation
  - `77fc9444b057d7e9e3a9de52613ef9c1fcbfda80` — candidate intake tests
  - `7f7632d1894c36d5a9802b19f7150b820a6b4601` — CI guard
- Importer smoke: `34850710246` = SUCCESS
- Candidate-intake CI: `34850726415` = SUCCESS

### Mainline03 external/cross-store endpoint
After the importer code endpoint stayed fixed at `7f7632d...`, an independent MODELER static snapshot produced two proof-grade architecture edges. The cross-store pointer advanced without changing importer code:
- Supabase row `207` — `CSMC_MODELER_FULL_SNAPSHOT_RECONCILIATION_V1_20260914`
- Supabase row `208` — `CSMC_IMPORTER_LAB_FINAL_CURRENT_CHECKPOINT_V11_EXTERNAL_20260914`
- Base44 V11 mirror: `6aa800e15ce2b9befd257127`
- Drive V11 Markdown: `1gvwwhssPqWfjRKxZitjQNdVxrW23pBfs`
- Drive V11 JSON: `1H_MWImhZoqiJQ3ZB-J4QHQBGApZNbFt2`
- Static branch head: `fa3c3a7af57342eee9178cd78a65c11a83f8c471`
- Static CI: `34853787912` = SUCCESS

Therefore:
- `MAINLINE03_CODE_END = 7f7632d...`
- `MAINLINE03_EXTERNAL_END = Supabase row208 / V11`

### First definite post-Mainline03 transition
Do not import these back into Mainline03:
- Supabase row `209` — Companion C-069 independent deep pass; boundary-adjacent cross-lane evidence, not Mainline03 canonical.
- GitHub `f7e2e69d52fa39e5eaa6074611ec4688d9773a7b`
- Supabase row `210` — consumer-constrained phase, 50 synthetic proposals -> 43 unique survivors
- Supabase row `211` — V12 pointer
- Supabase row `212` — Mainline04 complete handoff

`f7e2e69d` / row210 is the first definite Mainline04-transition implementation and must not be back-projected into Mainline03.

## 1. Final Mainline03 state

At row208/V11:
- pipeline: `STRUCTURAL_ONLY`
- mainline_state: `ACTIVE`
- structural_development: `ACTIVE`
- semantic_gate: `CLOSED`
- semantic_promotion_count: `0`
- geometry: `UNRESOLVED`
- index_topology: `UNRESOLVED`
- Blender production emit: `BLOCKED`
- runtime_dispatch: `false`
- physical F02 oracle: `0/30 PENDING_MANUAL_ORACLE`
- broad blind semantic expansion: `BLOCKED`
- oracle-independent importer/structural work: `AUTHORIZED`
- `EXPLICIT_SERIALIZER_FIELD_READ`: `UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`: `UNRESOLVED`
- frozen F02 questions resolved: `0`

New at the external endpoint:
- `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP`: CONFIRMED proof-grade architecture edge
- `EXPLICIT_MODELDATA_LOOKUP`: CONFIRMED proof-grade architecture edge
- `EXPLICIT_CANVAS3D_LOAD_ENTRY`: CANDIDATE
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION`: CANDIDATE

These are architecture/consumer-path facts only. They do not identify geometry/index/material/UV/bone/weight semantics.

## 2. Mainline03 progression ledger

### M0/M1 infrastructure
Supabase row `166` — `CSMC_IMPORTER_LAB_M0_M1_ACCEPTANCE_20260914`
- synthetic M0/M1 acceptance PASS
- semantic promotion 0

Supabase row `187` — `CSMC_IMPORTER_LAB_M1_ACCEPTANCE_V2_20260914`
- 20/20 PASS
- bounded private GEN0 eligible
- no semantic promotion
- physical oracle still 0/30

### GEN0 bounded falsification
Supabase row `167` — Phase7 `LOCAL_INDEX_RANGE_BLOCK`
- 48 candidates; 0 hard pass / 48 hard fail
- rejects only the preregistered raw contiguous u16/u32 BE/LE reference-domain family in tested windows
- does not prove index absence

Supabase row `168` — Phase8 `LOCAL_COUNT_TO_ANCHOR_EXTENT`
- one train-only hit, zero validation hits, zero recurrent/common format
- frozen family rejected only

Supabase row `170` — Phase9 `LOCAL_LENGTH_CHAIN`
- zero TRAIN hits, zero VALIDATION hits
- frozen family rejected only

Supabase row `171` — static GEN0 frontier pause
- paused after three consecutive bounded generations without validation-frontier improvement
- resource-allocation pause, not a global semantic conclusion

### Residual localization / targeted resume
Supabase row `172` — render-part residual localization
- exact triple-common block: 7392 B / 924 qwords
- pre-common shifts: +88 B, +184 B, F07-F06 +96 B
- shared post-common growth: 2456 + 11 B
- `TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE`
- Level-4 refined candidate, not promoted
- direct boundary-relative raw scalar family rejected in preregistered scope

Supabase row `173` — `SIMPLE_96B_SINGLE_INSERTION_BEFORE_COMMON_BLOCK`
- full pre-common hits 0
- trailing preregistered scope hits 0
- simple literal one-span 96 B insertion model rejected
- return to pause

Supabase row `174` — Companion C-064 reconciliation
- residual localization independently reconciled
- no semantic promotion
- serializer read and fixture-to-consumer match unresolved

### F02 mutation oracle
Supabase row `169` — read-only mutation-oracle intake contract
Supabase row `176` — raw-manifest-SHA provenance hardening
Supabase row `180` — operator/intake V2
- 30 expected observations
- 0 acquired observations
- sentinel9: `M01 -> M10 -> M13 -> M14 -> M15 -> M18 -> M22 -> M23 -> M30`
- Save / Save As / Ctrl+S / serialization trigger forbidden
- visual change is not semantic proof

Supabase row `190` — offline 30-mutation structural map
- 30 preregistered mutations
- 5 discrimination questions
- predictions kept separate from observations
- physical observations remain 0/30

### Private GEN0 bounded stride family
Supabase row `191` — `LOCAL_BOUNDED_STRIDE_PERIODICITY`
- candidate strides 1..32
- 32 generated / 32 deduped
- 0 cross-fixture survivors
- only final 1024 B before validated phase-7 invariant core tested
- no post-hoc widening authorized
- conclusion: seek consumer-side direct read/width/endian/count/destination evidence instead of another blind static family

### Targeted consumer-static preregistration
Supabase row `192` — `CSMC_TARGETED_CONSUMER_STATIC_QUESTION_PACKET_V1_20260914`
Five frozen bounded questions:
- `Q-BND-01` — boundary 3215/3216/3217
- `Q-BND-02` — locality 3200, 3208, 3215, 3216, 3217, 3224, 3232
- `Q-INV-01` — invariant partition 3728, 7312, 11408, 15216
- `Q-PFX-01` — prefix partition 8, 64, 128, 256, 512, 1024, 1536, 2048, 2560, 3072
- `Q-TERM-01` — logical end vs framing remainder 17687..17695

Proof admission required direct input-read primitive, function/instruction address, width, endianness, count/length source, destination, upstream/downstream data-flow summary, negative control, and provenance hash. This packet was preregistration, not proof.

### Public .clip prior
Supabase rows `184` and `193`:
- public `.clip` architecture prior only
- direct CSMC evidence = false
- public names post-blind only
- declaration/name/schema presence never proves a concrete CSMC field or semantic

Companion C-067/C-068 retained the quarantine and corrected source-independence accounting. Repository count is not an independent replication count.

### Noncanonical research branch
Supabase row `195`, GitHub `81e18a0470308604f9afbdacc29d10be08e799ff`:
- `research-lab-m1-20260914`
- NO MERGE
- NO CODE CHERRY-PICK
- no stale registry snapshot imported as authority
- governance ideas reference-only

## 3. Mainline03 progression-policy correction

Supabase row `203` — `CSMC_MAINLINE_PROGRESSION_POLICY_CORRECTION_V1_20260914`

GitHub chain:
- `e74e9d181a6e0d41d5cbcf943b5ca46223c7b60e`
- `7c777bea9cf51cbae8547847b8599e58d39138e0`
- `7e7aab503da42d88dba3e8b188d3c64809407e74`

Canonical interpretation: `PHYSICAL_ORACLE_PENDING` and unresolved serializer-field proof are semantic-promotion gates, not a global mainline pause.

Authorized while semantic gate is closed:
1. strengthen importer intake / Structural IR bridges
2. fail-closed validation and regression
3. admit non-semantic Structural Facts
4. admit Lab `STRUCTURAL_CANDIDATE` / `CODEC_CANDIDATE`
5. prepare proof-grade evidence packet schemas
6. prepare/validate controlled-fixture-to-consumer admission
7. prepare direct MODELER static evidence admission
8. prepare same-identity fixture provenance
9. candidate -> discriminating-question handoff
10. strengthen importer CI/smoke guards

Blocked:
- semantic CONFIRMED claims for geometry/index/UV/material/bone/weight
- Blender production emit
- visual result or Lab score as semantic proof
- blind Phase10-style expansion
- reopening rejected families without genuinely new independent evidence
- inference/fabrication of unobserved oracle values

Local blocking rule: only the task needing unavailable semantic evidence becomes `BLOCKED_BY_EVIDENCE`; the rest of the structural mainline stays ACTIVE.

## 4. Fail-closed Lab candidate intake

Supabase row `205` — `CSMC_MAINLINE_LAB_CANDIDATE_INTAKE_V1_20260914`

GitHub:
- implementation `a2b4ed8a0b81974a9d5a32f50f298b7cbce39fed`
- tests `77fc9444b057d7e9e3a9de52613ef9c1fcbfda80`
- workflow / Mainline03 code endpoint `7f7632d1894c36d5a9802b19f7150b820a6b4601`

Only accepted candidate kinds:
- `STRUCTURAL_CANDIDATE`
- `CODEC_CANDIDATE`

Admission: `ADMITTED_NON_SEMANTIC_REFERENCE_ONLY`.

Fail-closed conditions:
- source SHA-256 required
- raw/private bytes forbidden
- semantic claim fields forbidden
- semantic promotion false
- Blender emit false
- runtime dispatch false
- independent evidence required before semantic promotion

Supabase row `206` / V10 made this the external current state before the later static snapshot.

## 5. Full MODELER static snapshot at 03 external end

Supabase row `207` — `CSMC_MODELER_FULL_SNAPSHOT_RECONCILIATION_V1_20260914`

Identity:
- MODELER executable SHA-256: `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`
- snapshot ZIP SHA-256: `afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342`
- snapshot files: 196
- uncompressed bytes: 79,493,525
- static head: `fa3c3a7af57342eee9178cd78a65c11a83f8c471`
- static CI: `34853787912` SUCCESS

Confirmed architecture edges:
- `EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP`
- `EXPLICIT_MODELDATA_LOOKUP`

Candidate edges:
- `EXPLICIT_CANVAS3D_LOAD_ENTRY`
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION`

Still unresolved:
- `EXPLICIT_CSMC_HANDLER_ENTRY`
- `EXPLICIT_SERIALIZER_FIELD_READ`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`
- all geometry/index semantic binding

Supabase row `208` / V11 incorporated these two confirmed edges while keeping importer code HEAD at `7f7632d...`. This is the final reconstructed Mainline03 external state.

## 6. Durable store references

### GitHub
Historical importer branch: `csmc-importer-experimental-20260902`
Mainline03 code endpoint: `7f7632d1894c36d5a9802b19f7150b820a6b4601`
Static branch: `csmc-modeler-static-analysis-second-pass-20260914`
Static head at 03 external end: `fa3c3a7af57342eee9178cd78a65c11a83f8c471`
F02 oracle branch: `csmc-f02-mutation-oracle-intake-20260914`
F02 oracle head: `5db89bc6f0ca20dcb2646b89202ead6b8b53bde2`

### Google Drive
- V5 external checkpoint: `1USvkoZ5NZB1mWivZAXncSyFxOvkSN9Zx`, SHA-256 `5915c066e8d7d8e3fc991a59afa6ad0a1949453a214e6103a3c32fabd713503d`
- V10 Markdown: `1kC-D2snh31MHtcHSS8GGbMN6GY2Iv3y9`
- V10 JSON: `14xlmtYc2vWkjzLLFPPJEG-iwORe1k7V6`
- V11 Markdown: `1gvwwhssPqWfjRKxZitjQNdVxrW23pBfs`
- V11 JSON: `1H_MWImhZoqiJQ3ZB-J4QHQBGApZNbFt2`
- row207 static report MD: `1jwWlqYq7rM8D099oKn7oCvckoGgub-6J`
- row207 static report JSON: `1EGJQjfNhc-J363K0vMl5K1B4DcUNUneC`

### Base44
App `6aa2743da37b11162682c01f`, entity `ExperimentLineage`.
Key records:
- row169 oracle contract: `6aa7b7acf722c811b4a51c6e`
- row176 oracle hardening: `6aa7bcb72c955663a751d4c5`
- row180 oracle V2: `6aa7c076c821ffa9af341c73`
- row182 static validator v2: `6aa7c2c8d0cc0260a748c376`
- row192 targeted consumer-static packet: `6aa7d308c1f846e65496e5a0`
- row193 public prior v2: `6aa7d359bef741b499ea1752`
- row194 V5: `6aa7d4324c6c68668f8d9d2d`
- row195 noncanonical review: `6aa7e98eb552f875596b7e29`
- row203 policy correction: `6aa7f8735ff59ba73150aa72`
- row204 V9: `6aa7f8f959098c8303dc4ce5`
- row205 Lab intake: `6aa7f9de7224b4a5a858fa92`
- row206 V10: `6aa7fa3e547973b0d4a2de75`
- row207 static snapshot: `6aa8008228ae511fe5eca5ea`
- row208 V11: `6aa800e15ce2b9befd257127`

### Supabase
Project: `vbuokbwglauibabinaqs`
Table: `public.bp3d_csmc_runtime_runs`
- rows 166–208 contain the relevant final Mainline03 history
- row208 is final Mainline03 external pointer
- row210 begins definite consumer-constrained Mainline04 transition

### Linear
Relevant issues, without state mutation from this historical reconstruction:
- RIO-58 — Importer Hypothesis Lab / mainline structural research
- RIO-56 — MODELER static second pass
- RIO-59 — F02 30-variant read-only physical oracle
- RIO-48 — Companion C
- RIO-26 — runtime adapter; do not mutate as a consequence of this handoff

## 7. Gmail / Calendar audit

A bounded Gmail recheck for 2026-09-13 through 2026-09-15 using CSMC/MODELER terms found historical GitHub CI failure notifications, Linear notifications, and earlier scheduled CSMC reports. None is admitted as new proof-grade Mainline03 evidence. CI truth comes from later successful GitHub runs and durable ledger records, not superseded failure notifications.

A bounded Google Calendar search for CSMC and MODELER over 2026-09-13 through 2026-09-16 returned no matching events. Calendar contributes no Mainline03 evidence or scheduling constraint.

## 8. Rejected / closed families that must not be silently reopened

Closed only in their frozen scopes:
- Phase7 raw contiguous u16/u32 BE/LE reference-domain family
- Phase8 local count-to-anchor extent
- Phase9 local length chain
- simple literal 96-byte single insertion before common block
- local bounded byte-equality stride periodicity 1..32 in frozen pre-core window
- direct shared boundary-relative raw scalar family in preregistered residual-localization window

A rejection is not proof that geometry/index/count/length/etc. do not exist elsewhere or in transformed/indirect forms.

## 9. Mainline03 restart rule

If intentionally resuming historical 03 for analysis/comparison:
1. Start from code endpoint `7f7632d...`.
2. Overlay row207/208 external facts only as evidence; do not change historical code identity.
3. Keep `STRUCTURAL_ONLY` and semantic promotion 0.
4. Keep geometry/index unresolved.
5. Keep F02 physical oracle at 0/30 unless direct observations are actually acquired.
6. Keep public `.clip` names post-blind/non-proof.
7. Do not merge `research-lab-m1-20260914`.
8. Do not re-open bounded rejected families without genuinely new independent evidence.
9. Do not import row210+ Mainline04 consumer-constrained machinery into historical Mainline03.
10. Do not perform MODELER Save/Ctrl+S/serialization trigger/hook/injection/patch as part of this reconstruction.
11. Do not authorize Blender production emit or runtime dispatch.

The highest-value unresolved 03 target was:
`known consumer architecture -> explicit serializer field read -> width/endian/count-or-length -> destination/internal construction -> controlled fixture to consumer match`

Mainline04 later made this chain more mechanically fail-closed, but those later gates are not retroactive Mainline03 facts.

## 10. Historical interpretation

Mainline03 is the generation where the project stopped treating more blind byte-pattern hypotheses as the primary path and shifted toward proof-admitted consumer-side evidence.

Its key accomplishments were bounded falsification of several narrow static families, prevention of post-hoc widening, separation of semantic gates from structural development, fail-closed non-semantic candidate intake, strict quarantine of public `.clip` priors, provenance-hardened F02 oracle intake with zero fabricated observations, and the first two proof-grade consumer architecture edges from the full static snapshot.

Its unresolved boundary at closure was not “which semantic field is geometry/index,” but how the confirmed architecture reaches one concrete serializer reader and then a bounded controlled-fixture field.

## 11. Successor boundary

For later work, consult the separate Mainline04 canonical handoff. This historical Mainline03 artifact must never supersede, downgrade, or overwrite current Mainline04 pointers.

Known transition:
`7f7632d (Mainline03 code end)`
`-> row207/208 external static evidence overlay`
`-> row209 boundary-adjacent Companion independent pass`
`-> f7e2e69d / row210 consumer-constrained transition`
`-> row211 V12`
`-> row212 Mainline04 complete handoff`

End of Mainline03 historical handoff.
