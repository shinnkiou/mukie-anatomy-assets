#!/usr/bin/env python3
from csmc_controlled_size_law_probe import analyze


def row(fid, v, t, bones, weights, stored):
    return {
        "fixture_id": fid,
        "frame": {"stored_length": stored},
        "ground_truth": {
            "vertices": v,
            "triangles": t,
            "bones": bones,
            "weight_assignments": weights,
        },
    }


def make_inputs():
    fixtures = [
        row("CSMC_F01_TRIANGLE", 3, 1, 0, 0, 17688),
        row("CSMC_F02_QUAD", 4, 2, 0, 0, 17696),
        row("CSMC_F03_CUBE", 8, 12, 0, 0, 17952),
        row("CSMC_F04_CUBE_SUBDIV", 26, 48, 0, 0, 18560),
        row("CSMC_R01_CUBE_B1_W0", 8, 12, 1, 0, 17864),
        row("CSMC_R02_CUBE_B1_W100", 8, 12, 1, 8, 18128),
        row("CSMC_R03_CUBE_B2_W100", 8, 12, 2, 8, 18200),
        row("CSMC_R04_CUBE_B2_SPLIT", 8, 12, 2, 8, 18256),
        row("CSMC_R05_CUBE_B2_MIX50", 8, 12, 2, 16, 18248),
    ]
    manifest = {"fixtures": fixtures}
    phase = {
        "pairs": [{
            "fixture_a": "CSMC_F02_QUAD",
            "fixture_b": "CSMC_F04_CUBE_SUBDIV",
            "same_logical_mod8": True,
            "longest_run_start_a": 402,
            "longest_run_start_b": 510,
            "qword_count_a": 2212,
            "qword_count_b": 2320,
        }]
    }
    return manifest, phase


def test_bounded_negative_screen():
    manifest, phase = make_inputs()
    out = analyze(manifest, phase)
    assert out["simple_geometry_size_law_rejected"] is True
    assert out["simple_rig_size_law_rejected"] is True
    assert out["same_phase_geometry"]["prefix_delta_bytes"] == 864
    assert out["same_phase_geometry"]["teacher_deltas"] == {
        "vertices": 22,
        "triangles": 46,
        "corners": 138,
    }
    assert out["same_phase_geometry"]["pure_single_count_exact_models"] == []
    assert out["same_phase_geometry"]["vertex_plus_corner_index_exact_models"] == []
    assert out["same_phase_geometry"]["vertex_plus_triangle_exact_models"] == []
    assert out["semantic_promotion"] is False
    assert out["blender_emit_ready"] is False


def main():
    test_bounded_negative_screen()
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
