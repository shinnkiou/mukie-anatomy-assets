#!/usr/bin/env python3

from csmc_p4_stride_cadence_probe import analyze, gap23_regular


def main() -> None:
    observed = [
        48, 49, 48, 48, 49, 48, 49, 48, 48, 49, 48,
        49, 48, 49, 48, 48, 49, 48, 49, 48, 49, 48,
    ]
    result = analyze(observed)
    assert result["record_count"] == 22
    assert result["count_48"] == 13
    assert result["count_49"] == 9
    assert result["long_record_internal_gaps"] == [3, 2, 3, 2, 2, 3, 2, 2]
    assert result["all_internal_gaps_in_2_or_3"] is True
    exact = result["fixed_class_exact_enumeration"]
    assert exact["assignments"] == 497420
    assert exact["assignments_with_all_internal_gaps_2_or_3"] == 522
    assert abs(exact["fraction"] - (522 / 497420)) < 1e-15
    assert result["five_record_sliding_sum_counts"] == {"242": 16, "243": 2}

    clustered = [49] * 9 + [48] * 13
    assert gap23_regular(clustered) is False

    print("PASS: P4 stride cadence metadata-only synthetic checks")


if __name__ == "__main__":
    main()
