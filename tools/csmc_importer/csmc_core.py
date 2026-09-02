from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import struct
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

MAGIC = b"CLIP_STUDIO_3D_DATA2"
# Use longer byte signatures to reduce false positives inside high-entropy payloads.
# These offsets are still only raw byte-occurrence diagnostics, not proof of an embedded file.
SIGNATURES = {
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg_jfif": b"\xff\xd8\xff\xe0",
    "jpeg_exif": b"\xff\xd8\xff\xe1",
    "zip_local_header": b"PK\x03\x04",
    "fbx_binary": b"Kaydara FBX Binary",
    "gltf": b"glTF",
}


@dataclass
class ProbeResult:
    path: str
    size: int
    sha256: str
    sqlite_table: str
    blob_column: str
    outer_version: int | None
    magic: str
    payload_kind: str
    guid_hex: str | None
    inner_version: int | None
    logical_size: int | None
    stored_size: int | None
    blob_size: int
    payload_offset: int | None
    payload_size_available: int | None
    entropy_first_1m: float
    signatures: dict[str, int]
    signature_note: str


def _read_lp_string(blob: bytes, offset: int) -> tuple[bytes, int]:
    if offset + 4 > len(blob):
        raise ValueError("truncated length-prefixed string")
    n = struct.unpack_from("<I", blob, offset)[0]
    start = offset + 4
    end = start + n
    if end > len(blob):
        raise ValueError("length-prefixed string exceeds blob")
    return blob[start:end], end


def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    c = Counter(data)
    n = len(data)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def _table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in con.execute(f'pragma table_info("{table}")')}


def _select_blob(con: sqlite3.Connection) -> tuple[str, str, int | None, bytes]:
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    candidates = [
        ("character", "catalog_data"),
        ("character", "character"),
        ("catalog_character", "catalog_data"),
    ]
    seen_schemas = {}
    for table, blob_col in candidates:
        if table not in tables:
            continue
        cols = _table_columns(con, table)
        seen_schemas[table] = sorted(cols)
        if blob_col not in cols:
            continue
        version_col = "version" if "version" in cols else None
        select_cols = f'"{blob_col}"' if version_col is None else f'"{version_col}", "{blob_col}"'
        row = con.execute(f'select {select_cols} from "{table}" limit 1').fetchone()
        if not row:
            continue
        if version_col is None:
            outer_version, raw = None, row[0]
        else:
            outer_version, raw = row[0], row[1]
        if raw is None:
            continue
        return table, blob_col, outer_version, bytes(raw)
    raise ValueError(f"unsupported/missing CELSYS character schema: {seen_schemas or sorted(tables)}")


def extract_character_blob(path: str | Path) -> tuple[bytes, str, str, int | None]:
    p = Path(path)
    con = sqlite3.connect(str(p))
    try:
        table, blob_col, outer_version, blob = _select_blob(con)
    finally:
        con.close()
    return blob, table, blob_col, outer_version


def probe(path: str | Path) -> ProbeResult:
    p = Path(path)
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()

    blob, table, blob_col, outer_version = extract_character_blob(p)

    magic, off = _read_lp_string(blob, 0)
    kind, off = _read_lp_string(blob, off)
    if magic != MAGIC:
        raise ValueError(f"unexpected magic: {magic!r}")

    guid = None
    inner_version = logical_size = stored_size = payload_offset = payload_available = None
    if off + 28 <= len(blob):
        guid = blob[off:off + 16].hex()
        inner_version, logical_size, stored_size = struct.unpack_from("<III", blob, off + 16)
        payload_offset = off + 28
        payload_available = len(blob) - payload_offset

    sample = blob[: min(len(blob), 1_000_000)]
    signatures = {name: blob.find(sig) for name, sig in SIGNATURES.items()}

    return ProbeResult(
        path=str(p),
        size=len(raw),
        sha256=sha,
        sqlite_table=table,
        blob_column=blob_col,
        outer_version=outer_version,
        magic=magic.decode("ascii", errors="replace"),
        payload_kind=kind.decode("ascii", errors="replace"),
        guid_hex=guid,
        inner_version=inner_version,
        logical_size=logical_size,
        stored_size=stored_size,
        blob_size=len(blob),
        payload_offset=payload_offset,
        payload_size_available=payload_available,
        entropy_first_1m=_entropy(sample),
        signatures=signatures,
        signature_note="Raw byte offsets only; high-entropy payloads can contain accidental matches. Treat as a lead, not embedded-file proof.",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Read-only CSMC/CS3C diagnostic probe")
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = probe(args.path)
    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        for k, v in asdict(result).items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
