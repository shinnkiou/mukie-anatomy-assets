from csmc_analysis_c_p3_artifact_evidence import analyze, classify_candidate


def test_plan_only_is_not_execution():
    assert classify_candidate({"kind": "TEMPLATE"}) == "PLAN_ONLY"


def test_executed_pair_requires_controlled_evidence():
    row = {
        "kind": "PAIR_REPORT",
        "stage_sha256": {"A0": "a", "C0": "c", "B0": "b"},
        "c0_vs_b0_diff": {"changed_regions": 2},
        "interpretable": True,
    }
    assert classify_candidate(row) == "EXECUTED_DIFFERENTIAL_EVIDENCE"


def test_realistic_plan_inventory_does_not_promote_semantics():
    discovery = {
        "searched_experiment_ids": ["P3-CONTROL-001"],
        "candidates": [
            {"source": "github", "kind": "RUNBOOK"},
            {"source": "github", "kind": "TEMPLATE", "stage_sha256": {}, "c0_vs_b0_diff": None, "interpretable": None},
        ],
    }
    out = analyze(discovery)
    assert out["executed_interpretable_pair_found"] is False
    assert out["semantic_promotion_allowed"] is False
