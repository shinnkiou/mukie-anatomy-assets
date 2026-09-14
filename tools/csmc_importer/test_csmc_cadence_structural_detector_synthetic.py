#!/usr/bin/env python3
from csmc_cadence_structural_detector import detect_cadence_qwords


def make_synthetic_cadence(cadence_count: int, lag: int = 307) -> list[bytes]:
    run_count = 2 * (cadence_count - 1)
    starts = [100]
    gaps = (221, 88)
    for i in range(1, run_count):
        starts.append(starts[-1] + gaps[(i - 1) % 2])
    lengths = [18 if i % 2 == 0 else 12 for i in range(run_count)]
    n = max(s + lag + length for s, length in zip(starts, lengths)) + 100

    parent = list(range(n))
    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a: int, b: int):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for start, length in zip(starts, lengths):
        for j in range(length):
            union(start + j, start + lag + j)

    root_ids = {}
    out = []
    for i in range(n):
        root = find(i)
        if root not in root_ids:
            root_ids[root] = len(root_ids) + 1
        out.append(root_ids[root].to_bytes(8, "little"))
    return out


def test_detects_expected_cadence_counts():
    for expected in (3, 4, 10):
        out = detect_cadence_qwords(make_synthetic_cadence(expected))
        assert out.detected is True
        assert out.cadence_count_candidate == expected
        assert out.cluster_run_count == 2 * (expected - 1)
        assert out.period_bytes == 2456
        assert out.raw_values_embedded is False
        assert out.semantic_promotion is False


def test_wrong_lag_does_not_inherit_307_result():
    qwords = make_synthetic_cadence(4)
    out = detect_cadence_qwords(qwords, lag_qwords=306)
    assert out.detected is False
    assert out.cadence_count_candidate is None


def test_no_repeat_input_stays_unresolved():
    qwords = [i.to_bytes(8, "little") for i in range(1000)]
    out = detect_cadence_qwords(qwords)
    assert out.detected is False
    assert out.cluster_run_count == 0
    assert out.cadence_count_candidate is None


def main():
    test_detects_expected_cadence_counts()
    test_wrong_lag_does_not_inherit_307_result()
    test_no_repeat_input_stays_unresolved()
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
