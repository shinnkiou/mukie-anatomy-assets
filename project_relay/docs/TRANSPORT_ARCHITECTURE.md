# PROJECT RELAY transport architecture

PROJECT RELAY Core should not depend on one communication service. Commands/results move through replaceable transports.

## Layering

```text
User voice/text
    -> ChatGPT (reasoning / command compilation)
        -> transport adapter
            -> PROJECT RELAY Core
                -> project runner/plugin
            <- result/status adapter
        <- ChatGPT analysis
```

Core understands only normalized command/result records. Discord, Google Drive/Sheets, Base44, local files, and future MCP/HTTP bridges are transports, not business logic.

## Transport priority

### Phase 0: local inbox (implemented)

`runtime/queue/inbox/*.json`

Purpose: prove START / STOP / SAVE / RESUME without network dependence.

### Phase 1: auditable cloud queue

Preferred candidates:

- Google Sheets command/status table, or
- Base44 entity queue.

Desired fields:

`command_id, project, action, payload_ref, priority, status, created_at, started_at, finished_at, result_ref, error_ref`

The Windows agent polls/receives only normalized commands. Large payloads are stored separately.

### Phase 2: Discord control/notification bus

Discord is best used as a human-visible control room rather than a binary artifact store.

Suggested channels:

- `agent-command`
- `agent-human`
- `agent-running`
- `agent-results`
- `agent-errors`
- `agent-approval`
- `agent-system`

Bot/API integration is preferred over mouse-driving the Discord UI.

Discord messages should carry small command/status records and links/IDs to artifacts in Drive/local storage.

### Phase 3: Base44 / LIFE ARCHIVE dashboard

Expose job states:

- RUNNING
- PAUSED
- WAITING_APPROVAL
- FAILED
- DONE
- STOPPED

LIFE ARCHIVE receives compact job/artifact metadata, not huge ZIP/video/blob payloads.

### Phase 4: phone satellite

A spare Wi-Fi phone acts as an external monitor/control terminal:

- heartbeat visibility
- STOP/PAUSE/RESUME
- approval prompts
- push notifications
- camera fallback for external screen observation
- optional Wake-on-LAN

A physical phone remains useful even when Android emulators exist because it survives failures of the Windows host itself.

## Result routing

Small metadata/log summary:

`Relay -> transport -> ChatGPT/Base44/Discord`

Large artifact:

`Relay -> Drive/local artifact store -> transport sends artifact id/reference`

Code/version history:

`Relay/ChatGPT -> GitHub`

## GUI automation hierarchy

When a task needs UI interaction, choose the most deterministic method available:

1. direct API/connector
2. CLI or file interface
3. browser DOM automation
4. Windows UI Automation
5. clipboard
6. screenshot/vision + coordinates

Coordinate clicking is a last resort.

## Authentication / secret rules

- no OAuth tokens/API keys in command payloads
- no secrets in Discord messages
- no secrets in public GitHub
- credentials are local/private configuration only
- remote command transport cannot submit arbitrary shell source
- dangerous actions require explicit allowlisted runner/action and, where appropriate, approval state

## Offline behavior

Core should continue local execution if Discord/Base44/Drive are temporarily unreachable.

State and results are persisted locally first, then synchronized when transport returns.

This makes unattended work resilient to short network failures.
