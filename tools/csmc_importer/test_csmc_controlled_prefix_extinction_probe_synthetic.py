#!/usr/bin/env python3
from csmc_controlled_prefix_extinction_probe import (
    _discover_holdout_core,
    _prefix_overlap,
    _validate_fixed_core,
)


def q(x: int) -> bytes:
    return x.to_bytes(8, "little")


def test_prefix_zero_overlap_and_core_validation():
    a = [q(1), q(2), q(100), q(101), q(999)]
    b = [q(3), q(4), q(5), q(100), q(101), q(888)]
    row = _validate_fixed_core("P", "A", "B", 9, 17, a, b, 2, 3, 2, 1)
    assert row.distinct_exact_qwords_shared_in_prefix == 0
    assert row.multiset_exact_qword_overlap_in_prefix == 0
    assert row.invariant_length_qwords == 2


def test_prefix_overlap_is_counted_fail_closed():
    distinct, multiset = _prefix_overlap([q(1), q(1), q(2)], [q(1), q(3)])
    assert distinct == 1
    assert multiset == 1


def test_holdout_bounded_trailing_search():
    a = [q(1), q(2), q(50), q(51), q(52), q(900), q(901)]
    b = [q(3), q(4), q(5), q(50), q(51), q(52), q(800), q(801)]
    row = _discover_holdout_core("H", "A", "B", 11, 19, a, b)
    assert row.trailing_qwords_each == 2
    assert row.invariant_length_qwords == 3
    assert row.invariant_start_a == 2
    assert row.invariant_start_b == 3
    assert row.distinct_exact_qwords_shared_in_prefix == 0


def test_reject_wrong_mod_and_broken_core():
    a = [q(1), q(100), q(999)]
    b = [q(2), q(100), q(888)]
    try:
        _validate_fixed_core("BADMOD", "A", "B", 9, 10, a, b, 1, 1, 1, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("different phase accepted")

    try:
        _validate_fixed_core("BADCORE", "A", "B", 9, 17, a, b, 0, 0, 2, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("broken invariant core accepted")


def main():
    test_prefix_zero_overlap_and_core_validation()
    test_prefix_overlap_is_counted_fail_closed()
    test_holdout_bounded_trailing_search()
    test_reject_wrong_mod_and_broken_core()
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
