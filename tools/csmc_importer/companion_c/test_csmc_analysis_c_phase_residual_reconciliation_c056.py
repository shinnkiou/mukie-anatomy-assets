#!/usr/bin/env python3
from copy import deepcopy

from csmc_analysis_c_phase_residual_reconciliation_c056 import BASELINE, reconcile


def test_c056_baseline_accepts() -> None:
    out = reconcile(BASELINE)
    assert out["accepted"] is True
    assert out["classification"] == "PHASE_LOCALIZED_RESIDUAL_DIFFERENTIAL_CANDIDATE"
    assert out["derived"]["f03_to_f06_residual_qwords"] == 13
    assert out["derived"]["f03_to_f07_residual_qwords"] == 25
    assert out["derived"]["residual_difference_qwords"] == 12
    assert out["derived"]["f06_f07_payload_qword_delta"] == 12
    assert out["derived"]["invariant_run_start_delta_qwords"] == 12
    assert out["semantic_binding"] == "UNRESOLVED"
    assert out["semantic_promotion"] is False


def test_c056_fail_closed_guardrails() -> None:
    mutations = []
    bad = deepcopy(BASELINE); bad["c050"]["f03_to_f07_total_delta_qwords"] = 333; mutations.append(bad)
    bad = deepcopy(BASELINE); bad["phase_pair"]["longest_run_start_b"] = 458; mutations.append(bad)
    bad = deepcopy(BASELINE); bad["phase_pair"]["qword_count_b"] = 2577; mutations.append(bad)
    bad = deepcopy(BASELINE); bad["phase_pair"]["same_logical_mod8"] = False; mutations.append(bad)
    bad = deepcopy(BASELINE); bad["phase_pair"]["trailing_qwords_after_longest_b"] = 2; mutations.append(bad)
    bad = deepcopy(BASELINE); bad["semantic_promotion_count"] = 1; mutations.append(bad)
    bad = deepcopy(BASELINE); bad["blender_emit_ready"] = True; mutations.append(bad)
    bad = deepcopy(BASELINE); bad["runtime_dispatch"] = True; mutations.append(bad)
    bad = deepcopy(BASELINE); bad["raw_private_bytes_published"] = True; mutations.append(bad)

    for row in mutations:
        assert reconcile(row)["accepted"] is False
