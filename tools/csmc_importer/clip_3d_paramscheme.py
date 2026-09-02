from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

TYPE_MAP = {
    1: "INTEGER",
    2: "REAL",
    3: "TEXT",
    4: "BLOB",
}

DEFAULT_TABLES = [
    "Manager3D",
    "ModelInfo3D",
    "ModelNodeInfo3D",
    "ModelData3D",
    "DessinDollInfo",
]


def inspect(db_path: str | Path, tables: list[str] | None = None) -> dict:
    p = Path(db_path)
    con = sqlite3.connect(str(p))
    try:
        live_tables = {
            r[0] for r in con.execute(
                "select name from sqlite_master where type='table'"
            )
        }
        if "ParamScheme" not in live_tables:
            raise ValueError("ParamScheme table not found")

        elem = {}
        if "ElemScheme" in live_tables:
            for name, elem_type, max_index in con.execute(
                "select TableName, ElemType, MaxIndex from ElemScheme"
            ):
                elem[name] = {
                    "elem_type": elem_type,
                    "max_index": max_index,
                }

        wanted = tables or DEFAULT_TABLES
        out = {}
        for table in wanted:
            rows = con.execute(
                """
                select LabelName, DataType, Flag, OwnerType, LockType,
                       LockSpecified, LinkTable
                from ParamScheme
                where TableName = ?
                order by _PW_ID
                """,
                (table,),
            ).fetchall()
            out[table] = {
                "exists_as_live_table": table in live_tables,
                "elem_scheme": elem.get(table),
                "fields": [
                    {
                        "name": label,
                        "data_type_code": dtype,
                        "inferred_sql_type": TYPE_MAP.get(dtype, "UNKNOWN"),
                        "flag": flag,
                        "owner_type": owner,
                        "lock_type": lock_type,
                        "lock_specified": lock_specified,
                        "link_table": link or None,
                    }
                    for (
                        label,
                        dtype,
                        flag,
                        owner,
                        lock_type,
                        lock_specified,
                        link,
                    ) in rows
                ],
            }

        project_version = None
        if "Project" in live_tables:
            row = con.execute(
                "select ProjectInternalVersion from Project limit 1"
            ).fetchone()
            if row:
                project_version = row[0]

        return {
            "source": str(p),
            "project_internal_version": project_version,
            "data_type_map": TYPE_MAP,
            "tables": out,
        }
    finally:
        con.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Extract CELSYS 3D semantic field maps from CLIP ParamScheme"
    )
    ap.add_argument("sqlite")
    ap.add_argument("--table", action="append", dest="tables")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = inspect(args.sqlite, args.tables)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
