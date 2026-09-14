#!/usr/bin/env python3
from copy import deepcopy
from csmc_analysis_c_phase3_prefix_extinction_reconcile_c061 import BASELINE, evaluate

def test_c061_reconciliation():
    out = evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["classification"] == "PHASE3_HOLDOUT_PREFIX_EXACT_QWORD_NEGATIVE_CONTROL_RECONCILED"
    assert out["source_pair_count"] == 7
    assert out["holdout_supported"] is True
    assert out["holdout_is_same_identity_semantic_control"] is False
    assert out["exact_qword_reuse_status"] == "NOT_PRODUCTIVE_FOR_TESTED_BOUNDED_PREFIXES"
    assert out["framing"]["framing_remainder_length"] == 8
    assert out["semantic_binding"] == "UNRESOLVED"
    assert out["blender_emit_ready"] is False

def test_c061_fail_closed():
    cases = []
    bad = deepcopy(BASELINE); bad["pair_count"] = 6; cases.append(bad)
    bad = deepcopy(BASELINE); bad["holdout_invariant_length_qwords"] = 1799; cases.append(bad)
    bad = deepcopy(BASELINE); bad["prefix_exact_qword_overlap_zero_pairs"] = 6; cases.append(bad)
    bad = deepcopy(BASELINE); bad["framing_remainder_length"] = 7; cases.append(bad)
    bad = deepcopy(BASELINE); bad["alignment_extension_semantic"] = "PADDING"; cases.append(bad)
    bad = deepcopy(BASELINE); bad["semantic_promotion_count"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); bad["runtime_dispatch"] = True; cases.append(bad)
    for row in cases:
        assert evaluate(row)["accepted"] is False
