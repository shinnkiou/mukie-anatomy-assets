from csmc_analysis_c_boundary_motif_classifier import analyze


def test_classifies_extinction_and_mixed_reuse():
    fixture = {
        "boundaries": {
            "local": {
                "barrier_matches_old_delta": 0,
                "barrier_matches_new_delta": 0,
                "clip_barrier_distinct_found_anywhere_in_csmc": 0,
                "csmc_barrier_distinct_found_anywhere_in_clip": 0,
                "complete_cross_serialization_extinction": True,
                "clip_barrier_qwords": 10,
                "net_relative_size_change_bytes": -16,
            },
            "mixed": {
                "barrier_matches_old_delta": 2,
                "barrier_matches_new_delta": 1,
                "clip_barrier_distinct_found_anywhere_in_csmc": 4,
                "csmc_barrier_distinct_found_anywhere_in_clip": 3,
                "complete_cross_serialization_extinction": False,
                "clip_barrier_qwords": 20,
                "net_relative_size_change_bytes": 128,
            },
        }
    }
    out = analyze(fixture)
    assert out["boundaries"]["local"]["class"] == "LOCAL_EXTINCTION_CANDIDATE"
    assert out["boundaries"]["mixed"]["class"] == "MIXED_REUSE_REPACK_CANDIDATE"
    assert out["universal_complete_extinction_supported"] is False
