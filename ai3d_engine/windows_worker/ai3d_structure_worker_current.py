# SPDX-License-Identifier: MIT
"""Stable build entrypoint for the current AI3D Structure Worker channel.

The user-facing launcher/updater is stable. This module is only the canonical
worker build target and may advance behind that launcher without requiring a
new manual ZIP install.
"""
from __future__ import annotations

import ai3d_structure_worker_v023 as impl

WORKER_VERSION = impl.WORKER_VERSION
ALLOWED_ACTIONS = impl.ALLOWED_ACTIONS

if __name__ == "__main__":
    raise SystemExit(impl.core.main())
