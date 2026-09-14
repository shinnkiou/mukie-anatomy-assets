# SPDX-License-Identifier: MIT
"""Stable-channel build entrypoint for AI3D Structure Worker v0.2.4 CANARY-005."""
from __future__ import annotations

import ai3d_structure_worker_v024 as impl

WORKER_VERSION = impl.WORKER_VERSION
ALLOWED_ACTIONS = impl.ALLOWED_ACTIONS

if __name__ == "__main__":
    raise SystemExit(impl.core.main())
