#!/usr/bin/env python3
import sqlite3
import struct
import tempfile
from pathlib import Path

from csmc_controlled_envelope import (
    MAGIC, KIND, EnvelopeError, align8, parse_character_blob, parse_csmc_file,
)


def make_blob(logical: int, *, magic=MAGIC, kind=KIND, inner_version=2, stored=None) -> bytes:
    if stored is None:
        stored = align8(logical) + 8
    payload = bytes((i * 37 + 11) & 0xFF for i in range(stored))
    return (
        struct.pack("<I", len(magic)) + magic +
        struct.pack("<I", len(kind)) + kind +
        bytes.fromhex("00112233445566778899aabbccddeeff") +
        struct.pack("<III", inner_version, logical, stored) +
        payload
    )


def test_synthetic_blob():
    blob = make_blob(17)
    env = parse_character_blob(blob)
    assert env.payload_offset == 65
    assert env.logical_length == 17
    assert env.aligned_logical_length == 24
    assert env.alignment_extension_length == 7
    assert env.stored_length == 32
    assert env.framing_remainder_length == 8
    assert env.tail_length == 15
    assert env.align8_plus8_holds is True
    assert env.raw_payload_embedded is False


def test_reject_false_align16_assumption():
    blob = make_blob(24)
    env = parse_character_blob(blob)
    assert env.stored_length == 32
    assert env.alignment_extension_length == 0
    assert env.framing_remainder_length == 8
    blob2 = make_blob(16)
    env2 = parse_character_blob(blob2)
    assert env2.stored_length == 24
    assert env2.stored_length % 16 == 8
    assert env2.framing_remainder_length == 8


def test_reject_wrong_magic_and_kind():
    for bad in (make_blob(10, magic=b"X" * 20), make_blob(10, kind=b"characteX")):
        try:
            parse_character_blob(bad)
        except EnvelopeError:
            pass
        else:
            raise AssertionError("bad frame accepted")


def test_reject_truncation():
    blob = make_blob(10)
    try:
        parse_character_blob(blob[:-1])
    except EnvelopeError:
        pass
    else:
        raise AssertionError("truncated blob accepted")


def test_sqlite_route():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "synthetic.csmc"
        con = sqlite3.connect(p)
        con.execute("CREATE TABLE character(version INTEGER, character BLOB)")
        con.execute("INSERT INTO character VALUES (?, ?)", (1, make_blob(31)))
        con.commit(); con.close()
        env = parse_csmc_file(p)
        assert env.outer_version == 1
        assert env.logical_length == 31
        assert env.aligned_logical_length == 32
        assert env.alignment_extension_length == 1
        assert env.framing_remainder_length == 8
        assert env.align8_plus8_holds


def main():
    test_synthetic_blob()
    test_reject_false_align16_assumption()
    test_reject_wrong_magic_and_kind()
    test_reject_truncation()
    test_sqlite_route()
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
