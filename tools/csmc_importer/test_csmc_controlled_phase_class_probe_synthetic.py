#!/usr/bin/env python3
from csmc_controlled_phase_class_probe import compare_qword_sequences


def tok(n: int) -> bytes:
    return n.to_bytes(8, "little")


def test_same_mod_large_run():
    common = [tok(1000 + i) for i in range(40)]
    a = [tok(i) for i in range(5)] + common + [tok(9001)]
    b = [tok(100 + i) for i in range(8)] + common + [tok(9002)]
    row = compare_qword_sequences(
        "SAME", "A", "B", 71, 87, a, b, "same_mod"
    )
    assert row.same_logical_mod8
    assert row.longest_run_qwords == 40
    assert row.longest_run_start_a == 5
    assert row.longest_run_start_b == 8
    assert row.trailing_qwords_after_longest_a == 1
    assert row.trailing_qwords_after_longest_b == 1
    assert row.raw_values_embedded is False


def test_different_mod_contract():
    a = [tok(i) for i in range(10)]
    b = [tok(i) for i in range(10)]
    row = compare_qword_sequences(
        "DIFF", "A", "B", 70, 71, a, b, "different_mod"
    )
    assert not row.same_logical_mod8
    assert row.total_matching_qwords == 10


def test_relation_mismatch_rejected():
    try:
        compare_qword_sequences(
            "BAD", "A", "B", 71, 79, [tok(1)], [tok(1)], "different_mod"
        )
    except ValueError:
        pass
    else:
        raise AssertionError("relation mismatch accepted")


def main():
    test_same_mod_large_run()
    test_different_mod_contract()
    test_relation_mismatch_rejected()
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
