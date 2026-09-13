from __future__ import annotations

import argparse
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from csmc_p4_anchor_probe import load_surface, stored_payload


ROLE_ORDER = (
    "record_whole",
    "stable_prefix_0_20",
    "control_zone_21_27",
    "preserved_island_25_26",
)


def fixed_regions(record_length_qwords: int) -> dict[str, tuple[int, int]]:
    if record_length_qwords < 28:
        raise ValueError("record too short for fixed +965 role grammar")
    return {
        "record_whole": (0, record_length_qwords * 8),
        "stable_prefix_0_20": (0, 21 * 8),
        "control_zone_21_27": (21 * 8, 7 * 8),
        "preserved_island_25_26": (25 * 8, 2 * 8),
    }


def eligible_shape(region_length: int, width: int) -> int | None:
    data_len = region_length - 4
    if data_len < 0 or data_len % width:
        return None
    return data_len // width


def exact_counted_be_fit(region: bytes, width: int) -> dict[str, Any] | None:
    count = eligible_shape(len(region), width)
    if count is None or len(region) < 4:
        return None
    observed_count = int.from_bytes(region[:4], "big")
    if observed_count != count:
        return None
    if count > 4096:
        return None
    data = region[4:]
    fmt = ">" + ("f" if width == 4 else "d") * count
    values = struct.unpack(fmt, data) if count else ()
    finite_count = sum(math.isfinite(v) for v in values)
    return {
        "encoding": "be_f32" if width == 4 else "be_f64",
        "count": count,
        "region_bytes": len(region),
        "finite_values": finite_count,
        "value_count": count,
        "all_finite": finite_count == count,
    }


def preflight_shape_table(record_lengths_qwords: list[int]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for length in sorted(set(record_lengths_qwords)):
        for role in ROLE_ORDER:
            _, region_len = fixed_regions(length)[role]
            rows.append({
                "record_length_qwords": length,
                "role": role,
                "region_bytes": region_len,
                "be_f32_expected_count": eligible_shape(region_len, 4),
                "be_f64_expected_count": eligible_shape(region_len, 8),
            })
    return {
        "roles": list(ROLE_ORDER),
        "rows": rows,
        "all_fixed_roles_f64_shape_ineligible": all(r["be_f64_expected_count"] is None for r in rows),
    }


def analyze_fixed_binding_roles(
    a_payload: bytes,
    b_payload: bytes,
    starts: list[int],
    delta_blocks: int,
) -> dict[str, Any]:
    if len(starts) < 2:
        raise ValueError("at least two record starts are required")
    if any(y <= x for x, y in zip(starts, starts[1:])):
        raise ValueError("record starts must be strictly increasing")

    lengths = [y - x for x, y in zip(starts, starts[1:])]
    complete = starts[:-1]
    shape = preflight_shape_table(lengths)
    fits: list[dict[str, Any]] = []
    opportunities = 0

    for record_index, (start_qword, length_qwords) in enumerate(zip(complete, lengths)):
        for role in ROLE_ORDER:
            rel_byte, region_len = fixed_regions(length_qwords)[role]
            for surface_name, payload, surface_start_qword in (
                ("a", a_payload, start_qword),
                ("b", b_payload, start_qword + delta_blocks),
            ):
                start_byte = surface_start_qword * 8 + rel_byte
                region = payload[start_byte:start_byte + region_len]
                if len(region) != region_len:
                    continue
                for width in (4, 8):
                    expected = eligible_shape(region_len, width)
                    if expected is None:
                        continue
                    opportunities += 1
                    fit = exact_counted_be_fit(region, width)
                    if fit is not None:
                        fits.append({
                            "record_index": record_index,
                            "record_length_qwords": length_qwords,
                            "surface": surface_name,
                            "role": role,
                            **fit,
                        })

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in fits:
        grouped[(row["surface"], row["role"], row["encoding"])].append(row)

    recurrence = []
    for (surface, role, encoding), rows in sorted(grouped.items()):
        record_ids = sorted({int(r["record_index"]) for r in rows})
        recurrence.append({
            "surface": surface,
            "role": role,
            "encoding": encoding,
            "fit_count": len(rows),
            "distinct_record_count": len(record_ids),
            "recurrent_same_role": len(record_ids) >= 2,
            "record_indices": record_ids,
            "counts": dict(Counter(int(r["count"]) for r in rows)),
            "all_values_finite": all(bool(r["all_finite"]) for r in rows),
        })

    recurrent = [r for r in recurrence if r["recurrent_same_role"]]
    nominal_fwer = min(1.0, opportunities / (2**32))

    return {
        "analysis": "csmc_p4_counted_be_fixed_role_binding_v1",
        "protocol": {
            "post_hoc_window_search": False,
            "roles_predeclared_from_structural_grammar": list(ROLE_ORDER),
            "record_count": len(lengths),
            "surface_count": 2,
            "codec_widths_considered": [4, 8],
            "eligible_codec_opportunities": opportunities,
            "uniform_prefix_null_fwer_any_fit_upper_bound": nominal_fwer,
            "probability_guardrail": "Nominal union bound only; not a model of the CELSYS serializer or independent-trial claim.",
        },
        "shape_preflight": shape,
        "fit_count": len(fits),
        "fits": fits,
        "same_role_recurrence": recurrence,
        "recurrent_binding_candidates": recurrent,
        "binding_gate": {
            "recurrent_exact_fit_present": bool(recurrent),
            "semantic_binding_claimed": False,
            "geometry_binding_claimed": False,
            "note": "A recurrent exact fit can support codec binding only. Semantic promotion still requires independent controlled evidence.",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Test only predeclared +965 structural roles for CELSYS counted big-endian numeric codec fits"
    )
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--a-kind", default=None)
    ap.add_argument("--b-kind", default=None)
    ap.add_argument("--lattice-json", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    prior = json.loads(Path(args.lattice_json).read_text(encoding="utf-8"))
    starts = [int(x) for x in prior["record_start_blocks"]]
    delta = int(prior["delta_blocks"])

    a_blob, a_meta = load_surface(args.a, args.a_kind)
    b_blob, b_meta = load_surface(args.b, args.b_kind)
    out = analyze_fixed_binding_roles(
        stored_payload(a_blob, a_meta),
        stored_payload(b_blob, b_meta),
        starts,
        delta,
    )
    out["sources"] = {
        "a_blob_sha256": a_meta.blob_sha256,
        "a_kind": a_meta.kind,
        "b_blob_sha256": b_meta.blob_sha256,
        "b_kind": b_meta.kind,
    }
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
