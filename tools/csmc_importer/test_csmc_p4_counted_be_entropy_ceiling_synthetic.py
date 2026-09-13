from __future__ import annotations

from csmc_p4_counted_be_entropy_ceiling import (
    analyze_entropy_ceiling,
    hmax_fixed_prefix,
    hmax_two_count_prefixes,
    max_fits_compatible,
)


def main() -> None:
    assert hmax_fixed_prefix(fitting_rows=7, total_rows=22) > 6.80
    assert hmax_fixed_prefix(fitting_rows=8, total_rows=22) < 6.80
    assert hmax_two_count_prefixes(fitting_rows=7, total_rows=22, class_caps=(13, 9)) > 6.80
    assert hmax_two_count_prefixes(fitting_rows=8, total_rows=22, class_caps=(13, 9)) < 6.80
    assert max_fits_compatible(6.80011855035714, total_rows=22, mode="fixed") == 7
    assert max_fits_compatible(
        6.80011855035714,
        total_rows=22,
        mode="record_length",
        class_caps=(13, 9),
    ) == 7
    assert max_fits_compatible(6.838498592983068, total_rows=22, mode="fixed") == 6

    lengths = [48,49,48,48,49,48,49,48,48,49,48,49,48,49,48,48,49,48,49,48,49,48]
    lattice = {
        "record_lengths_blocks": lengths,
        "relative_equality_profile": [
            {"relative_block": 0, "a_byte_entropy": 6.80011855035714, "b_byte_entropy": 6.80011855035714},
            {"relative_block": 21, "a_byte_entropy": 6.868300368538958, "b_byte_entropy": 6.945060453790815},
            {"relative_block": 25, "a_byte_entropy": 6.838498592983068, "b_byte_entropy": 6.838498592983068},
        ],
    }
    out = analyze_entropy_ceiling(lattice)
    got = {(r["role"], r["surface"]): r["max_exact_fit_rows_compatible_with_entropy"] for r in out["results"]}
    assert got[("record_whole", "a")] == 7
    assert got[("record_whole", "b")] == 7
    assert got[("stable_prefix_0_20", "a")] == 7
    assert got[("stable_prefix_0_20", "b")] == 7
    assert got[("control_zone_21_27", "a")] == 6
    assert got[("control_zone_21_27", "b")] == 5
    assert got[("preserved_island_25_26", "a")] == 6
    assert got[("preserved_island_25_26", "b")] == 6
    assert out["decision"]["regime_global_counted_be_f32_binding_excluded_for_all_fixed_roles"] is True
    assert out["decision"]["minority_same_role_recurrence_still_unresolved"] is True
    print("synthetic counted-BE entropy ceiling: PASS")


if __name__ == "__main__":
    main()
