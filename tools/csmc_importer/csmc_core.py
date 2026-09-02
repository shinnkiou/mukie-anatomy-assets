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
SIGNATURES = {
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg": b"\xff\xd8\xff",
    "zip": b"PK\x03\x04",
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
    entropy_first_1m: float
    signatures: dict[str, int]


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


def _select_blob(con: sqlite3.Connection) -> tuple[str, str, int | None, bytes]:
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    if "character" not in tables:
        raise ValueError("character table not found")

    cols = [r[1] for r in con.execute("pragma table_info(character)")]
    if "catalog_data" in cols:
        blob_col = "catalog_data"
    elif "character" in cols:
        blob_col = "character"
    else:
        raise ValueError(f"unsupported character schema: {cols}")

    row = con.execute(f"select version, {blob_col} from character limit 1").fetchone()
    if not row or row[1] is None:
        raise ValueError("character row/blob missing")
    return "character", blob_col, row[0], bytes(row[1])


def probe(path: str | Path) -> ProbeResult:
    p = Path(path)
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()

    con = sqlite3.connect(str(p))
    try:
        table, blob_col, outer_version, blob = _select_blob(con)
    finally:
        con.close()

    magic, off = _read_lp_string(blob, 0)
    kind, off = _read_lp_string(blob, off)
    if magic != MAGIC:
        raise ValueError(f"unexpected magic: {magic!r}")

    guid = None
    inner_version = logical_size = stored_size = None
    if off + 28 <= len(blob):
        guid = blob[off:off + 16].hex()
        inner_version, logical_size, stored_size = struct.unpack_from("<III", blob, off + 16)

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
        entropy_first_1m=_entropy(sample),
        signatures=signatures,
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
