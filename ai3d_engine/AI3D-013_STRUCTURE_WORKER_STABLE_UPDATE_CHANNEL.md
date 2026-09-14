# AI3D-013 Structure Worker Stable Update Channel

## Purpose

Stop the version-specific `ZIP -> VERIFY -> INSTALL -> new Start Menu shortcut` loop seen in v0.2.0 through v0.2.3 while preserving the fail-closed physical CANARY boundary.

This change does **not** promote `ai3d_structure_module_v1`, does not run CANARY-004, and does not broaden cloud execution capabilities.

## User interaction after bootstrap

There is one final bootstrap install. After that, the user launches only:

`NEVER TEAR AI3D Structure Worker CANARY`

Normal worker revisions are fetched on the next launch of that same stable shortcut. The user no longer downloads/extracts/installs a new worker ZIP for every diagnostic revision.

## Trust boundary

The launcher hard-codes:

- repository: `shinnkiou/mukie-anatomy-assets`
- release tag: `ai3d-structure-worker-canary-channel`
- channel manifest asset: `AI3D_STRUCTURE_WORKER_CHANNEL_V1.json`
- worker asset: `NEVER_TEAR_AI3D_STRUCTURE_WORKER.exe`
- capability: `ai3d_structure_module_v1`

The manifest is data-only and cannot supply a URL, filesystem path, command, script, executable name, worker capability, timeout, or promotion decision.

Before a downloaded worker becomes current, the launcher requires:

1. fixed HTTPS GitHub release channel;
2. bounded byte size;
3. exact SHA-256 match;
4. packaged worker `--self-test` exit code 0;
5. self-test `status=PASS`;
6. exact worker version match;
7. exact sole allowlist `ai3d_structure_module_v1`;
8. `arbitrary_shell=false`.

Workers are installed side-by-side under the local Structure CANARY root. `current.json` is switched atomically only after all checks pass. An update-service/network failure does not replace or corrupt the previous verified worker.

## Separation from physical promotion

The stable launcher solves distribution only. It has no authority to:

- arm a CANARY;
- alter claim/lease rules;
- change the six-command Structure CANARY contract;
- promote `ai3d_structure_module_v1`;
- unblock AI3D-010;
- treat CI as physical evidence.

CANARY-004 still requires real Windows heartbeat -> isolated claim/lease -> real Blender -> durable provider SHA readback -> automated Structure QA -> visual QA before promotion.

## Expected lifecycle

1. Build/test worker and launcher on Windows CI.
2. Publish the verified worker + data-only channel manifest to the fixed prerelease tag.
3. Publish the one-time bootstrap ZIP.
4. User installs the stable launcher once.
5. Future worker fixes update the fixed release-channel assets after CI PASS.
6. On next stable-launcher start, the new worker is downloaded, SHA/self-test verified, then atomically activated.

No version-specific Start Menu shortcut is needed after bootstrap.
