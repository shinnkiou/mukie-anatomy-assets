from __future__ import annotations

import csv
import struct
import tempfile
from pathlib import Path

from modeler_capture_header_probe import MEM_PRIVATE, inspect_csv

MAGIC = b"CLIP_STUDIO_3D_DATA2"
GUID = "19c1747bf2b84da197b9ead412256c5b"


def main() -> None:
    kind = b"character"
    logical = 12345
    stored = ((logical + 7) // 8) * 8 + 8
    header = (
        struct.pack("<I", len(MAGIC)) + MAGIC
        + struct.pack("<I", len(kind)) + kind
        + bytes.fromhex(GUID)
        + struct.pack("<III", 2, logical, stored)
    )
    prefix = b"\xCC" * 24
    context = prefix + header + b"\xAA" * 16
    magic_address = 0x10000000 + len(prefix) + 4

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "marker_hits.csv"
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["time", "pid", "marker", "encoding", "address", "region_base", "protect", "type", "context_hex"])
            w.writeheader()
            w.writerow({
                "time": "2026-09-12T00:00:00+09:00",
                "pid": "42",
                "marker": MAGIC.decode("ascii"),
                "encoding": "UTF8",
                "address": hex(magic_address),
                "region_base": "0x10000000",
                "protect": "0x4",
                "type": hex(MEM_PRIVATE),
                "context_hex": context.hex().upper(),
            })

        result = inspect_csv(
            p,
            expected_guid=GUID,
            expected_kind="character",
            require_region_type=MEM_PRIVATE,
            saved_logical=logical - 7,
            saved_stored=stored - 8,
        )
        assert result["candidate_count"] == 1
        c = result["candidates"][0]
        assert c["blob_start"] == f"0x{magic_address - 4:X}"
        assert c["is_mem_private"] is True
        assert c["guid_hex"] == GUID
        assert c["kind"] == "character"
        assert c["inner_version"] == 2
        assert c["stored_minus_align8_logical"] == 8
        assert c["logical_delta_vs_saved"] == 7
        assert c["stored_delta_vs_saved"] == 8

    print("synthetic capture header probe: PASS")


if __name__ == "__main__":
    main()
