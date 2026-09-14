#!/usr/bin/env python3
from copy import deepcopy

from csmc_analysis_c_transitive_phase_core_c057 import BASELINE, evaluate


def test_c057_transitive_cores() -> None:
    out = evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["classification"] == "PHASE_CLASS_TRANSITIVE_INVARIANT_SUFFIX_CORE_CANDIDATE"
    assert out["cores"]["mod7"]["fixtures"] == ["F02", "F04", "R01"]
    assert out["cores"]["mod7"]["common_exact_core_qwords"] == 1809
    assert out["cores"]["mod1"]["fixtures"] == ["F06", "F07", "R03"]
    assert out["cores"]["mod1"]["common_exact_core_qwords"] == 1801
    assert out["cores"]["mod1"]["ranges"]["F07"] == [774, 2575]
    assert out["cores"]["mod1"]["pair_specific_extension_f06_f07_qwords"] == 317
    assert out["semantic_promotion"] is False


def test_c057_fail_closed() -> None:
    cases = []
    bad = deepcopy(BASELINE); bad["mod7"]["ac"]["sa"] = 403; cases.append(bad)
    bad = deepcopy(BASELINE); bad["mod1"]["ac"]["length"] = 1800; cases.append(bad)
    bad = deepcopy(BASELINE); bad["mod1"]["ab"]["tb"] = 2; cases.append(bad)
    bad = deepcopy(BASELINE); bad["semantic_promotion_count"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); bad["blender_emit_ready"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["runtime_dispatch"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["raw_private_bytes_published"] = True; cases.append(bad)
    for row in cases:
        assert evaluate(row)["accepted"] is False
