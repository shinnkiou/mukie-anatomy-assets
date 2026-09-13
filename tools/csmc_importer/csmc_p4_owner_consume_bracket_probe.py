#!/usr/bin/env python3
"""Public-safe qword extinction / phase-switch probe for CSMC P4 research.

The probe consumes already-extracted payload bytes and emits aggregate counts only.
It never writes or prints source qword values.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

QWORD = 8


def read_qword(data: bytes, block: int) -> bytes:
    start = block * QWORD
    end = start + QWORD
    if block < 0 or end > len(data):
        raise ValueError(f"qword block out of range: {block}")
    return data[start:end]


def iter_qwords(data: bytes) -> Iterable[bytes]:
    usable = len(data) - (len(data) % QWORD)
    for off in range(0, usable, QWORD):
        yield data[off : off + QWORD]


def barrier_values(data: bytes, start_block: int, end_block: int) -> list[bytes]:
    if not (0 <= start_block <= end_block):
        raise ValueError("invalid block interval")
    return [read_qword(data, i) for i in range(start_block, end_block)]


def global_presence(query_values: list[bytes], target: bytes) -> dict[str, int]:
    query_set = set(query_values)
    found: set[bytes] = set()
    if query_set:
        for value in iter_qwords(target):
            if value in query_set:
                found.add(value)
                if len(found) == len(query_set):
                    break
    return {
        "query_qwords": len(query_values),
        "query_distinct_qwords": len(query_set),
        "query_distinct_found_anywhere_in_target": len(found),
    }


def direct_match_count(clip: bytes, csmc: bytes, start: int, end: int, delta: int) -> int:
    if end < start:
        raise ValueError("invalid match interval")
    count = 0
    for i in range(start, end):
        if read_qword(clip, i) == read_qword(csmc, i + delta):
            count += 1
    return count


def analyze(
    clip: bytes,
    csmc: bytes,
    *,
    clip_prev_anchor: int,
    clip_next_anchor: int,
    csmc_prev_anchor: int,
    csmc_next_anchor: int,
    delta_before: int,
    delta_after: int,
    pre_start: int,
    post_end: int,
) -> dict[str, object]:
    clip_open_start = clip_prev_anchor + 1
    clip_open_end = clip_next_anchor
    csmc_open_start = csmc_prev_anchor + 1
    csmc_open_end = csmc_next_anchor

    if csmc_prev_anchor - clip_prev_anchor != delta_before:
        raise ValueError("left anchor does not match delta_before")
    if csmc_next_anchor - clip_next_anchor != delta_after:
        raise ValueError("right anchor does not match delta_after")
    if pre_start > clip_prev_anchor or post_end <= clip_next_anchor:
        raise ValueError("invalid pre/post bounds")

    clip_barrier = barrier_values(clip, clip_open_start, clip_open_end)
    csmc_barrier = barrier_values(csmc, csmc_open_start, csmc_open_end)

    left_reused = read_qword(clip, clip_prev_anchor) == read_qword(csmc, csmc_prev_anchor)
    right_reused = read_qword(clip, clip_next_anchor) == read_qword(csmc, csmc_next_anchor)

    result = {
        "schema_version": "csmc_p4_owner_consume_bracket_v1",
        "boundary": {
            "clip_prev_anchor_block": clip_prev_anchor,
            "clip_open_start_block": clip_open_start,
            "clip_open_end_block_exclusive": clip_open_end,
            "clip_open_qwords": clip_open_end - clip_open_start,
            "csmc_prev_anchor_block": csmc_prev_anchor,
            "csmc_open_start_block": csmc_open_start,
            "csmc_open_end_block_exclusive": csmc_open_end,
            "csmc_open_qwords": csmc_open_end - csmc_open_start,
            "delta_before_qwords": delta_before,
            "delta_after_qwords": delta_after,
            "net_relative_size_change_qwords": delta_after - delta_before,
            "net_relative_size_change_bytes": (delta_after - delta_before) * QWORD,
        },
        "global_presence": {
            "clip_barrier_in_csmc": global_presence(clip_barrier, csmc),
            "csmc_barrier_in_clip": global_presence(csmc_barrier, clip),
            "left_boundary_qword_reused_at_expected_position": left_reused,
            "right_boundary_qword_reused_at_expected_position": right_reused,
        },
        "phase_lock": {
            "pre_start_block": pre_start,
            "pre_end_block_exclusive": clip_open_start,
            "pre_qwords": clip_open_start - pre_start,
            "pre_matches_delta_before": direct_match_count(clip, csmc, pre_start, clip_open_start, delta_before),
            "pre_matches_delta_after": direct_match_count(clip, csmc, pre_start, clip_open_start, delta_after),
            "barrier_matches_delta_before": direct_match_count(clip, csmc, clip_open_start, clip_open_end, delta_before),
            "barrier_matches_delta_after": direct_match_count(clip, csmc, clip_open_start, clip_open_end, delta_after),
            "post_start_block": clip_next_anchor,
            "post_end_block_exclusive": post_end,
            "post_qwords": post_end - clip_next_anchor,
            "post_matches_delta_before": direct_match_count(clip, csmc, clip_next_anchor, post_end, delta_before),
            "post_matches_delta_after": direct_match_count(clip, csmc, clip_next_anchor, post_end, delta_after),
        },
    }
    result["global_presence"]["complete_cross_serialization_extinction"] = (
        result["global_presence"]["clip_barrier_in_csmc"]["query_distinct_found_anywhere_in_target"] == 0
        and result["global_presence"]["csmc_barrier_in_clip"]["query_distinct_found_anywhere_in_target"] == 0
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip-payload", type=Path, required=True)
    ap.add_argument("--csmc-payload", type=Path, required=True)
    ap.add_argument("--clip-prev-anchor", type=int, required=True)
    ap.add_argument("--clip-next-anchor", type=int, required=True)
    ap.add_argument("--csmc-prev-anchor", type=int, required=True)
    ap.add_argument("--csmc-next-anchor", type=int, required=True)
    ap.add_argument("--delta-before", type=int, required=True)
    ap.add_argument("--delta-after", type=int, required=True)
    ap.add_argument("--pre-start", type=int, required=True)
    ap.add_argument("--post-end", type=int, required=True)
    ap.add_argument("--json-out", type=Path)
    ns = ap.parse_args()

    result = analyze(
        ns.clip_payload.read_bytes(),
        ns.csmc_payload.read_bytes(),
        clip_prev_anchor=ns.clip_prev_anchor,
        clip_next_anchor=ns.clip_next_anchor,
        csmc_prev_anchor=ns.csmc_prev_anchor,
        csmc_next_anchor=ns.csmc_next_anchor,
        delta_before=ns.delta_before,
        delta_after=ns.delta_after,
        pre_start=ns.pre_start,
        post_end=ns.post_end,
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    if ns.json_out:
        ns.json_out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
