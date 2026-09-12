# Modeler P4 private capture runbook — 2026-09-12

Status: `READY_FOR_FRESH_LIVE_MEM_PRIVATE_CAPTURE`

This runner is a narrow continuation after fresh P1/P2 file-route closure and the historical MEM_PRIVATE full-header validation.

## Gate

A runtime candidate is accepted only when all are true:

- process is CLIP STUDIO MODELER,
- memory region is committed/readable `MEM_PRIVATE`,
- full length-prefixed `CLIP_STUDIO_3D_DATA2` magic validates,
- kind is `character`,
- GUID exactly matches the authorized target,
- inner version is `2`,
- size fields are sane,
- `stored - align8(logical) == 8`.

The search itself plans only readable `MEM_PRIVATE` regions. A dump is performed automatically only when **exactly one** candidate passes the gate. If zero or multiple candidates pass, no raw dump is taken.

## Safety / privacy

- read-only process access (`ReadProcessMemory` only),
- no process modification/injection,
- no installation,
- no privilege escalation,
- no network upload,
- raw runtime BLOB remains local/private,
- never commit the resulting runtime BLOB/ZIP to public GitHub.

## User action

1. Keep `RUN_MODELER_P4_CAPTURE.cmd` and `BP3D_ModelerObserver_P4.ps1` together.
2. Open CLIP STUDIO MODELER and load the authorized female-160 drawing-doll model.
3. Double-click `RUN_MODELER_P4_CAPTURE.cmd`.
4. When the observer attaches, press `B` once.
5. After the result returns, press `Q` to package.
6. Attach the produced `CAPTURE_*_P4.zip` privately to the project chat.

After a fresh BLOB is recovered, compare it immediately against the saved CSMC with `runtime_blob_compare.py` / `csmc_p4_anchor_probe.py`. Use full-header/MEM_PRIVATE validation and structural anchor deltas; do not fall back to generic GUID hits.
