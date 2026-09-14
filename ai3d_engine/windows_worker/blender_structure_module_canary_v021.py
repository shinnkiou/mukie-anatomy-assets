# SPDX-License-Identifier: MIT
"""Bind the reviewed AI3D-013 Structure Blender executor to CANARY-002.

The geometry/QA implementation stays unchanged. Only the bounded run identity is
advanced so CANARY-001 remains immutable diagnostic history.
"""
from __future__ import annotations

import blender_structure_module_canary as base

base.RUN_ID = "AI3D-013-PHYSICAL-STRUCTURE-CANARY-002"

if __name__ == "__main__":
    base.main()
