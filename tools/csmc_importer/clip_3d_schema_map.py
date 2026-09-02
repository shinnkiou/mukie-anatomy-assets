from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from collections import defaultdict
from pathlib import Path

CSF_MAGIC = b"CSFCHUNK"
CHNK_SQLI = b"CHNKSQLi"

TYPE_NAMES = {1: "INTEGER", 2: "REAL", 3: "TEXT", 4: "BLOB"}


def chunks(raw: bytes):
    if not raw.startswith(CSF_MAGIC):
        raise ValueError("not a CLIP CSFCHUNK file")
    pos = 24
    while pos + 16 <= len(raw):
        tag = raw[pos:pos + 8]
        size = int.from_bytes(raw[pos + 8:pos + 16], "big")
        start = pos + 16
        end = start + size
        if end > len(raw):
            raise ValueError(f"chunk exceeds file at {pos}")
        yield pos, tag, raw[start:end]
        pos = end
        if tag == b"CHNKFoot":
            break


def extract_sqlite(clip_path: Path) -> bytes:
    for _, tag, payload in chunks(clip_path.read_bytes()):
        if tag == CHNK_SQLI:
            return payload
    raise ValueError("CHNKSQLi not found")


def schema_map(clip_path: Path) -> dict:
    sqlite_bytes = extract_sqlite(clip_path)
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "clip.sqlite"
        db.write_bytes(sqlite_bytes)
        con = sqlite3.connect(db)
        try:
            tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
            if "ParamScheme" not in tables:
                raise ValueError("ParamScheme not found")
            active = {t: con.execute(f'select count(*) from "{t}"').fetchone()[0] for t in tables}
            rows = con.execute(
                "select TableName,LabelName,DataType,Flag,OwnerType,LockType,LockSpecified,LinkTable "
                "from ParamScheme order by TableName,_PW_ID"
            ).fetchall()
        finally:
            con.close()

    grouped = defaultdict(list)
    for table, label, dtype, flag, owner, lock, lock_spec, link in rows:
        name = table or ""
        if not any(k in name.lower() for k in ("3d", "model", "camera", "character")):
            continue
        grouped[name].append({
            "name": label,
            "datatype_code": dtype,
            "datatype": TYPE_NAMES.get(dtype, f"UNKNOWN_{dtype}"),
            "flag": flag,
            "owner_type": owner,
            "lock_type": lock,
            "lock_specified": lock_spec,
            "link_table": link or None,
        })

    out = {
        "clip": str(clip_path),
        "datatype_map": TYPE_NAMES,
        "tables": {},
    }
    for table in sorted(grouped):
        out["tables"][table] = {
            "active_sql_table": table in active,
            "active_row_count": active.get(table),
            "fields": grouped[table],
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Read-only CLIP ParamScheme 3D schema mapper")
    ap.add_argument("clip")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    out = schema_map(Path(args.clip))
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for table, info in out["tables"].items():
            print(f"[{table}] active={info['active_sql_table']} rows={info['active_row_count']}")
            for field in info["fields"]:
                link = f" -> {field['link_table']}" if field['link_table'] else ""
                print(f"  {field['name']}: {field['datatype']}{link}")


if __name__ == "__main__":
    main()
