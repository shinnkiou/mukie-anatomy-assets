#!/usr/bin/env python3
"""C-059 canonical wrapper for the C-056/name-literal reconciliation.

The underlying fail-closed implementation first landed under a concurrent C-058
run-id collision. C-058 is canonically reserved for the broader plaintext source-
name negative control. This wrapper preserves the tested implementation without
rewriting history and assigns the derived C-056-specific reconciliation to C-059.
"""
from csmc_analysis_c_c056_name_literal_reconcile_c058 import BASELINE, evaluate


def self_test() -> None:
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
    print("C059_SELF_TEST_PASS canonical_wrapper")


if __name__ == "__main__":
    self_test()
