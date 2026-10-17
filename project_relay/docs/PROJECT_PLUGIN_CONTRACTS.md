# PROJECT RELAY project-plugin contracts

All plugins use the same Core lifecycle and must not bypass Core safety checks.

## Common contract

Each plugin may provide:

- runner definitions (allowlisted executable/argv/cwd/environment)
- preflight rules
- progress/heartbeat adapters
- success/failure evidence adapters
- checkpoint/resume adapters
- artifact collectors
- optional data-quality validators

A plugin must never accept arbitrary shell source from a remote command payload.

## BP3D / Blender

### Known environment

Blender executable currently used by the project:

`C:\Users\nurun\AppData\Local\BlenderChatGPT\Runtime\blender-4.2.23-windows-x64\blender.exe`

This path belongs in local/private runner configuration, not public remote command messages.

### Production lineage to preserve

`v0.7.1 Clean Body -> v0.7.6 Connector/Pose SUCCESS -> v0.8.1 Visual Acceptance`

Do not select v0.7.0. Keep v0.8.0 as a known failed recovery reference.

### Core expectations

- pass input with `-InputPath`; avoid file picker
- monitor `percent + stage + detail + updated_at`
- monitor PowerShell/Blender process tree
- stdout and stderr are drained concurrently
- success requires marker + expected outputs + process result
- original `.blend` protection may require before/after SHA-256 equality
- worker should observe `PROJECT_RELAY_STOP_FILE`/project stop file where possible
- long candidate/pose jobs should expose checkpoint/resume index

### Primary future runner

`visual_acceptance_v081`

Runner config must be created locally after verifying the exact PowerShell script path and required markers.

## DataScope AI

### Core expectations

- strict dependency PREFLIGHT before launch
- a launcher file alone does not prove the collector exists
- use known-good CURRENT/manifest, not newest-mtime-only selection
- collector phases should checkpoint: DISCOVER / COLLECT / NORMALIZE / ANALYZE / PACKAGE / UPLOAD
- preserve stdout/stderr and current-run output identity
- do not treat an older `RESULTS_FOR_CHATGPT_*.zip` as current success

### Data-quality layer

Technical success is not enough. Validate where applicable:

- total known content vs processed content
- observation coverage
- duplicate rate
- null/unknown rate
- source role / evidence region
- large changes from prior run

Unknown is not zero. Metrics are observations with timestamp/source/confidence rather than destructive overwrites.

## Sakura Drum 77

### Primary v0.1 use

This is the safest first artifact-watch workload.

Watch for selected patterns such as:

- `PLAY_MEASURE_*.zip`
- `CHART_FEEL_DIFF_*.zip`
- `RHYTHM_SKETCH_*.zip`

### Pipeline

`DETECT -> ZIP VERIFY -> SHA256 -> BASIC STATS -> HISTORY -> MANIFEST -> REPORT`

Basic statistics should remain deterministic Python processing; ChatGPT performs interpretation.

The user remains responsible for actual drumming and subjective feel reports.

## LIFE ARCHIVE

LIFE ARCHIVE should not be used as the binary artifact store.

Relay should eventually send compact records such as:

- artifact_id
- job_id
- project
- file name
- SHA-256
- Drive reference
- status
- summary
- started/finished times
- resume point

Large ZIP/video/image assets remain in Drive/local storage.

Future operations:

- `REPORT_ARTIFACT`
- `REGISTER_JOB`
- `UPDATE_JOB`
- `CREATE_REPORT_CANDIDATE`
- `UPDATE_MISSION_PROGRESS`
- `WEB_QA`

## Transport order

Proposed rollout order:

1. local inbox transport (current bootstrap)
2. Google Drive/Sheets or another auditable queue
3. Discord notification/command bus
4. Base44/LIFE ARCHIVE job monitor
5. optional remote MCP/HTTP bridge after private-repo and authentication design

The Windows Core should continue operating locally even if an external transport is unavailable.
