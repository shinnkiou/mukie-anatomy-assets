#!/usr/bin/env python3
from csmc_analysis_c_c056_name_literal_reconcile_c059 import BASELINE, evaluate


def test_c059_canonical_reconciliation() -> None:
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
