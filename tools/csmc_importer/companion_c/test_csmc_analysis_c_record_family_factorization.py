from csmc_analysis_c_record_family_factorization import analyze


def test_shared_signature_forces_two_axes():
    fixture = {
        "signature_counts_by_length": {
            "48": {"A": 2, "S": 1},
            "49": {"S": 1, "B": 2},
        }
    }
    out = analyze(fixture)
    assert out["length_is_function_of_signature"] is False
    assert out["signature_is_function_of_length"] is False
    assert out["signatures_shared_across_lengths"] == {"S": [48, 49]}
    assert out["recommended_ir_axes"] == ["length_blocks", "preserve_signature"]
