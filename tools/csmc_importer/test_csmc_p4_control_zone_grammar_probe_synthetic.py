#!/usr/bin/env python3
from __future__ import annotations

import hashlib

from csmc_p4_control_zone_grammar_probe import analyze


def qword(tag: str, index: int) -> bytes:
    return hashlib.sha256(f"{tag}:{index}".encode()).digest()[:8]


def main() -> None:
    starts = [0, 48, 97, 145]
    lengths = [48, 49, 48, 49]
    delta = 7
    total_blocks = 220
    left = bytearray().join(qword("left", i) for i in range(total_blocks))
    right = bytearray().join(qword("right", i) for i in range(total_blocks + delta + 8))

    signatures = [
        "0000110",  # length 48
        "1000111",  # length 49
        "0001110",  # length 48
        "0000111",  # length 49; intentionally ambiguous signature family
    ]
    rel = [21, 22, 23, 24, 25, 26, 27]

    for start, sig in zip(starts, signatures):
        # Stable prefix is copied exactly but contains no hard-coded model data.
        for r in range(21):
            dst = (start + delta + r) * 8
            src = (start + r) * 8
            right[dst:dst + 8] = left[src:src + 8]
        for r, bit in zip(rel, sig):
            if bit == "1":
                dst = (start + delta + r) * 8
                src = (start + r) * 8
                right[dst:dst + 8] = left[src:src + 8]

    out = analyze(bytes(left), bytes(right), starts, lengths, delta, rel)
    assert out["record_count"] == 4
    assert out["fixed_equal_relative_blocks"] == [25, 26]
    assert out["fixed_different_relative_blocks"] == [22, 23]
    assert out["conditional_relative_blocks"] == [21, 24, 27]
    assert out["signature_counts_by_length"]["48"] == {"0000110": 1, "0001110": 1}
    assert out["signature_counts_by_length"]["49"] == {"0000111": 1, "1000111": 1}

    rules = {
        (r["relative_block"], r["condition"], r["implies_length_blocks"]): r
        for r in out["one_way_marker_rules"]
    }
    assert (21, "equal", 49) in rules
    assert (24, "equal", 48) in rules
    assert (27, "different", 48) in rules
    assert rules[(27, "different", 48)]["support"] == 2
    print("CSMC P4 control-zone grammar synthetic PASS")


if __name__ == "__main__":
    main()
