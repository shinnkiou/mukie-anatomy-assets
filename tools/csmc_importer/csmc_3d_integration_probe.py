from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import struct
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

CSF_MAGIC = b"CSFCHUNK"
CHNK_EXTA = b"CHNKExta"
CHNK_SQLI = b"CHNKSQLi"
CHNK_FOOT = b"CHNKFoot"
C3D_MAGIC = b"CLIP_STUDIO_3D_DATA2"

EXTERNAL_COLUMNS = {
    "Canvas3DModelLoader": ["ModelData"],
    "Manager3DOd": ["SceneData"],
    "ModelData3D": ["Layer3DModelData"],
    "Canvas3DModelBank": ["BankData"],
}

FOCUS_TABLES = {
    "Canvas3DModelLoader",
    "Manager3DOd",
    "ModelData3D",
    "Canvas3DModelBank",
    "ModelInfo3D",
    "ModelNodeInfo3D",
    "CharacterInfo",
    "CameraInfo",
    "LayerObject",
    "CanvasItem",
    "Canvas",
}

MODELINFO_FIELDS = [
    "_PW_ID",
    "ModelNodeInfoCount",
    "ModelNodeInfoFirstIndex",
    "DessindollShapeInfo",
    "DessindollBoneInfo",
    "PartsBody",
    "PartsMaterial",
    "PartsLayout",
    "PartsTransform",
]

MODELNODE_FIELDS = [
    "_PW_ID",
    "NodeName",
    "NodeRotationR",
    "NodeRotationVX",
    "NodeRotationVY",
    "NodeRotationVZ",
    "NodeTranslationX",
    "NodeTranslationY",
    "NodeTranslationZ",
    "NodeScaleX",
    "NodeScaleY",
    "NodeScaleZ",
    "NextIndex",
]


@dataclass
class ChunkInfo:
    offset: int
    tag: str
    payload_size: int
    end_offset: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iter_chunks(raw: bytes) -> Iterable[tuple[int, bytes, bytes]]:
    if not raw.startswith(CSF_MAGIC):
        raise ValueError("not a CLIP CSFCHUNK file")
    pos = 24
    while pos + 16 <= len(raw):
        tag = raw[pos : pos + 8]
        size = int.from_bytes(raw[pos + 8 : pos + 16], "big")
        start = pos + 16
        end = start + size
        if end > len(raw):
            raise ValueError(f"chunk exceeds file at offset {pos}")
        yield pos, tag, raw[start:end]
        pos = end
        if tag == CHNK_FOOT:
            break


def parse_exta(payload: bytes) -> tuple[str, bytes]:
    if len(payload) < 16:
        raise ValueError("truncated CHNKExta")
    n = int.from_bytes(payload[:8], "big")
    p = 8
    if p + n + 8 > len(payload):
        raise ValueError("truncated CHNKExta id")
    ext_id = payload[p : p + n].decode("ascii", "replace")
    p += n
    m = int.from_bytes(payload[p : p + 8], "big")
    p += 8
    blob = payload[p : p + m]
    if len(blob) != m:
        raise ValueError("truncated CHNKExta data")
    return ext_id, blob


def read_lp(blob: bytes, off: int) -> tuple[bytes, int]:
    if off + 4 > len(blob):
        raise ValueError("truncated LP length")
    n = struct.unpack_from("<I", blob, off)[0]
    start = off + 4
    end = start + n
    if end > len(blob):
        raise ValueError("truncated LP value")
    return blob[start:end], end


def c3d_meta(blob: bytes) -> dict[str, Any]:
    out: dict[str, Any] = {
        "size": len(blob),
        "sha256": sha256_bytes(blob),
    }
    try:
        magic, off = read_lp(blob, 0)
        kind, off = read_lp(blob, off)
        out["magic"] = magic.decode("ascii", "replace")
        out["kind"] = kind.decode("ascii", "replace")
        if magic == C3D_MAGIC and off + 28 <= len(blob):
            out["guid_hex"] = blob[off : off + 16].hex()
            version, logical, stored = struct.unpack_from("<III", blob, off + 16)
            out["inner_version"] = version
            out["logical_size"] = logical
            out["stored_size"] = stored
            out["payload_offset"] = off + 28
            out["payload_size_available"] = len(blob) - (off + 28)
            out["stored_size_invariant"] = stored == (((logical + 7) // 8) * 8 + 8)
    except Exception as exc:
        out["parse_error"] = str(exc)
    return out


def normalize_value(v: Any) -> Any:
    if v is None or isinstance(v, (str, int, float)):
        return v
    if isinstance(v, memoryview):
        v = v.tobytes()
    if isinstance(v, (bytes, bytearray)):
        b = bytes(v)
        if b.startswith(b"extrnlid"):
            return {"external_ref": b.decode("ascii", "replace")}
        result: dict[str, Any] = {
            "blob_len": len(b),
            "sha256": sha256_bytes(b),
        }
        if len(b) <= 32:
            result["hex"] = b.hex()
        else:
            result["head_hex_16"] = b[:16].hex()
        return result
    return repr(v)


def read_ref(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, str):
        return v
    if isinstance(v, memoryview):
        v = v.tobytes()
    if isinstance(v, (bytes, bytearray)):
        return bytes(v).decode("ascii", "replace")
    return str(v)


def table_columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in con.execute(f'pragma table_info("{table}")')]


def snapshot_table(
    con: sqlite3.Connection,
    table: str,
    keep: list[str] | None = None,
    limit: int = 1000,
) -> dict[str, Any]:
    cols = table_columns(con, table)
    chosen = [c for c in (keep or cols) if c in cols]
    if not chosen:
        return {"columns": cols, "row_count": 0, "rows": []}
    qcols = ",".join('"' + c.replace('"', '""') + '"' for c in chosen)
    order = ' order by "_PW_ID"' if "_PW_ID" in cols else ""
    count = con.execute(f'select count(*) from "{table}"').fetchone()[0]
    rows = con.execute(f'select {qcols} from "{table}"{order} limit ?', (limit,)).fetchall()
    return {
        "columns": cols,
        "selected_columns": chosen,
        "row_count": count,
        "rows_truncated": count > limit,
        "rows": [
            {c: normalize_value(v) for c, v in zip(chosen, row)}
            for row in rows
        ],
    }


def inspect_sqlite(
    sql_blob: bytes,
    ext_index: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "clip.sqlite"
        db.write_bytes(sql_blob)
        con = sqlite3.connect(str(db))
        try:
            tables = sorted(
                r[0]
                for r in con.execute("select name from sqlite_master where type='table'")
            )
            out: dict[str, Any] = {
                "all_table_count": len(tables),
                "focus_tables": {},
            }
            graph_edges: list[dict[str, Any]] = []

            for table in sorted(FOCUS_TABLES):
                if table not in tables:
                    out["focus_tables"][table] = {
                        "present": False,
                        "row_count": 0,
                    }
                    continue

                keep = None
                if table == "ModelInfo3D":
                    keep = MODELINFO_FIELDS
                elif table == "ModelNodeInfo3D":
                    keep = MODELNODE_FIELDS
                elif table in EXTERNAL_COLUMNS:
                    keep = ["_PW_ID", *EXTERNAL_COLUMNS[table]]
                snap = snapshot_table(con, table, keep=keep)
                snap["present"] = True
                out["focus_tables"][table] = snap

            for table, columns in EXTERNAL_COLUMNS.items():
                if table not in tables:
                    continue
                cols = table_columns(con, table)
                id_col = "_PW_ID" if "_PW_ID" in cols else None
                for col in columns:
                    if col not in cols:
                        continue
                    qcols = f'"{col}"' if id_col is None else f'"{id_col}","{col}"'
                    rows = con.execute(f'select {qcols} from "{table}"').fetchall()
                    for ordinal, row in enumerate(rows):
                        row_id = ordinal if id_col is None else row[0]
                        raw_ref = row[0] if id_col is None else row[1]
                        ref = read_ref(raw_ref)
                        if not ref:
                            continue
                        graph_edges.append(
                            {
                                "table": table,
                                "row_id": row_id,
                                "column": col,
                                "external_ref": ref,
                                "resolved": ref in ext_index,
                                "target": ext_index.get(ref),
                            }
                        )

            return out, graph_edges
        finally:
            con.close()


def inspect_csmc(path: Path) -> dict[str, Any]:
    con = sqlite3.connect(str(path))
    try:
        tables = {
            r[0]
            for r in con.execute("select name from sqlite_master where type='table'")
        }
        candidates = [
            ("character", "character"),
            ("character", "catalog_data"),
            ("catalog_character", "catalog_data"),
        ]
        for table, column in candidates:
            if table not in tables:
                continue
            cols = table_columns(con, table)
            if column not in cols:
                continue
            row = con.execute(f'select "{column}" from "{table}" limit 1').fetchone()
            if row and row[0] is not None:
                blob = bytes(row[0])
                return {
                    "path": str(path),
                    "file_size": path.stat().st_size,
                    "file_sha256": sha256_bytes(path.read_bytes()),
                    "table": table,
                    "blob_column": column,
                    "blob": c3d_meta(blob),
                }
        raise ValueError("no supported CSMC/CS3C character blob found")
    finally:
        con.close()


def inspect_clip(path: Path, csmc_path: Path | None = None) -> dict[str, Any]:
    raw = path.read_bytes()
    ext_index: dict[str, dict[str, Any]] = {}
    chunk_map: list[dict[str, Any]] = []
    sql_blob: bytes | None = None

    for offset, tag, payload in iter_chunks(raw):
        chunk_map.append(
            asdict(
                ChunkInfo(
                    offset=offset,
                    tag=tag.decode("ascii", "replace"),
                    payload_size=len(payload),
                    end_offset=offset + 16 + len(payload),
                )
            )
        )
        if tag == CHNK_EXTA:
            ext_id, blob = parse_exta(payload)
            ext_index[ext_id] = {
                "external_id": ext_id,
                "chunk_offset": offset,
                "blob_size": len(blob),
                "sha256": sha256_bytes(blob),
                "c3d": c3d_meta(blob),
            }
        elif tag == CHNK_SQLI:
            sql_blob = payload

    if sql_blob is None:
        raise ValueError("CHNKSQLi not found")

    sqlite_info, graph_edges = inspect_sqlite(sql_blob, ext_index)
    unresolved = [e for e in graph_edges if not e["resolved"]]
    resolved = [e for e in graph_edges if e["resolved"]]

    csmc_info = inspect_csmc(csmc_path) if csmc_path else None
    comparisons: list[dict[str, Any]] = []
    if csmc_info:
        cmeta = csmc_info["blob"]
        for edge in resolved:
            target = edge.get("target") or {}
            tmeta = target.get("c3d") or {}
            comparisons.append(
                {
                    "external_ref": edge["external_ref"],
                    "table": edge["table"],
                    "column": edge["column"],
                    "same_blob_sha256": target.get("sha256") == cmeta.get("sha256"),
                    "same_guid": bool(tmeta.get("guid_hex"))
                    and tmeta.get("guid_hex") == cmeta.get("guid_hex"),
                    "same_kind": tmeta.get("kind") == cmeta.get("kind"),
                    "size_delta_external_minus_csmc": target.get("blob_size", 0)
                    - cmeta.get("size", 0),
                }
            )

    return {
        "probe_version": "csmc_3d_integration_probe_v0.1",
        "clip": {
            "path": str(path),
            "size": len(raw),
            "sha256": sha256_bytes(raw),
            "sqlite_size": len(sql_blob),
            "sqlite_sha256": sha256_bytes(sql_blob),
        },
        "chunk_map": chunk_map,
        "external_payload_index": ext_index,
        "sqlite_3d_tables": sqlite_info,
        "reference_graph": {
            "edges": graph_edges,
            "resolved_count": len(resolved),
            "unresolved_count": len(unresolved),
        },
        "csmc": csmc_info,
        "comparisons": comparisons,
        "status": {
            "external_payloads": len(ext_index),
            "reference_edges": len(graph_edges),
            "resolved_references": len(resolved),
            "unresolved_references": len(unresolved),
        },
    }


def write_outputs(result: dict[str, Any], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    files = {
        "CSMC_3D_INTEGRATION_REPORT.json": result,
        "CSMC_3D_REFERENCE_GRAPH.json": result["reference_graph"],
        "CSMC_EXTERNAL_PAYLOAD_INDEX.json": result["external_payload_index"],
        "CSMC_SQLITE_3D_TABLES.json": result["sqlite_3d_tables"],
        "CSMC_BINARY_REGION_MAP.json": {"chunks": result["chunk_map"]},
    }
    for name, payload in files.items():
        (outdir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    lines = [
        "# CSMC 3D Integration Probe Report",
        "",
        f"Probe: `{result['probe_version']}`",
        f"CLIP SHA-256: `{result['clip']['sha256']}`",
        f"External payloads: {result['status']['external_payloads']}",
        f"Reference edges: {result['status']['reference_edges']}",
        f"Resolved: {result['status']['resolved_references']}",
        f"Unresolved: {result['status']['unresolved_references']}",
        "",
        "## Live 3D tables",
    ]
    for table, info in sorted(result["sqlite_3d_tables"]["focus_tables"].items()):
        lines.append(
            f"- `{table}`: present={info.get('present', False)} "
            f"rows={info.get('row_count', 0)}"
        )
    lines += ["", "## External references"]
    for edge in result["reference_graph"]["edges"]:
        lines.append(
            f"- `{edge['table']}.{edge['column']}` row={edge['row_id']} -> "
            f"`{edge['external_ref']}` resolved={edge['resolved']}"
        )
    if result.get("csmc"):
        lines += ["", "## CSMC comparison"]
        for comp in result.get("comparisons", []):
            lines.append(
                f"- `{comp['table']}.{comp['column']}` ref=`{comp['external_ref']}` "
                f"same_guid={comp['same_guid']} same_kind={comp['same_kind']} "
                f"same_blob_sha256={comp['same_blob_sha256']} "
                f"size_delta={comp['size_delta_external_minus_csmc']}"
            )
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "This probe records schema/table/row/reference/payload facts. It does not infer that a schema-only field is live, and it does not claim vertex, index, UV, bone, weight, material, or texture semantics unless a later controlled experiment proves them.",
    ]
    (outdir / "CSMC_PROBE_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Read-only CLIP/CSMC 3D integration probe")
    ap.add_argument("clip", type=Path)
    ap.add_argument("--csmc", type=Path)
    ap.add_argument(
        "--outdir",
        type=Path,
        default=Path("CSMC_3D_INTEGRATION_OUTPUT"),
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="also print the combined report to stdout",
    )
    args = ap.parse_args()

    result = inspect_clip(args.clip, args.csmc)
    write_outputs(result, args.outdir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {args.outdir}")
        print(json.dumps(result["status"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
