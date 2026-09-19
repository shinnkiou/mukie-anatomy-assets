# V1.6.2 validation design

## Why this revision exists

V1.6.1 produced a formally complete CHANGED snapshot, but the geometry delta was not plausible for a left-elbow-only movement:

- 35,933 / 36,254 position vertices changed
- selected max displacement was approximately 4.0e38

That is treated as an instrumentation/candidate-selection problem, not as useful body geometry evidence.

## Known body fingerprint

- upload size: 1,160,128 bytes
- vertex count: 36,254
- stride: 32 bytes
- Position: float3 @ 0
- Normal: float3 @ 12
- UV: float2 @ 24
- EBO/topology fixed across pose experiments
- UV fixed across pose experiments

## V1.6.2 candidate admission

A candidate must:

1. be exactly 1,160,128 bytes;
2. parse as 36,254 stride-32 records;
3. contain only finite Position/Normal/UV floats;
4. stay inside broad sanity bounds;
5. for CHANGED, have the same UV SHA-256 as BASELINE;
6. change 100..30,000 position vertices;
7. have max position displacement <= 10,000.

Repeated identical hashes are preferred over one-off candidates so that stable pose plateaus beat transition buffers.

## Writer watch

After a validated CHANGED candidate is chosen:

- choose up to 8 high-delta vertices from distinct 4 KiB pages;
- collect recent plausible source pointers;
- monitor only currently mapped pages;
- record operation, source instruction, MODELER RVA, symbol, watched pointer, and watched vertex.

If no write is captured after controlled rounds, the output still records pointer reuse and validated upload history so the next move can be WinDbg TTD / Stalker rather than another broad static scan.

## Anti-loop rule

Do not return to:

- SQLite rediscovery
- DATA2 envelope rediscovery
- ExternalChunk / CHNK broad scans
- broad string/XREF exploration
- generic ReadFile/winRead tracing

The active research line remains:

posed VBO -> source pointer -> writer -> transform palette -> bone index / weight
