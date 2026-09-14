# CSMC targeted static extraction request V1

## Scope

One narrow read-only operation against CLIPStudioModeler.exe 1.10.13, SHA-256 2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150.

Purpose: close or falsify DQ-BRIDGE-LOADER-SER-01 before any ModelData width/endian/count claim.

## Required exports

1. Decompile and instruction listings for 0x140f62d20, 0x140f64600, 0x140f650c0, 0x140f622f0, 0x140f63200 and 0x140f635d0.
2. Dump initialized pointer values, symbols and xrefs for candidate slots:
   - PW3DModelDataLoader vftable 0x14195fad0 through before 0x14195fb18
   - PWCanvas3DModelLoader vftable 0x1417f6d30 through before 0x1417f6d78
3. Export constructor/destructor xrefs assigning either vftable.
4. Trace 0x141656a80 from stored creator/factory to concrete lookup, construction and virtual invocation.
5. Only if vtable/factory resolution points to them, decompile 0x141658300 and 0x1416586f0.

## Required evidence fields

- source and target VA
- edge kind
- exact basic block/instruction
- input stream argument
- read/write direction
- width and endian
- count source and loop bound
- allocation/resize/reserve
- destination object/type/field offset
- downstream builder
- negative control
- executable SHA and tool version

## Acceptance

A bridge must begin at C02 source 0x140d45d30 and terminate at a concrete reader with ownership provenance. String adjacency, shared helpers, compilation-unit proximity and unbound vtable candidates are insufficient.

## Safety

No MODELER launch, Save, runtime hook, F02 mutation execution, semantic promotion, or Blender emit. Return analysis exports only; do not publish the proprietary executable.