# SPDX-License-Identifier: MIT
"""CANARY-003 wrapper correcting QA gate semantics only."""
from __future__ import annotations
import builtins
import blender_structure_module_canary as base

base.RUN_ID = "AI3D-013-PHYSICAL-STRUCTURE-CANARY-003"
base.EVIDENCE_CLASS = "PHYSICAL_WINDOWS_BLENDER_STRUCTURE_CAPABILITY_CANARY_V3"


def _qa_gate_all(values):
    vals = list(values)
    # The reviewed base executor has eight positive QA predicates followed by
    # canary_promoted=False. Promotion safety must remain false and must not be
    # treated as a positive predicate.
    if len(vals) == 9 and vals[-1] is False:
        return builtins.all(vals[:-1])
    return builtins.all(vals)


base.all = _qa_gate_all

if __name__ == "__main__":
    base.main()
