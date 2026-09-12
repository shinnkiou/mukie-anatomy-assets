from __future__ import annotations

import argparse
import csv
import json
import struct
from pathlib import Path
from typing import Any

MAGIC = b"CLIP_STUDIO_3D_DATA2"
MEM_PRIVATE = 0x20000


def parse_int(value: str | int | None) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    return int(value, 0)


def align8(n: int) -> int:
    return ((n + 7) // 8) * 8


def parse_context_candidate(row: dict[str, str], expected_guid: str | None, expected_kind: str | None) -> dict[str, Any] | None:
    if row.get("marker") != MAGIC.decode("ascii"):
        return None
    try:
        context = bytes.fromhex(row.get("context_hex", ""))
        magic_off = context.find(MAGIC)
        marker_addr = int(row.get("address", "0"), 0)
    except Exception:
        return None
    if magic_off < 4:
        return None
    if struct.unpack_from("<I", context, magic_off - 4)[0] != len(MAGIC):
        return None

    p = magic_off + len(MAGIC)
    if p + 4 > len(context):
        return None
    kind_len = struct.unpack_from("<I", context, p)[0]
    p += 4
    if kind_len < 1 or kind_len > 64 or p + kind_len + 28 > len(context):
        return None
    kind = context[p:p + kind_len].decode("ascii", "replace")
    p += kind_len
    guid = context[p:p + 16].hex()
    p += 16
    version, logical, stored = struct.unpack_from("<III", context, p)
    header_end = p + 12

    if expected_guid and guid.lower() != expected_guid.lower():
        return None
    if expected_kind and kind != expected_kind:
        return None
    if version > 100 or stored < 8:
        return None

    region_type = parse_int(row.get("type"))
    protect = parse_int(row.get("protect"))
    return {
        "time": row.get("time"),
        "pid": int(row.get("pid", "0") or 0),
        "encoding": row.get("encoding"),
        "magic_address": f"0x{marker_addr:X}",
        "blob_start": f"0x{marker_addr - 4:X}",
        "region_base": row.get("region_base"),
        "region_type": f"0x{region_type:X}" if region_type is not None else None,
        "protect": f"0x{protect:X}" if protect is not None else None,
        "is_mem_private": region_type == MEM_PRIVATE,
        "kind": kind,
        "guid_hex": guid,
        "inner_version": version,
        "logical_size": logical,
        "stored_size": stored,
        "header_bytes": header_end - (magic_off - 4),
        "stored_minus_align8_logical": stored - align8(logical),
        "full_header_validated_from_context": True,
    }


def inspect_csv(
    csv_path: str | Path,
    expected_guid: str | None = None,
    expected_kind: str | None = "character",
    require_region_type: int | None = None,
    saved_logical: int | None = None,
    saved_stored: int | None = None,
) -> dict[str, Any]:
    p = Path(csv_path)
    candidates: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            candidate = parse_context_candidate(row, expected_guid, expected_kind)
            if candidate is None:
                continue
            if require_region_type is not None and parse_int(candidate["region_type"]) != require_region_type:
                continue
            if saved_logical is not None:
                candidate["logical_delta_vs_saved"] = candidate["logical_size"] - saved_logical
            if saved_stored is not None:
                candidate["stored_delta_vs_saved"] = candidate["stored_size"] - saved_stored
            candidates.append(candidate)

    return {
        "probe_version": "modeler_capture_header_probe_v0.1",
        "source": str(p),
        "expected_guid": expected_guid,
        "expected_kind": expected_kind,
        "required_region_type": f"0x{require_region_type:X}" if require_region_type is not None else None,
        "saved_logical": saved_logical,
        "saved_stored": saved_stored,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "interpretation_guardrail": (
            "A validated serialized-looking header in a historical capture is a runtime anchor lead only. "
            "It does not prove resident geometry, decoded mesh buffers, or a stable address across processes."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate serialized CELSYS character headers in existing Modeler Observer marker_hits.csv captures")
    ap.add_argument("marker_hits_csv")
    ap.add_argument("--expected-guid", default=None)
    ap.add_argument("--kind", default="character")
    ap.add_argument("--require-type", default=None, help="Optional region type, e.g. 0x20000 for MEM_PRIVATE")
    ap.add_argument("--saved-logical", type=int, default=None)
    ap.add_argument("--saved-stored", type=int, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    result = inspect_csv(
        args.marker_hits_csv,
        expected_guid=args.expected_guid,
        expected_kind=args.kind,
        require_region_type=parse_int(args.require_type),
        saved_logical=args.saved_logical,
        saved_stored=args.saved_stored,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
