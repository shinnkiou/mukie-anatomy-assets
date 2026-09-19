# V1.6.3 design constraints

## Reused, not rediscovered

- body size 1,160,128 bytes
- 36,254 vertices
- stride 32
- Position float3 @0
- Normal float3 @12
- UV float2 @24
- fixed UV fingerprint
- V1.6.2 finite/sanity validator
- elbow pose plausibility window

## Newly collected

For validated uploads only:

- timestamp
- thread id
- data pointer
- VBO SHA-256
- phase
- upload API
- backtrace
- MODELER frame RVAs
- stack signature

## Completion gate

Prefer:
1. stack signature present in BASELINE + ELBOW_FLEX + RETURN;
2. otherwise MODELER RVA present in all three phases.

Do not send all observed frames to Ghidra.
Write only ranked candidates into `TARGET_RVAS.txt`.

## Explicit non-goals

- no MemoryAccessMonitor
- no broader source-pointer page watch
- no file-read tracing
- no SQLite/DATA2/CHNK rediscovery
- no ModelData string/XREF reopening
- no semantic promotion
