#!/usr/bin/env python3
import sqlite3
import struct
import tempfile
from pathlib import Path

from csmc_controlled_envelope import KIND, MAGIC, align8
from csmc_import_intake import ImportIntakeError, inspect_csmc


def make_blob(logical: int, *, stored=None, kind=KIND) -> bytes:
    if stored is None:
        stored = align8(logical) + 8
    payload = bytes((i * 29 + 7) & 0xFF for i in range(stored))
    return (
        struct.pack("<I", len(MAGIC)) + MAGIC +
        struct.pack("<I", len(kind)) + kind +
        bytes.fromhex("00112233445566778899aabbccddeeff") +
        struct.pack("<III", 2, logical, stored) +
        payload
    )


def write_db(path: Path, blob: bytes, *, column="character", rows=1):
    con = sqlite3.connect(path)
    con.execute(f'CREATE TABLE character(version INTEGER, "{column}" BLOB)')
    for _ in range(rows):
        con.execute(f'INSERT INTO character(version, "{column}") VALUES (?, ?)', (1, blob))
    con.commit()
    con.close()


def expect_rejected(path: Path):
    try:
        inspect_csmc(path)
    except (ImportIntakeError, ValueError, sqlite3.Error):
        return
    raise AssertionError("invalid intake accepted")


def test_valid_intake():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "valid.csmc"
        write_db(p, make_blob(31))
        out = inspect_csmc(p)
        assert out.schema_version == "csmc_import_intake_v0_2"
        assert out.sqlite_table == "character"
        assert out.blob_column == "character"
        assert out.logical_length == 31
        assert out.logical_mod8_phase == 7
        assert out.stored_length == 40
        assert out.payload_offset == 65
        assert out.payload_size_available == 40
        assert out.frame_rule_holds is True
        assert out.raw_payload_embedded is False
        assert out.pipeline_stage == "STRUCTURAL_ONLY"
        assert out.semantic_promotion_count == 0
        assert out.geometry == "unresolved"
        assert out.index_topology == "unresolved"
        assert out.blender_emit_ready is False
        public = out.to_public_dict()
        assert "payload_bytes" not in public
        assert "source_path" not in public


def test_phase_is_structural_metadata_only():
    with tempfile.TemporaryDirectory() as td:
        for logical in range(8, 16):
            p = Path(td) / f"phase_{logical}.csmc"
            write_db(p, make_blob(logical))
            out = inspect_csmc(p)
            assert out.logical_mod8_phase == logical % 8
            assert out.geometry == "unresolved"
            assert out.index_topology == "unresolved"
            assert out.blender_emit_ready is False


def test_reject_wrong_route():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "route.csmc"
        write_db(p, make_blob(16), column="catalog_data")
        expect_rejected(p)


def test_reject_wrong_frame_rule():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "bad_rule.csmc"
        write_db(p, make_blob(16, stored=32))
        expect_rejected(p)


def test_reject_truncated_payload():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "truncated.csmc"
        blob = make_blob(17)[:-1]
        write_db(p, blob)
        expect_rejected(p)


def main():
    test_valid_intake()
    test_phase_is_structural_metadata_only()
    test_reject_wrong_route()
    test_reject_wrong_frame_rule()
    test_reject_truncated_payload()
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
