"""Operational policy overlay for the fixed CSMC self-update bootstrap.

The immutable bootstrap must preserve the original Scheduled Task semantics:
after confirming that `current` already equals the promoted release, it runs one
normal canary poll/claim/execute cycle. `heartbeat-only` is reserved for the
post-swap health gate and rollback validation, so a self-update bootstrap never
turns the canary task into a heartbeat-only task.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from . import csmc_self_update as base
except ImportError:
    import csmc_self_update as base


def _run_current_cycle(root: Path) -> dict[str, Any]:
    current = root / base.CURRENT_NAME
    if not (current / base.WORKER_EXE).is_file():
        return {"status": "NO_CURRENT_WORKER"}
    return {"status": "ONCE", "result": base._run_worker(current, "once", timeout=180)}


# Patch exactly one scheduling policy in the base implementation. All update,
# verification, fixed endpoint/root, and rollback logic remains in the audited
# base module.
base._run_current_cycle = _run_current_cycle

CsmcSelfUpdateError = base.CsmcSelfUpdateError
run_cycle = base.run_cycle
self_test = base.self_test
BOOTSTRAP_VERSION = base.BOOTSTRAP_VERSION
FIXED_RELEASE_ENDPOINT = base.FIXED_RELEASE_ENDPOINT
