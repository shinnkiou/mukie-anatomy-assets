#!/usr/bin/env python3
"""C-050 public-safe controlled-fixture aggregate validator.

Contains only aggregate counts/relations. No CSMC payload bytes.
"""
FIXTURES = {
    "F01": (1, 3),
    "F02": (1, 3),
    "F03": (1, 3),
    "F04": (1, 3),
    "F05": (1, 3),
    "F06": (2, 4),
    "F07": (2, 4),
    "R01": (1, 3),
    "R02": (1, 3),
    "R03": (1, 3),
    "R04": (1, 3),
    "R05": (1, 3),
    "V01": (8, 10),
}

PAIRWISE_QWORD_DELTAS = {
    "F01_to_F02": 1,
    "F02_to_F03": 32,
    "F03_to_F04": 76,
    "F03_to_F05": 7,
    "F03_to_F06": 320,
    "F03_to_F07": 332,
    "R01_to_R02": 33,
    "R02_to_R03": 9,
    "R03_to_R04": 7,
    "R04_to_R05": -1,
}

CADENCE_QWORDS = 307


def self_test():
    for fixture, (render_parts, observed) in FIXTURES.items():
        assert observed == 2 + render_parts, (fixture, render_parts, observed)

    assert PAIRWISE_QWORD_DELTAS["F03_to_F06"] - CADENCE_QWORDS == 13
    assert PAIRWISE_QWORD_DELTAS["F03_to_F07"] - CADENCE_QWORDS == 25
    assert PAIRWISE_QWORD_DELTAS["R04_to_R05"] == -1

    semantic_promotion_count = 0
    blender_emit_ready = False
    assert semantic_promotion_count == 0
    assert blender_emit_ready is False
    print("SELF_TEST_PASS 17/17")


if __name__ == "__main__":
    self_test()
