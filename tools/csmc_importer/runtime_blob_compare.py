from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import struct
from dataclasses import asdict, dataclass
from pathlib import Path

MAGIC = b"CLIP_STUDIO_3D_DATA2"


@dataclass
class BlobMeta:
    source: str
    container: str
    table: str | None
    column: str | None
    outer_version: int | None
    blob_size: int
    blob_sha256: str
    magic: str | None
    kind: str | None
    guid_hex: str | None
    inner_version: int | None
    logical_size: int | None
    stored_size: int | None
    payload_offset: int | None
    payload_size_available: int | None
    payload_sha256: str | None


def _lp(blob: bytes, off: int) -> tuple[bytes, int]:
    if off + 4 > len(blob):
        raise ValueError("truncated length prefix")
    n = struct.unpack_from("<I", blob, off)[0]
    start, end = off + 4, off + 4 + n
    if end > len(blob):
        raise ValueError("length-prefixed string exceeds blob")
    return blob[start:end], end


def _sqlite_blob(path: Path) -> tuple[bytes, str, str, int | None]:
    con = sqlite3.connect(str(path))
    try:
        tables = {r[0] for r in con.execute(
            "select name from sqlite_master where type='table'"
        )}
        candidates = [
            ("character", "character"),
            ("character", "catalog_data"),
            ("catalog_character", "catalog_data"),
        ]
        for table, col in candidates:
            if table not in tables:
                continue
            cols = {r[1] for r in con.execute(f"pragma table_info({table})")}
            if col not in cols:
                continue
            version_col = "version" if "version" in cols else None
            sql = f"select {version_col + ',' if version_col else ''}{col} from {table} limit 1"
            row = con.execute(sql).fetchone()
            if not row:
                continue
            if version_col:
                version, raw = row[0], row[1]
            else:
                version, raw = None, row[0]
            if raw is not None:
                return bytes(raw), table, col, version
        raise ValueError("no supported CELSYS character BLOB found")
    finally:
        con.close()


def load_blob(path: str | Path) -> tuple[bytes, BlobMeta]:
    p = Path(path)
    raw = p.read_bytes()
    table = col = None
    outer_version = None
    if raw.startswith(b"SQLite format 3\x00"):
        blob, table, col, outer_version = _sqlite_blob(p)
        container = "sqlite"
    else:
        blob = raw
        container = "raw_blob"

    magic = kind = guid = None
    iv = logical = stored = payload_off = payload_avail = None
    payload_sha = None
    try:
        m, off = _lp(blob, 0)
        k, off = _lp(blob, off)
        magic = m.decode("ascii", "replace")
        kind = k.decode("ascii", "replace")
        if m == MAGIC and off + 28 <= len(blob):
            guid = blob[off:off + 16].hex()
            iv, logical, stored = struct.unpack_from("<III", blob, off + 16)
            payload_off = off + 28
            payload_avail = max(0, len(blob) - payload_off)
            payload_sha = hashlib.sha256(blob[payload_off:]).hexdigest()
    except Exception:
        pass

    meta = BlobMeta(
        source=str(p),
        container=container,
        table=table,
        column=col,
        outer_version=outer_version,
        blob_size=len(blob),
        blob_sha256=hashlib.sha256(blob).hexdigest(),
        magic=magic,
        kind=kind,
        guid_hex=guid,
        inner_version=iv,
        logical_size=logical,
        stored_size=stored,
        payload_offset=payload_off,
        payload_size_available=payload_avail,
        payload_sha256=payload_sha,
    )
    return blob, meta


def _ranges(a: bytes, b: bytes, cap: int = 100) -> tuple[list[dict], int]:
    n = min(len(a), len(b))
    out: list[dict] = []
    count = 0
    i = 0
    while i < n:
        if a[i] == b[i]:
            i += 1
            continue
        start = i
        while i < n and a[i] != b[i]:
            count += 1
            i += 1
        if len(out) < cap:
            out.append({"start": start, "end_exclusive": i, "length": i - start})
    count += abs(len(a) - len(b))
    if len(a) != len(b) and len(out) < cap:
        out.append({
            "start": n,
            "end_exclusive": max(len(a), len(b)),
            "length": abs(len(a) - len(b)),
            "reason": "length_difference",
        })
    return out, count


def compare(a_path: str | Path, b_path: str | Path) -> dict:
    a, am = load_blob(a_path)
    b, bm = load_blob(b_path)
    n = min(len(a), len(b))
    first = next((i for i in range(n) if a[i] != b[i]), None)
    if first is None and len(a) != len(b):
        first = n

    ranges, diff_bytes = _ranges(a, b)
    blocks = n // 8
    same_blocks = sum(
        1 for i in range(blocks)
        if a[i * 8:(i + 1) * 8] == b[i * 8:(i + 1) * 8]
    )

    return {
        "a": asdict(am),
        "b": asdict(bm),
        "exact_equal": a == b,
        "common_length": n,
        "length_delta_b_minus_a": len(b) - len(a),
        "first_difference": first,
        "different_bytes_including_length_delta": diff_bytes,
        "aligned_8byte_blocks_compared": blocks,
        "aligned_8byte_blocks_equal": same_blocks,
        "aligned_8byte_equal_fraction": (same_blocks / blocks) if blocks else None,
        "difference_ranges_first_100": ranges,
        "header_relation": {
            "same_magic": am.magic == bm.magic,
            "same_kind": am.kind == bm.kind,
            "same_guid": am.guid_hex == bm.guid_hex,
            "same_inner_version": am.inner_version == bm.inner_version,
            "logical_delta": (
                bm.logical_size - am.logical_size
                if am.logical_size is not None and bm.logical_size is not None else None
            ),
            "stored_delta": (
                bm.stored_size - am.stored_size
                if am.stored_size is not None and bm.stored_size is not None else None
            ),
            "payload_offset_delta": (
                bm.payload_offset - am.payload_offset
                if am.payload_offset is not None and bm.payload_offset is not None else None
            ),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Read-only comparator for saved CSMC/CS3C character BLOBs and Observer runtime BLOB dumps"
    )
    ap.add_argument("a")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.b:
        result = compare(args.a, args.b)
    else:
        _, meta = load_blob(args.a)
        result = asdict(meta)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
