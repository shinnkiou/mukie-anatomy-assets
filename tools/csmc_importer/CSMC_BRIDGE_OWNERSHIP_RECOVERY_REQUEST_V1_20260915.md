# CSMC Bridge Ownership Recovery Request V1 — 2026-09-15

Classification: `READ_ONLY_STATIC_RECOVERY_REQUEST__NOT_PROOF`

## Goal
Recover the smallest admissible static slice needed to confirm, falsify, or keep unresolved the ownership/dispatch bridge behind `DQ-BRIDGE-LOADER-SER-01`.

This request intentionally precedes serializer width/endian/count work. It does not request MODELER runtime execution, Save/serialization, hooks, patches, F02 physical execution, semantic promotion, or Blender emit.

## Exact target identity
- Product/version: CLIP STUDIO MODELER 1.10.13
- executable SHA-256: `2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150`
- baseline Full Snapshot SHA-256: `afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342`

Any mismatch is fail-closed.

## Stage A — factory ownership first
Export read-only static evidence for:

1. `0x140d45d30` — C02 registration source, enough instruction/decompile context to preserve the `ModelData -> Canvas3DModelLoader` registration provenance.
2. `0x141657140` — immediate registration/helper edge.
3. `0x141656a80` — factory/creator helper root.

For `0x141656a80`, record all directly supported evidence for:
- creator/factory object stored or referenced;
- key/type/name input and destination registry/container;
- lookup/read path for the stored creator;
- construction/callable invocation path;
- direct, vtable, callback, or other provenance-bound indirect edge kind;
- exact source/target VA and instruction/basic block for each admitted edge;
- negative controls showing searched-but-absent paths.

Do not infer a runtime invocation from registration alone.

### Stage A decision
Return exactly one:
- `FACTORY_BRIDGE_RESOLVED`
- `FACTORY_BRIDGE_FALSIFIED_WITH_SCOPE`
- `FACTORY_BRIDGE_INCONCLUSIVE`

`RESOLVED` requires a provenance-bound chain from the C02 registration corridor to a concrete created/invoked loader object or method. Name/string proximity is insufficient.

## Stage B — vtable ownership in parallel
Export initialized pointer values, symbols/xrefs, and assignment sites for both exact intervals:

### PW3DModelDataLoader
- start `0x14195fad0`
- end exclusive `0x14195fb18`
- expected span 72 bytes
- expected 9 pointer-width slots

### PWCanvas3DModelLoader
- start `0x1417f6d30`
- end exclusive `0x1417f6d78`
- expected span 72 bytes
- expected 9 pointer-width slots

For every slot record:
- slot offset
- initialized raw pointer value
- resolved symbol/function VA if available
- xrefs to the slot/function
- constructor/destructor or object-init assignment xrefs
- confidence source (`INITIALIZED_MEMORY`, `RELOCATION`, `XREF`, `SYMBOL`, etc.)

No semantic meaning is assigned to a slot merely from position.

### Stage B decision
Return exactly one:
- `VTABLE_OWNERSHIP_RESOLVED`
- `VTABLE_OWNERSHIP_FALSIFIED_WITH_SCOPE`
- `VTABLE_OWNERSHIP_INCONCLUSIVE`

`RESOLVED` requires an object-construction/assignment provenance chain, not only RTTI/vtable labels.

## Conditional Stage C — only after A or B points to a concrete loader method
Only when Stage A/B supplies ownership provenance, export the specific reached method(s) and enough caller/callee context to test whether they connect toward the known candidate corridor.

Candidate corridor currently preserved only as a bounded lead:
`0x140e78810 -> 0x140e7c270 -> 0x140f5e510 -> 0x140f5ac20 -> 0x140f64600 -> 0x140f62d20 -> 0x140f650c0`

Do not assume this corridor belongs to C02.

Conditional functions `0x141658300` / `0x1416586f0` are exported only if Stage A/B resolution points to them. If resolution points to `0x141658300`, include its known direct caller wrapper `0x1416586c0` only as needed for provenance.

## Deferred until bridge admission
Do **not** decide yet:
- u16 vs u32
- little vs big endian
- count source
- sentinel vs length-bound loop
- geometry/index/material/UV/bone/weight meaning
- F02 field identity

H03/H04/H05/H06 direction/destination questions may be examined only after an owner/dispatch bridge exists. H09-H16 remain blocked until bridge admission.

## Output manifest minimum
- executable SHA-256
- extraction tool and version
- generated timestamp
- every exported file SHA-256
- function VA / edge kind / exact instruction
- both vtable interval dumps
- constructor/destructor assignment xrefs
- factory trace result
- negative-control search scope
- safety guards

## Safety guards
All must remain false:
- semantic promotion
- Blender emit
- runtime dispatch
- MODELER runtime started
- Save/Save As/Ctrl+S triggered
- hook or patch
- F02 runtime observation
- proprietary executable publication

## Admission semantics
Even if Stage A and Stage B are both `RESOLVED`, this request alone does not admit `EXPLICIT_SERIALIZER_FIELD_READ` or any ModelData field semantic.

The maximum immediate result is:
`BRIDGE_OWNERSHIP_STATIC_REVIEW_READY`

A separate evidence review must decide `DQ-BRIDGE-LOADER-SER-01` before width/endian/count work starts.
