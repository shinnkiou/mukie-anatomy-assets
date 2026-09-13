from __future__ import annotations

import struct

from csmc_p4_counted_be_binding_probe import (
    analyze_fixed_binding_roles,
    exact_counted_be_fit,
    preflight_shape_table,
)


def counted_f32(values: list[float]) -> bytes:
    return len(values).to_bytes(4, "big") + struct.pack(">" + "f" * len(values), *values)


def make_record(length_qwords: int, seed: int, island_fit: bool) -> bytes:
    raw = bytearray(((seed * 37 + i * 17) & 0xFF) for i in range(length_qwords * 8))
    if island_fit:
        island = counted_f32([seed + 0.25, seed + 1.25, seed + 2.25])
        assert len(island) == 16
        raw[25 * 8:27 * 8] = island
    return bytes(raw)


def main() -> None:
    shape = preflight_shape_table([48, 49])
    assert shape["all_fixed_roles_f64_shape_ineligible"] is True
    expected = {(r["record_length_qwords"], r["role"]): r["be_f32_expected_count"] for r in shape["rows"]}
    assert expected[(48, "record_whole")] == 95
    assert expected[(49, "record_whole")] == 97
    assert expected[(48, "stable_prefix_0_20")] == 41
    assert expected[(48, "control_zone_21_27")] == 13
    assert expected[(48, "preserved_island_25_26")] == 3

    assert exact_counted_be_fit(counted_f32([1.0, 2.0, 3.0]), 4)["count"] == 3
    assert exact_counted_be_fit(counted_f32([1.0, 2.0, 3.0]), 8) is None

    starts = [0, 48, 97, 145]
    records = [
        make_record(48, 1, True),
        make_record(49, 2, True),
        make_record(48, 3, False),
    ]
    a = b"".join(records)
    b = b"\xAA" * (5 * 8) + a
    out = analyze_fixed_binding_roles(a, b, starts, 5)
    rec = [r for r in out["recurrent_binding_candidates"] if r["role"] == "preserved_island_25_26"]
    assert len(rec) == 2
    assert all(r["encoding"] == "be_f32" for r in rec)
    assert all(r["distinct_record_count"] == 2 for r in rec)
    assert out["binding_gate"]["recurrent_exact_fit_present"] is True
    assert out["binding_gate"]["semantic_binding_claimed"] is False
    assert out["protocol"]["post_hoc_window_search"] is False
    assert out["protocol"]["eligible_codec_opportunities"] == 3 * 2 * 4
    print("synthetic counted-BE fixed-role binding probe: PASS")


if __name__ == "__main__":
    main()
