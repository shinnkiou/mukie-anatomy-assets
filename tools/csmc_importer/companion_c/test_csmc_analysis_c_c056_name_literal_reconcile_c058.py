#!/usr/bin/env python3
from copy import deepcopy

from csmc_analysis_c_c056_name_literal_reconcile_c058 import BASELINE, evaluate


def test_c058_baseline_rejects_plaintext_name_explanation() -> None:
    out = evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["classification"] == "C056_PREFIX_PLAINTEXT_NAME_EXPLANATION_REJECTED"
    assert out["localized_delta_qwords"] == 12
    assert out["plaintext_known_identifier_explanation"] == "REJECTED_WITHIN_TESTED_ENCODINGS_AND_SURFACES"
    assert out["transformed_or_remapped_identity_confounder"] == "OPEN"
    assert out["material_semantic_binding"] == "UNRESOLVED"
    assert out["object_semantic_binding"] == "UNRESOLVED"
    assert out["i3_valid"] is False
    assert out["semantic_promotion"] is False


def test_c058_fail_closed() -> None:
    cases = []
    bad = deepcopy(BASELINE); bad["name_literal_probe"]["fixtures"]["CSMC_F06_CUBE_MAT2"]["character_blob_literal_occurrences"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); bad["name_literal_probe"]["sqlite_file_literal_occurrences_total"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); del bad["name_literal_probe"]["fixtures"]["CSMC_F07_TWO_CUBES"]; cases.append(bad)
    bad = deepcopy(BASELINE); bad["name_literal_probe"]["name_metadata_region_confirmed"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["c056"]["localized_delta_qwords"] = 13; cases.append(bad)
    bad = deepcopy(BASELINE); bad["semantic_promotion_count"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); bad["blender_emit_ready"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["runtime_dispatch"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["raw_private_bytes_published"] = True; cases.append(bad)
    for row in cases:
        assert evaluate(row)["accepted"] is False
