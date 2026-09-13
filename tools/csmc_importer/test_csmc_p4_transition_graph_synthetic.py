#!/usr/bin/env python3
from csmc_p4_transition_graph import analyze, fixture, self_test

self_test()

doc = fixture()
doc["transitions"].append({
    "boundary_id": "BND_UNRESOLVED",
    "from_delta_qwords": 10,
    "to_delta_qwords": 11,
    "clip_gap_qwords": 100,
    "csmc_gap_qwords": 101,
    "net_relative_size_change_bytes": 8,
    "complete_cross_serialization_extinction": False,
    "structural_class": "UNRESOLVED_TRANSITION",
})
out = analyze(doc)
assert out["valid"] is True
assert out["transition_count"] == 6
assert out["preferred_consumer_landmark"] == "BND_197_TO_195"
print("EXTRA_TEST_PASS")
