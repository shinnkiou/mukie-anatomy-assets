from __future__ import annotations

import argparse
import json
import sqlite3
import struct
from pathlib import Path


def decode_counted_numeric(blob: bytes) -> dict | None:
    if len(blob) < 4:
        return None
    count = int.from_bytes(blob[:4], 'big')
    data = blob[4:]
    if count < 0 or count > 4096:
        return None
    if len(data) == count * 8:
        vals = list(struct.unpack('>' + 'd' * count, data)) if count else []
        return {'count': count, 'encoding': 'be_f64', 'values': vals}
    if len(data) == count * 4:
        vals = list(struct.unpack('>' + 'f' * count, data)) if count else []
        return {'count': count, 'encoding': 'be_f32', 'values': vals}
    return None


def inspect_sqlite(path: str | Path, table_filter: str | None = None) -> dict:
    p = Path(path)
    con = sqlite3.connect(str(p))
    try:
        tables = [r[0] for r in con.execute(
            "select name from sqlite_master where type='table' order by name"
        )]
        if table_filter:
            tables = [t for t in tables if table_filter.lower() in t.lower()]
        out = []
        for table in tables:
            info = con.execute(f'pragma table_info("{table}")').fetchall()
            cols = [r[1] for r in info]
            if not cols:
                continue
            rows = con.execute(f'select * from "{table}"').fetchall()
            for ri, row in enumerate(rows):
                for ci, val in enumerate(row):
                    if not isinstance(val, (bytes, bytearray)):
                        continue
                    decoded = decode_counted_numeric(bytes(val))
                    if decoded is None:
                        continue
                    out.append({
                        'table': table,
                        'row_index': ri,
                        'column': cols[ci],
                        'blob_size': len(val),
                        **decoded,
                    })
        return {'source': str(p), 'matches': out, 'count': len(out)}
    finally:
        con.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description='Detect CELSYS-style counted big-endian numeric vector BLOBs in SQLite'
    )
    ap.add_argument('sqlite')
    ap.add_argument('--table-filter')
    args = ap.parse_args()
    print(json.dumps(inspect_sqlite(args.sqlite, args.table_filter), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
