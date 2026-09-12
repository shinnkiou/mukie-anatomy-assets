from __future__ import annotations

import sqlite3
import struct
import tempfile
from pathlib import Path

from csmc_p4_anchor_probe import compare_surfaces, load_surface

MAGIC = b"CLIP_STUDIO_3D_DATA2"


def lp(value: bytes) -> bytes:
    return struct.pack("<I", len(value)) + value


def make_c3d(kind: bytes, opaque: bytes, guid_byte: int) -> bytes:
    logical = max(0, len(opaque) - 8)
    stored = len(opaque)
    return (
        lp(MAGIC)
        + lp(kind)
        + bytes([guid_byte]) * 16
        + struct.pack("<III", 2, logical, stored)
        + opaque
    )


def make_exta(ext_id: bytes, blob: bytes) -> bytes:
    payload = len(ext_id).to_bytes(8, "big") + ext_id + len(blob).to_bytes(8, "big") + blob
    return b"CHNKExta" + len(payload).to_bytes(8, "big") + payload


def make_clip(path: Path, blob: bytes) -> None:
    raw = b"CSFCHUNK" + b"\x00" * 16
    raw += make_exta(b"extrnlidTEST", blob)
    raw += b"CHNKFoot" + (0).to_bytes(8, "big")
    path.write_bytes(raw)


def make_csmc(path: Path, blob: bytes) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute("create table character(version integer, character blob)")
        con.execute("insert into character values (?, ?)", (2, blob))
        con.commit()
    finally:
        con.close()


def main() -> None:
    base_blocks = [struct.pack("<Q", 0x100000 + i) for i in range(96)]
    inserted = [struct.pack("<Q", 0xABC000 + i) for i in range(3)]
    clip_opaque = b"".join(base_blocks)
    csmc_opaque = b"".join(inserted + base_blocks)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        clip_path = root / "synthetic.clip"
        csmc_path = root / "synthetic.csmc"
        make_clip(clip_path, make_c3d(b"catalog_character", clip_opaque, 0x11))
        make_csmc(csmc_path, make_c3d(b"character", csmc_opaque, 0x22))

        _, clip_meta = load_surface(clip_path, "catalog_character")
        _, csmc_meta = load_surface(csmc_path, "character")
        assert clip_meta.container == "clip_csfchunk"
        assert clip_meta.kind == "catalog_character"
        assert csmc_meta.container == "sqlite"
        assert csmc_meta.kind == "character"

        result = compare_surfaces(
            clip_path,
            csmc_path,
            "catalog_character",
            "character",
            mask_bits=0,
            top_peaks=3,
            runs_per_peak=3,
        )
        relation = result["payload_relation"]["anchor_relation"]
        assert relation["shared_sampled_unique_anchors"] == 96
        peak = relation["top_position_delta_peaks"][0]
        assert peak["delta_blocks_b_minus_a"] == 3
        assert peak["sampled_unique_anchor_count"] == 96
        longest = peak["longest_exact_runs"][0]
        assert longest["a_start_block"] == 0
        assert longest["b_start_block"] == 3
        assert longest["length_blocks"] == 96
        assert longest["length_bytes"] == 96 * 8

    print("synthetic P4 anchor probe: PASS")


if __name__ == "__main__":
    main()
