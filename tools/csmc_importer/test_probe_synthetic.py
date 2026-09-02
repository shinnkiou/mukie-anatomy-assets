import sqlite3
import struct
import tempfile
from pathlib import Path

from csmc_core import MAGIC, probe


def lp(data: bytes) -> bytes:
    return struct.pack("<I", len(data)) + data


def build_fixture(path: Path, kind: bytes = b"character") -> None:
    guid = bytes.fromhex("00112233445566778899aabbccddeeff")
    payload = b"synthetic-payload-for-parser-test"
    blob = (
        lp(MAGIC)
        + lp(kind)
        + guid
        + struct.pack("<III", 2, len(payload), len(payload))
        + payload
    )
    con = sqlite3.connect(path)
    try:
        con.execute(
            "create table character(_PW_ID integer primary key autoincrement, version integer default null, character blob default null)"
        )
        con.execute("insert into character(version, character) values (?, ?)", (1, blob))
        con.commit()
    finally:
        con.close()


def test_synthetic_character_fixture() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "fixture.csmc"
        build_fixture(p)
        result = probe(p)
        assert result.payload_kind == "character"
        assert result.inner_version == 2
        assert result.logical_size == len(b"synthetic-payload-for-parser-test")
        assert result.guid_hex == "00112233445566778899aabbccddeeff"
        assert result.signatures["png"] == -1


if __name__ == "__main__":
    test_synthetic_character_fixture()
    print("PASS synthetic CSMC fixture")
