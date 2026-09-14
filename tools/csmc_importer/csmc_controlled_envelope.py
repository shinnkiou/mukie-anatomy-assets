#!/usr/bin/env python3
"""Fail-closed parser for the outer CSMC controlled-fixture character envelope.

Public-safe: this module contains no private fixture bytes. It parses an already
available authorized CSMC file, exposes only container/frame metadata, and does
not assign mesh/material/rig semantics to the opaque variable region.
"""
from __future__ import annotations

import hashlib
import sqlite3
import struct
from dataclasses import dataclass, asdict
from pathlib import Path

MAGIC = b"CLIP_STUDIO_3D_DATA2"
KIND = b"character"
EXPECTED_INNER_VERSION = 2
PAYLOAD_OFFSET = 65


class EnvelopeError(ValueError):
    pass


@dataclass(frozen=True)
class CharacterEnvelope:
    file_sha256: str
    outer_version: int
    magic: str
    kind: str
    guid_hex: str
    inner_version: int
    logical_length: int
    stored_length: int
    payload_offset: int
    align8_plus8_expected: int
    align8_plus8_holds: bool
    tail_length: int
    payload_sha256: str
    raw_payload_embedded: bool = False

    def to_public_dict(self) -> dict:
        return asdict(self)


def align8(n: int) -> int:
    if n < 0:
        raise EnvelopeError("negative length")
    return (n + 7) & ~7


def parse_character_blob(blob: bytes, *, file_sha256: str = "0" * 64, outer_version: int = 1) -> CharacterEnvelope:
    if len(blob) < PAYLOAD_OFFSET:
        raise EnvelopeError("character blob shorter than 65-byte envelope")

    off = 0
    magic_len = struct.unpack_from("<I", blob, off)[0]
    off += 4
    if magic_len != len(MAGIC):
        raise EnvelopeError("unexpected magic length")
    if blob[off:off + magic_len] != MAGIC:
        raise EnvelopeError("unexpected magic")
    off += magic_len

    kind_len = struct.unpack_from("<I", blob, off)[0]
    off += 4
    if kind_len != len(KIND):
        raise EnvelopeError("unexpected kind length")
    if blob[off:off + kind_len] != KIND:
        raise EnvelopeError("unexpected kind")
    off += kind_len

    guid = blob[off:off + 16]
    if len(guid) != 16:
        raise EnvelopeError("truncated 16-byte frame field")
    off += 16

    inner_version = struct.unpack_from("<I", blob, off)[0]
    off += 4
    logical_length, stored_length = struct.unpack_from("<II", blob, off)
    off += 8

    if off != PAYLOAD_OFFSET:
        raise EnvelopeError(f"unexpected payload offset: {off}")
    if inner_version != EXPECTED_INNER_VERSION:
        raise EnvelopeError(f"unsupported inner version: {inner_version}")
    if stored_length < logical_length:
        raise EnvelopeError("stored length smaller than logical length")
    if len(blob) != PAYLOAD_OFFSET + stored_length:
        raise EnvelopeError("character blob size does not match stored length")

    expected = align8(logical_length) + 8
    payload = blob[PAYLOAD_OFFSET:]
    return CharacterEnvelope(
        file_sha256=file_sha256,
        outer_version=int(outer_version),
        magic=MAGIC.decode("ascii"),
        kind=KIND.decode("ascii"),
        guid_hex=guid.hex(),
        inner_version=inner_version,
        logical_length=logical_length,
        stored_length=stored_length,
        payload_offset=PAYLOAD_OFFSET,
        align8_plus8_expected=expected,
        align8_plus8_holds=(stored_length == expected),
        tail_length=stored_length - logical_length,
        payload_sha256=hashlib.sha256(payload).hexdigest(),
    )


def parse_csmc_file(path: str | Path) -> CharacterEnvelope:
    p = Path(path)
    file_bytes = p.read_bytes()
    if not file_bytes.startswith(b"SQLite format 3\x00"):
        raise EnvelopeError("not an SQLite 3 container")

    con = sqlite3.connect(str(p))
    try:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        if "character" not in tables:
            raise EnvelopeError("character table missing")
        rows = con.execute("SELECT version, character FROM character").fetchall()
        if len(rows) != 1:
            raise EnvelopeError(f"expected exactly one character row, got {len(rows)}")
        outer_version, blob = rows[0]
        if not isinstance(blob, (bytes, bytearray)):
            raise EnvelopeError("character payload is not a BLOB")
    finally:
        con.close()

    return parse_character_blob(
        bytes(blob),
        file_sha256=hashlib.sha256(file_bytes).hexdigest(),
        outer_version=int(outer_version),
    )
