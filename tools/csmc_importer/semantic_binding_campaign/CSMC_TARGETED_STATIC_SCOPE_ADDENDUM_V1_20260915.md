# CSMC Targeted Static Scope Addendum V1

Classification: `BOUNDED_PHASE_B_SCOPE_REFINEMENT_NOT_PROOF`

The existing Full Snapshot direct-call graph contains a narrow caller ancestry above the current `ModelData` reader candidate:

`0x140e78810 -> 0x140e7c270 -> 0x140f5e510 -> 0x140f5ac20 -> 0x140f64600 -> 0x140f62d20 -> 0x140f650c0`

Facts from the exported graph:
- `0x140f62d20` has one direct caller: `0x140f64600`.
- `0x140f64600` has one direct caller: `0x140f5ac20`.
- `0x140f5ac20` has one direct caller: `0x140f5e510`.
- `0x140f5e510` has one direct caller: `0x140e7c270`.
- `0x140e7c270` has an external caller `0x140e78810` plus a self-recursive edge.
- none of `0x140f5ac20`, `0x140f5e510`, `0x140e7c270`, `0x140e78810` is present in `targeted_decompile_index.tsv`.

This does not connect the chain to C02 and does not prove class ownership or serializer semantics. It is only a bounded Phase-B extraction order if the primary six-function request plus vtable/factory trace remains inconclusive.

Phase-B conditional order:
1. `0x140f5ac20`
2. `0x140f5e510`
3. `0x140e7c270`
4. `0x140e78810`

Additional conditional: only if factory/vtable resolution points to `0x141658300`, also decompile its sole exported direct caller wrapper `0x1416586c0`.

No proof gate changes:
- `DQ-BRIDGE-LOADER-SER-01 = WAIT_FOR_BRIDGE_PROOF`
- `DQ-SER-WIDTH-01 = WAIT_FOR_PROOF`
- semantic promotion = 0
- Blender emit = BLOCKED
- runtime dispatch = false
