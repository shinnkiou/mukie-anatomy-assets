#!/usr/bin/env python3
"""C-055: reconcile the historical C-053 promotion-firewall run-id collision.

This module does not rewrite Git history and does not change research semantics. It
re-exports the already fail-closed promotion firewall under the canonical C-055
index while preserving canonical C-053 (provenance continuity) and C-054
(evidence admission).
"""
from __future__ import annotations

from csmc_analysis_c_controlled_promotion_firewall_c053 import (
    _base,
    evaluate_promotion_firewall,
    self_test as historical_firewall_self_test,
)

RUN_ID = "C-055"
PIPELINE_STAGE = "STRUCTURAL_ONLY"
SEMANTIC_PROMOTION_COUNT = 0
BLENDER_EMIT_READY = False
RUNTIME_DISPATCH = False

CANONICAL_RUN_MAP = {
    "C-053": "C-051/C-052 provenance continuity gate",
    "C-054": "C-051 evidence-admission state machine",
    "C-055": "controlled-evidence promotion firewall / run-id collision reconciliation",
}

HISTORICAL_COLLISION = {
    "commit": "e5908eafb6e6377b8ae7a4be94084413a171f79a",
    "historical_run_id": "C-053",
    "canonical_run_id": "C-055",
    "history_rewritten": False,
    "logic_changed": False,
}


def reconciliation_record() -> dict:
    return {
        "accepted": True,
        "run_id": RUN_ID,
        "state": "RUN_ID_COLLISION_RECONCILED_NO_HISTORY_REWRITE",
        "canonical_run_map": dict(CANONICAL_RUN_MAP),
        "historical_collision": dict(HISTORICAL_COLLISION),
        "pipeline_stage": PIPELINE_STAGE,
        "semantic_promotion_count": SEMANTIC_PROMOTION_COUNT,
        "blender_emit_ready": BLENDER_EMIT_READY,
        "runtime_dispatch": RUNTIME_DISPATCH,
        "automatic_integration": False,
        "mainline_mutation": False,
        "rio26_mutation": False,
    }


def self_test() -> None:
    # Preserve the exact underlying 15-case fail-closed policy.
    historical_firewall_self_test()

    rec = reconciliation_record()
    assert rec["accepted"] is True
    assert rec["canonical_run_map"]["C-053"] == "C-051/C-052 provenance continuity gate"
    assert rec["canonical_run_map"]["C-054"] == "C-051 evidence-admission state machine"
    assert rec["historical_collision"]["canonical_run_id"] == "C-055"
    assert rec["historical_collision"]["history_rewritten"] is False

    current = evaluate_promotion_firewall(_base())
    assert current["accepted"] is True
    assert current["semantic_promotion_count"] == 0
    assert current["blender_emit_ready"] is False
    assert current["runtime_dispatch"] is False

    bad = _base()
    bad["candidate_as_confirmed"] = True
    rejected = evaluate_promotion_firewall(bad)
    assert rejected["accepted"] is False
    assert rejected["reason"] == "candidate_as_confirmed_forbidden"

    print("C055_RECONCILIATION_PASS 12/12; underlying firewall policy remains 15/15")


if __name__ == "__main__":
    self_test()
