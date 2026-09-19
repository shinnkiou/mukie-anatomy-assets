# CSMC P1 — VTABLE DISPATCH MAP

P1 ends the generic string-XREF lane and maps the two known loader vtables into a bounded virtual-dispatch call graph.

Run:

`00_RUN_P1_VTABLE_DISPATCH.bat`

Scope is fixed to:
- `PW3DModelDataLoader @ 0x14195fad0`, 9 slots
- `PWCanvas3DModelLoader @ 0x1417f6d30`, 9 slots
- one-time precheck `0x1400452b0`

Existing snapshot decompiles are reused. Only functions absent from `decompile_manifest.tsv` are decompiled by Ghidra.

See `GUIDE_JA.txt` for the operating procedure.
