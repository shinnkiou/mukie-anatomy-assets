#!/usr/bin/env python3
from csmc_p4_transition_object import analyze, self_test

self_test()

doc = {
    "schema_version": "csmc_p4_transition_object_v1",
    "boundary_id": "x",
    "container_route": "character",
    "regime_before": "+1",
    "regime_after": "+2",
    "clip_gap_qwords": 1,
    "csmc_gap_qwords": 2,
    "delta_before_qwords": 1,
    "delta_after_qwords": 2,
    "left_anchor_reused": True,
    "right_anchor_reused": True,
    "complete_cross_serialization_extinction": True,
    "post_regime_recurs_later": True,
    "guardrails": {
        "semantic_owner_confirmed": False,
        "codec_confirmed": False,
        "geometry_confirmed": False,
        "blender_import_confirmed": False,
        "runtime_trace_executed": False,
    },
}
out = analyze(doc)
assert out["valid"] is False and "missing_phase_lock" in out["errors"]
print("EXTRA_TEST_PASS")
