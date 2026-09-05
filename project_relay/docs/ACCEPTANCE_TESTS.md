# PROJECT RELAY acceptance / regression tests

This file converts real failures observed in the Blender/BP3D and DataScope workflows into permanent regression requirements.

## Execution safety

### RELAY-EXEC-001 Pipe buffer deadlock
A child that continuously writes large stdout and stderr streams must complete without blocking. Relay must drain both streams concurrently from process start and flush logs during execution.

### RELAY-EXEC-002 Exit-code false success
A process that exits `0` without required fresh success evidence must not become `SUCCESS`.

### RELAY-EXEC-003 Child crash / parent alive
If a child process disappears or writes a failure marker while the launcher remains alive, Relay must detect an incomplete/failed job rather than waiting forever on stale progress.

### RELAY-EXEC-004 Stale percent
A constant percentage is not enough to declare a stall if stage/detail/heartbeat/output activity continues to change.

### RELAY-EXEC-005 Process tree stop
SOFT/HARD/EMERGENCY stop must account for launcher + descendants; no orphaned Blender/Python/PowerShell process should remain after a hard stop.

### RELAY-EXEC-006 Deadline
At deadline, Relay stops starting new work, creates a stop request, preserves partial outputs/checkpoint, and records the stop result.

### RELAY-EXEC-007 Original protection
Where a job declares an immutable input SHA-256, any change to the original is a failure. Processing should use working copies.

## Result safety

### RELAY-RESULT-001 Stale result false success
A ZIP/result created before the current command started must never satisfy the current job's success condition.

### RELAY-RESULT-002 Result path without file
A textual result path is not evidence. The file must exist and pass expected size/entry/integrity checks.

### RELAY-RESULT-003 Transactional packaging
Build result package in temporary staging, validate, then move/rename to the final RESULTS location. Do not delete a known-good ZIP merely to regenerate the same path.

### RELAY-RESULT-004 Failure package tolerance
FAILED diagnostic packages must be best-effort and may omit normal success outputs. Failure packaging must not depend on the same strict conditions as success packaging.

## Discovery / preflight

### RELAY-PREFLIGHT-001 Launcher without worker
A launcher file existing is insufficient. All declared dependencies must exist before execute. This covers the observed `ONE_CLICK_RESEARCH.cmd -> RUN_COLLECTION.cmd` missing-worker failure.

### RELAY-PREFLIGHT-002 Bounded search
No unbounded recursive scan of Downloads/Documents/Desktop. Search configured roots in priority order and respect depth/time limits.

### RELAY-PREFLIGHT-003 Current version
A project should expose a known-good `CURRENT.json`/manifest. Old/failed/experimental versions must not be selected merely because they are newer by mtime.

### RELAY-PREFLIGHT-004 Path/encoding
Japanese paths, spaces, UTF-8/BOM inputs, and literal-path behavior must be covered by smoke tests. Internal IDs should remain ASCII even when display names are localized.

## Data quality

### RELAY-DQ-001 Coverage collapse
Technical success with an unexpected coverage drop (for example total known content 883 but research process sees 200) becomes `DATA_QUALITY_WARNING`, not ordinary success.

### RELAY-DQ-002 Unknown is not zero
Unknown/unobserved metrics must remain null/unknown and must never be silently replaced with measured zero.

### RELAY-DQ-003 Observation history
Changing follower/view/like values are observations with source + observed time; do not overwrite history into one assumed truth.

### RELAY-DQ-004 Dedup without destroying time series
Content identity and observation identity are separate. Parallel workers may deduplicate the same discovery while still preserving distinct valid time-series observations.

### RELAY-DQ-005 Source-role contamination
Artwork/media analysis must classify source role before feature extraction so avatars, UI, thumbnails, boilerplate, etc. cannot silently contaminate target-artwork statistics.

### RELAY-DQ-006 Prediction immutability
Prediction record/model version/input hash must be persisted before the outcome is known and never rewritten after the fact.

## Secrets / remote control

### RELAY-SEC-001 Secrets not exported
Logs/packages intended for ChatGPT/Discord/Drive must not contain API keys, bearer tokens, client secrets, passwords, credential files, or raw authorization headers.

### RELAY-SEC-002 No arbitrary remote shell
Remote commands reference an allowlisted `runner`. The command payload does not directly supply arbitrary shell/PowerShell source code.

### RELAY-SEC-003 Public repository isolation
No private artifact, credential, personal project file, or self-hosted Windows runner may be attached to this public staging repository.

## Initial implementation gates

Before adding Discord/Drive/Base44 transports, the local Core must prove:

1. one-click agent start;
2. command-id deduplication;
3. allowlisted execution;
4. concurrent stdout/stderr drain;
5. fresh success-marker/output verification;
6. per-job stop request;
7. deadline stop;
8. checkpoint/result/error state persistence;
9. agent heartbeat;
10. restart without re-running finalized command IDs.
