from csmc_p4_lattice_probe import analyze_lattice


def record(seed: int, length: int, variant: int) -> bytes:
    # 8-byte unique qwords. The first 21 qwords and 25-26 are preserved;
    # serializer-sensitive zones differ deterministically by variant.
    out = []
    for r in range(length):
        base = ((seed + 1) << 32) | (r + 1)
        if r <= 20 or r in (25, 26):
            value = base
        elif r == 27 and length == 49:
            value = base
        else:
            value = base ^ ((0x9E3779B97F4A7C15 * variant) & ((1 << 64) - 1))
        out.append(value.to_bytes(8, "little"))
    return b"".join(out)


def main() -> None:
    strides = [48, 49, 48, 48, 49] * 4
    starts = [100]
    for x in strides:
        starts.append(starts[-1] + x)
    delta = 31
    total_a = (starts[-1] + 100) * 8
    total_b = (starts[-1] + delta + 100) * 8
    a = bytearray(total_a)
    b = bytearray(total_b)
    for i, length in enumerate(strides):
        s = starts[i]
        ra = record(i + 1000, length, 1)
        rb = record(i + 1000, length, 2)
        a[s * 8:(s + length) * 8] = ra
        b[(s + delta) * 8:(s + delta + length) * 8] = rb
    out = analyze_lattice(bytes(a), bytes(b), starts, delta)
    assert out["record_length_counts"] == {48: 12, 49: 8}
    assert out["five_record_group_sums_blocks"] == [242, 242, 242, 242]
    assert out["boundary_recurrence"]["current_prefix_all_equal"] is True
    assert out["boundary_recurrence"]["current_prefix_unique_per_record"] is True
    assert out["boundary_recurrence"]["all_interior_next_prefixes_restart_equal"] is True
    assert out["local_match_offsets"]["off_diagonal_matches"] == 0
    assert out["interpretation"]["classification"] == "STRONG_VARIABLE_LENGTH_RECORD_BOUNDARY_CANDIDATE"
    print("CSMC P4 lattice synthetic test: PASS")


if __name__ == "__main__":
    main()
