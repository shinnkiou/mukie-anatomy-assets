from __future__ import annotations

import sqlite3
import struct
import tempfile
from pathlib import Path

from csmc_core import MAGIC, probe


def lp(data: bytes) -> bytes:
    return struct.pack("<I", len(data)) + data


def make_blob(kind: bytes, payload: bytes) -> bytes:
    guid = bytes.fromhex("00112233445566778899aabbccddeeff")
    return (
        lp(MAGIC)
        + lp(kind)
        + guid
        + struct.pack("<III", 2, len(payload), len(payload))
        + payload
    )


def make_db(path: Path, table: str, blob_col: str, kind: bytes) -> None:
    blob = make_blob(kind, b"SYNTHETIC_PAYLOAD")
    con = sqlite3.connect(path)
    try:
        con.execute(
            f'create table "{table}"(_PW_ID integer primary key, version integer, "{blob_col}" blob)'
        )
        con.execute(
            f'insert into "{table}"(version,"{blob_col}") values(?,?)',
            (1, blob),
        )
        con.commit()
    finally:
        con.close()


def test_supported_schemas() -> None:
    cases = [
        ("character", "character", b"character", 65),
        ("character", "catalog_data", b"catalog_character", 73),
        ("catalog_character", "catalog_data", b"catalog_character", 73),
    ]
    with tempfile.TemporaryDirectory() as td:
        for i, (table, col, kind, expected_off) in enumerate(cases):
            p = Path(td) / f"case{i}.sqlite"
            make_db(p, table, col, kind)
            result = probe(p)
            assert result.sqlite_table == table
            assert result.blob_column == col
            assert result.payload_kind == kind.decode("ascii")
            assert result.guid_hex == "00112233445566778899aabbccddeeff"
            assert result.inner_version == 2
            assert result.payload_offset == expected_off
            assert result.payload_size_available == len(b"SYNTHETIC_PAYLOAD")


if __name__ == "__main__":
    test_supported_schemas()
    print("PASS synthetic CSMC/CS3C/catalog_character schemas")
