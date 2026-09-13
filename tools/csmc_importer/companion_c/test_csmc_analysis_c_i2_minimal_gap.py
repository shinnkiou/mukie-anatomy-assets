#!/usr/bin/env python3
"""Synthetic regression tests for Companion C Run C-039."""
from csmc_analysis_c_i2_minimal_gap import analyze


def fixture():
    lengths = [48,49,48,48,49,48,49,48,48,49,48,49,48,49,48,48,49,48,49,48,49,48]
    matches = [23,24,24,24,25,23,25,23,24,25,23,25,23,24,24,24,25,23,25,23,24,24]
    return {
        "record_count_complete": 22,
        "record_lengths_blocks": lengths,
        "five_record_group_sums_blocks": [242,242,242,242],
        "per_record_match_summary": [
            {"record_index": i, "length_blocks": length, "same_position_matches": matches[i], "off_diagonal_matches": 0}
            for i, length in enumerate(lengths)
        ],
        "sources": {"a_kind":"catalog_character","b_kind":"character","a_blob_sha256":"a"*64,"b_blob_sha256":"b"*64},
    }


def test_partial_reconstruction():
    out = analyze(fixture(), "sha256:test")
    assert out["valid"] is True
    r = out["reconstruction"]
    assert r["signature_rows_resolved"] == 16
    assert r["ambiguous_record_indices"] == [2,3,8,14,15,21]
    assert r["full_signature_assignment_count_after_marginals"] == 20
    assert r["sufficient_public_safe_discriminator"]["relative_block"] == 24


def test_fail_closed_on_impossible_match_count():
    doc = fixture()
    doc["per_record_match_summary"][0]["same_position_matches"] = 26
    out = analyze(doc, "sha256:test")
    assert out["valid"] is False
    assert "no_signature_candidate_at_0" in out["errors"]


def test_fail_closed_on_broken_group_cadence():
    doc = fixture()
    doc["five_record_group_sums_blocks"] = [242,242,241,243]
    out = analyze(doc, "sha256:test")
    assert out["valid"] is False
    assert "unexpected_five_record_group_sums" in out["errors"]


if __name__ == "__main__":
    test_partial_reconstruction()
    test_fail_closed_on_impossible_match_count()
    test_fail_closed_on_broken_group_cadence()
    print("3/3 PASS")
