# CSMC MAINLINE 04 — Focused Snapshot Recovery Audit — 2026-09-15

Status: `DURABILITY_ONLY__NO_SCIENTIFIC_ADMISSION__ROW223_UNCHANGED`

## Purpose
Resume Mainline-04 safely from Supabase row 223 without inventing analysis for an archive whose checksum is durable but whose ZIP body is not currently reachable through the connected stores.

This checkpoint is an audit/recovery artifact only. It does not supersede the canonical pointer, admit new static evidence, close any proof gate, or change semantic confidence.

## Canonical state retained
- current global pointer: Supabase row 223 — `CSMC_NEXT_CHAT_HANDOFF_20260915_0924_JST`
- pipeline: `STRUCTURAL_ONLY`
- semantic gate: `CLOSED`
- semantic promotion: `0`
- Blender production emit: `BLOCKED`
- runtime dispatch: `false`
- F02 physical oracle: `0/30 PENDING_MANUAL_ORACLE`
- `DQ-BRIDGE-LOADER-SER-01 = WAIT_FOR_BRIDGE_PROOF`
- `DQ-SER-WIDTH-01 = WAIT_FOR_PROOF`
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- `EXPLICIT_INTERNAL_MODEL_CONSTRUCTION = UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`

## Focused archive recovery result
Expected archive:
- filename: `CSMC_FULL_SNAPSHOT_FOCUSED_20260914_232435.zip`
- SHA-256: `b07a02ac3fd15198288588f15092c1bd94bbd17512e05353a712d0333a76d678`
- recorded size: `12,235,062 bytes`
- recorded file count: `244`
- prior status: `RECEIVED_CHECKSUM_VERIFIED_NOT_YET_SCIENTIFICALLY_ADMITTED`

Recovery checks performed read-only:
- Google Drive exact-name/content search
- Google Drive SHA search
- Google Drive parent-folder enumeration around the row223 handoff
- Google Drive application/zip search in that parent
- ChatGPT File Library exact-name / SHA / date-window navigation
- Base44 file/entity lookup
- GitHub code/commit lookup for a published focused-archive derivative
- File Library search for the required VAs, targeted decompile index, vtable labels, and factory trace terms

Result:
- checksum sidecars and handoff references are available;
- the focused ZIP body is not currently reachable through the connected stores;
- no complete per-function targeted extraction package or manifest-backed body was recovered;
- therefore the focused archive is **not scientifically admitted** in this session.

No attempt was made to reconstruct or fabricate missing function bodies from summaries.

## Intake validator audit
The existing targeted-static intake remains fail-closed. It requires exact executable/snapshot identities, six required function exports, both 9-slot vtable intervals, factory trace rooted at `0x141656a80`, conditional exports when triggered, and all safety guards disabled.

Passing intake means only `INTAKE_COMPLETE_STATIC_REVIEW_REQUIRED`.

Additional audit note: the validator checks manifest SHA syntax/identity but does not by itself recompute every referenced file hash from archive bytes. When an archive body becomes available, pre-intake verification should be:

`archive SHA recompute -> inventory -> member hash/readback verification -> intake validator -> separate bridge evidence review`.

## Recovered generation/toolchain context
The public-safe Data Scout helper pinned by the original automation was recovered at commit `281a663fd5b1ac7b0845bb9ba5ad3b8ba659efc9`.

The recovered `csmc_static_relevance_ranker.py` is a blind-safe post-ranker only. It consumes an existing `analysis_ranking.tsv`, contains no product-specific addresses/names/bytes, and explicitly sets `semantic_promotion=false`. It is not a snapshot/decompile generator and therefore cannot reconstruct the missing focused ZIP by itself.

The corresponding Data Scout run classified the current static toolchain as `CURRENT_TOOLCHAIN_SUFFICIENT`; the bottleneck was candidate-ranking noise rather than missing static-analysis capability. Existing Ghidra 12.1.3 / FLOSS / LIEF-pefile / SQLite / controlled-fixture tooling remains sufficient for the current proof gaps. No new external analysis tool is justified by the present evidence.

## Evidence-constrained hypothesis reduction
Existing durable evidence already rejects a direct-call bridge from C02/factory helpers to the candidate reader set in the exported graph. This is a negative control, not proof against indirect dispatch.

Therefore the next discriminator remains at the bridge/ownership layer:
1. **H02 / factory ownership** — trace `0x141656a80` from stored creator/factory through concrete lookup, construction, and invocation toward the candidate path.
2. **H01 / vtable ownership** — recover initialized slot values/xrefs and constructor/destructor assignments for `PW3DModelDataLoader` `0x14195fad0 .. <0x14195fb18` and `PWCanvas3DModelLoader` `0x1417f6d30 .. <0x1417f6d78`.
3. Only after a provenance-bound owner/dispatch bridge is established, adjudicate H03/H04 and H05/H06 (inbound vs outbound direction/destination).
4. Only after bridge admission, evaluate H09-H12 width/endian and H13-H16 count/loop hypotheses.
5. H07/H08 (`0x141658300` / `0x1416586f0`) remain conditional/deferred until factory/vtable resolution points to them.

Phase-B direct ancestry remains a bounded fallback, not proof:
`0x140e78810 -> 0x140e7c270 -> 0x140f5e510 -> 0x140f5ac20 -> 0x140f64600 -> 0x140f62d20 -> 0x140f650c0`.

## Scope firewall retained
C03 exact 16-byte container-field read and C04 CHNKSQLi decoded-length bounded stream copy remain container/database-scope constraints only. Neither may be reused as ModelData serializer width/endian/count evidence without the provenance bridge.

## Safe next action
Acquire or regenerate a private read-only targeted static extraction for the exact MODELER 1.10.13 executable SHA-256 `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`, prioritizing factory/vtable ownership evidence before reader width/count semantics.

No MODELER launch, Save/Save As/Ctrl+S, runtime hook/patch, Worker/Canary/Production/STABLE mutation, F02 physical execution, semantic promotion, or Blender production emit is authorized by this checkpoint.
