#!/usr/bin/env python3
from csmc_analysis_c_controlled_promotion_firewall_c055 import reconciliation_record, self_test


def test_c055_reconciliation_record() -> None:
    row = reconciliation_record()
    assert row["accepted"] is True
    assert row["run_id"] == "C-055"
    assert row["historical_collision"]["historical_run_id"] == "C-053"
    assert row["historical_collision"]["canonical_run_id"] == "C-055"
    assert row["canonical_run_map"]["C-053"] == "C-051/C-052 provenance continuity gate"
    assert row["canonical_run_map"]["C-054"] == "C-051 evidence-admission state machine"
    assert row["semantic_promotion_count"] == 0
    assert row["runtime_dispatch"] is False


def test_c055_underlying_firewall() -> None:
    self_test()
