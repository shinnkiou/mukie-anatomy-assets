#!/usr/bin/env python3
from __future__ import annotations

import struct
from csmc_p4_owner_consume_bracket_probe import analyze


def pack(values: list[int]) -> bytes:
    return b"".join(struct.pack("<Q", v) for v in values)


def main() -> int:
    # Use disjoint value domains by default so accidental cross-file equality is impossible.
    clip = [0x1000000000000000 + i for i in range(1000)]
    csmc = [0x2000000000000000 + i for i in range(1100)]

    delta_before = 5
    delta_after = 3
    clip_prev = 499
    clip_next = 520
    csmc_prev = clip_prev + delta_before
    csmc_next = clip_next + delta_after

    # Dense pre-boundary reuse at +5.
    for i in range(490, 500):
        csmc[i + delta_before] = clip[i]

    # Barrier 500..519 in clip and 505..522 in csmc intentionally stays disjoint.

    # Immediate post-boundary reuse at +3.
    for i in range(520, 560):
        csmc[i + delta_after] = clip[i]

    result = analyze(
        pack(clip),
        pack(csmc),
        clip_prev_anchor=clip_prev,
        clip_next_anchor=clip_next,
        csmc_prev_anchor=csmc_prev,
        csmc_next_anchor=csmc_next,
        delta_before=delta_before,
        delta_after=delta_after,
        pre_start=490,
        post_end=560,
    )

    b = result["boundary"]
    gp = result["global_presence"]
    ph = result["phase_lock"]
    assert b["clip_open_qwords"] == 20
    assert b["csmc_open_qwords"] == 18
    assert b["net_relative_size_change_qwords"] == -2
    assert gp["complete_cross_serialization_extinction"] is True
    assert gp["clip_barrier_in_csmc"]["query_distinct_found_anywhere_in_target"] == 0
    assert gp["csmc_barrier_in_clip"]["query_distinct_found_anywhere_in_target"] == 0
    assert gp["left_boundary_qword_reused_at_expected_position"] is True
    assert gp["right_boundary_qword_reused_at_expected_position"] is True
    assert ph["pre_matches_delta_before"] == 10
    assert ph["pre_matches_delta_after"] == 0
    assert ph["barrier_matches_delta_before"] == 0
    assert ph["barrier_matches_delta_after"] == 0
    assert ph["post_matches_delta_before"] == 0
    assert ph["post_matches_delta_after"] == 40
    print("PASS: owner/consume bracket synthetic phase switch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
