from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import struct
import tempfile
from pathlib import Path
from typing import Any, Iterable

CSF_MAGIC = b"CSFCHUNK"
CHNK_EXTA = b"CHNKExta"
CHNK_SQLI = b"CHNKSQLi"
CHNK_FOOT = b"CHNKFoot"
C3D_MAGIC = b"CLIP_STUDIO_3D_DATA2"

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

EXTERNAL_COLUMNS = {
    "Canvas3DModelLoader": ["ModelData"],
    "Manager3DOd": ["SceneData"],
    "ModelData3D": ["Layer3DModelData"],
    "Canvas3DModelBank": ["BankData"],
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

PARAM_FIELDS = [
    "TableName",
    "LabelName",
    "DataType",
    "Flag",
    "OwnerType",
    "LockType",
    "LockSpecified",
    "LinkTable",
]

MODELINFO_BLOB_FIELDS = [
    "DessindollShapeInfo",
    "DessindollBoneInfo",
    "PartsBody",
    "PartsMaterial",
    "PartsLayout",
    "PartsTransform",
]

PROBE_VERSION = "csmc_3d_evidence_probe_v0.2"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iter_chunks(raw: bytes) -> Iterable[tuple[int, bytes, bytes]]:
    if not raw.startswith(CSF_MAGIC):
        raise ValueError("not a CLIP CSFCHUNK file")
    pos = 24
    while pos + 16 <= len(raw):
        tag = raw[pos:pos + 8]
        size = int.from_bytes(raw[pos + 8:pos + 16], "big")
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
    ext_id = payload[p:p + n].decode("ascii", "replace")
    p += n
    m = int.from_bytes(payload[p:p + 8], "big")
    p += 8
    blob = payload[p:p + m]
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
            out["guid_hex"] = blob[off:off + 16].hex()
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
        result = {
            "blob_len": len(b),
            "sha256": sha256_bytes(b),
        }
        if len(b) <= 32:
            result["hex"] = b.hex()
        else:
            result["head_hex_16"] = b[:16].hex()
        return result
    return repr(v)


def table_columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in con.execute(f'pragma table_info("{table}")')]


def fetch_rows(con: sqlite3.Connection, table: str, keep: list[str]) -> list[dict[str, Any]]:
    cols = table_columns(con, table)
    chosen = [c for c in keep if c in cols]
    if not chosen:
        return []
    qcols = ",".join('"' + c.replace('"', '""') + '"' for c in chosen)
    order = ' order by "_PW_ID"' if "_PW_ID" in cols else ""
    rows = con.execute(f'select {qcols} from "{table}"{order}').fetchall()
    return [{c: normalize_value(v) for c, v in zip(chosen, row)} for row in rows]


def extract_clip_parts(path: Path):
    raw = path.read_bytes()
    ext_index: dict[str, dict[str, Any]] = {}
    sql_blob = None
    chunk_map = []

    for offset, tag, payload in iter_chunks(raw):
        chunk_map.append({
            "offset": offset,
            "tag": tag.decode("ascii", "replace"),
            "payload_size": len(payload),
            "end_offset": offset + 16 + len(payload),
        })
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
    return raw, sql_blob, ext_index, chunk_map


def param_scheme_snapshot(con: sqlite3.Connection, tables: set[str]) -> dict[str, Any]:
    if "ParamScheme" not in tables:
        return {
            "present": False,
            "row_count": 0,
            "registered_tables": [],
            "focus_fields": {},
        }

    cols = table_columns(con, "ParamScheme")
    chosen = [c for c in PARAM_FIELDS if c in cols]
    count = con.execute('select count(*) from "ParamScheme"').fetchone()[0]
    if "TableName" not in chosen:
        return {
            "present": True,
            "row_count": count,
            "registered_tables": [],
            "focus_fields": {},
            "warning": "ParamScheme exists but TableName is unavailable",
        }

    qcols = ",".join('"' + c.replace('"', '""') + '"' for c in chosen)
    rows = con.execute(f'select {qcols} from "ParamScheme"').fetchall()
    normalized = [{c: normalize_value(v) for c, v in zip(chosen, row)} for row in rows]
    registered = sorted({str(r.get("TableName")) for r in normalized if r.get("TableName")})

    focus_fields: dict[str, list[dict[str, Any]]] = {}
    for table in sorted(FOCUS_TABLES):
        hits = [r for r in normalized if r.get("TableName") == table]
        if hits:
            focus_fields[table] = hits

    return {
        "present": True,
        "row_count": len(rows),
        "registered_tables": registered,
        "focus_fields": focus_fields,
    }


def liveness_snapshot(con: sqlite3.Connection, tables: set[str], param: dict[str, Any]) -> dict[str, Any]:
    registered = set(param.get("registered_tables", []))
    out: dict[str, Any] = {}
    for table in sorted(FOCUS_TABLES):
        sql_present = table in tables
        row_count = con.execute(f'select count(*) from "{table}"').fetchone()[0] if sql_present else 0
        schema_registered = table in registered

        if sql_present and row_count > 0:
            state = "LIVE_ROWS"
        elif sql_present:
            state = "TABLE_EMPTY"
        elif schema_registered:
            state = "SCHEMA_ONLY"
        else:
            state = "ABSENT"

        out[table] = {
            "schema_registered": schema_registered,
            "sql_table_present": sql_present,
            "row_count": row_count,
            "state": state,
        }
    return out


def external_reference_graph(con: sqlite3.Connection, tables: set[str], ext_index: dict[str, Any]) -> list[dict[str, Any]]:
    edges = []
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
                if raw_ref is None:
                    continue
                if isinstance(raw_ref, memoryview):
                    raw_ref = raw_ref.tobytes()
                if isinstance(raw_ref, (bytes, bytearray)):
                    ref = bytes(raw_ref).decode("ascii", "replace")
                else:
                    ref = str(raw_ref)
                edges.append({
                    "table": table,
                    "row_id": row_id,
                    "column": col,
                    "external_ref": ref,
                    "resolved": ref in ext_index,
                    "target": ext_index.get(ref),
                })
    return edges


def build_node_chains(model_rows: list[dict[str, Any]], node_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row.get("_PW_ID"): row for row in node_rows if row.get("_PW_ID") is not None}
    chains = []

    for model in model_rows:
        declared_count = model.get("ModelNodeInfoCount")
        first_index = model.get("ModelNodeInfoFirstIndex")
        current = first_index
        chain = []
        seen = set()
        terminal_reason = "first_index_not_found"

        while current in by_id and current not in seen:
            seen.add(current)
            row = by_id[current]
            chain.append({
                "_PW_ID": row.get("_PW_ID"),
                "NodeName": row.get("NodeName"),
                "NextIndex": row.get("NextIndex"),
                "rotation_candidate": [
                    row.get("NodeRotationR"),
                    row.get("NodeRotationVX"),
                    row.get("NodeRotationVY"),
                    row.get("NodeRotationVZ"),
                ],
                "translation": [
                    row.get("NodeTranslationX"),
                    row.get("NodeTranslationY"),
                    row.get("NodeTranslationZ"),
                ],
                "scale": [
                    row.get("NodeScaleX"),
                    row.get("NodeScaleY"),
                    row.get("NodeScaleZ"),
                ],
            })

            nxt = row.get("NextIndex")
            if nxt in seen:
                terminal_reason = "cycle_detected"
                break
            if nxt not in by_id:
                terminal_reason = "next_index_not_found"
                break
            current = nxt

        chains.append({
            "model_info_id": model.get("_PW_ID"),
            "declared_count": declared_count,
            "first_index": first_index,
            "first_index_resolved_by_pw_id": first_index in by_id,
            "resolved_chain_length": len(chain),
            "length_matches_declared_count": isinstance(declared_count, int) and declared_count == len(chain),
            "terminal_reason": terminal_reason,
            "chain": chain,
        })
    return chains


def inspect_csmc(path: Path) -> dict[str, Any]:
    con = sqlite3.connect(str(path))
    try:
        tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
        candidates = [
            ("character", "character"),
            ("character", "catalog_data"),
            ("catalog_character", "catalog_data"),
        ]
        for table, column in candidates:
            if table not in tables or column not in table_columns(con, table):
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


def inspect_evidence(clip_path: Path, csmc_path: Path | None = None) -> dict[str, Any]:
    raw, sql_blob, ext_index, chunk_map = extract_clip_parts(clip_path)

    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "clip.sqlite"
        db.write_bytes(sql_blob)
        con = sqlite3.connect(str(db))
        try:
            tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
            param = param_scheme_snapshot(con, tables)
            liveness = liveness_snapshot(con, tables, param)
            model_rows = fetch_rows(con, "ModelInfo3D", MODELINFO_FIELDS) if "ModelInfo3D" in tables else []
            node_rows = fetch_rows(con, "ModelNodeInfo3D", MODELNODE_FIELDS) if "ModelNodeInfo3D" in tables else []
            edges = external_reference_graph(con, tables, ext_index)
        finally:
            con.close()

    chains = build_node_chains(model_rows, node_rows)
    blob_summaries = [
        {
            "model_info_id": row.get("_PW_ID"),
            "fields": {name: row.get(name) for name in MODELINFO_BLOB_FIELDS if name in row},
        }
        for row in model_rows
    ]

    csmc_info = inspect_csmc(csmc_path) if csmc_path else None
    comparisons = []
    if csmc_info:
        cmeta = csmc_info["blob"]
        for edge in [e for e in edges if e["resolved"]]:
            target = edge["target"] or {}
            tmeta = target.get("c3d") or {}
            comparisons.append({
                "external_ref": edge["external_ref"],
                "table": edge["table"],
                "column": edge["column"],
                "same_blob_sha256": target.get("sha256") == cmeta.get("sha256"),
                "same_guid": bool(tmeta.get("guid_hex")) and tmeta.get("guid_hex") == cmeta.get("guid_hex"),
                "same_kind": tmeta.get("kind") == cmeta.get("kind"),
                "size_delta_external_minus_csmc": target.get("blob_size", 0) - cmeta.get("size", 0),
            })

    resolved = [e for e in edges if e["resolved"]]
    unresolved = [e for e in edges if not e["resolved"]]

    return {
        "probe_version": PROBE_VERSION,
        "clip": {
            "path": str(clip_path),
            "size": len(raw),
            "sha256": sha256_bytes(raw),
            "sqlite_size": len(sql_blob),
            "sqlite_sha256": sha256_bytes(sql_blob),
        },
        "chunk_map": chunk_map,
        "param_scheme": param,
        "schema_liveness": liveness,
        "model_info_rows": model_rows,
        "model_node_rows": node_rows,
        "model_node_chains": chains,
        "model_info_blob_summaries": blob_summaries,
        "reference_graph": {
            "edges": edges,
            "resolved_count": len(resolved),
            "unresolved_count": len(unresolved),
        },
        "external_payload_index": ext_index,
        "csmc": csmc_info,
        "comparisons": comparisons,
        "status": {
            "live_focus_tables": sorted(k for k, v in liveness.items() if v["state"] == "LIVE_ROWS"),
            "schema_only_focus_tables": sorted(k for k, v in liveness.items() if v["state"] == "SCHEMA_ONLY"),
            "model_info_live_rows": len(model_rows),
            "model_node_live_rows": len(node_rows),
            "node_chain_count": len(chains),
            "fully_resolved_declared_chains": sum(
                1
                for c in chains
                if c["first_index_resolved_by_pw_id"] and c["length_matches_declared_count"]
            ),
            "external_payloads": len(ext_index),
            "resolved_external_references": len(resolved),
            "unresolved_external_references": len(unresolved),
        },
        "interpretation_boundary": (
            "schema_registered, sql_table_present, row_count and external-reference resolution are reported separately. "
            "NodeRotationR/VX/VY/VZ is labelled only as a rotation candidate; quaternion semantics are not claimed here. "
            "A ModelNode chain is followed only when numeric indexes exactly match live ModelNodeInfo3D._PW_ID values."
        ),
    }


def write_outputs(result: dict[str, Any], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "CSMC_3D_EVIDENCE_REPORT.json": result,
        "CSMC_SCHEMA_LIVENESS.json": result["schema_liveness"],
        "CSMC_MODEL_NODE_CHAINS.json": result["model_node_chains"],
        "CSMC_MODELINFO_BLOB_SUMMARIES.json": result["model_info_blob_summaries"],
        "CSMC_3D_REFERENCE_GRAPH.json": result["reference_graph"],
        "CSMC_EXTERNAL_PAYLOAD_INDEX.json": result["external_payload_index"],
    }
    for name, payload in payloads.items():
        (outdir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    lines = [
        "# CSMC 3D Evidence Probe v0.2",
        "",
        f"CLIP SHA-256: `{result['clip']['sha256']}`",
        f"Live focus tables: {', '.join(result['status']['live_focus_tables']) or '(none)'}",
        f"Schema-only focus tables: {', '.join(result['status']['schema_only_focus_tables']) or '(none)'}",
        f"ModelInfo3D live rows: {result['status']['model_info_live_rows']}",
        f"ModelNodeInfo3D live rows: {result['status']['model_node_live_rows']}",
        f"Node chains: {result['status']['node_chain_count']}",
        f"Declared chains resolved by exact _PW_ID: {result['status']['fully_resolved_declared_chains']}",
        f"External refs resolved/unresolved: {result['status']['resolved_external_references']}/{result['status']['unresolved_external_references']}",
        "",
        "## Liveness states",
    ]
    for table, info in sorted(result["schema_liveness"].items()):
        lines.append(
            f"- `{table}`: {info['state']} "
            f"(schema={info['schema_registered']}, table={info['sql_table_present']}, rows={info['row_count']})"
        )
    lines += ["", "## Node chains"]
    for chain in result["model_node_chains"]:
        names = [str(n.get("NodeName")) for n in chain["chain"]]
        lines.append(
            f"- ModelInfo3D {chain['model_info_id']}: first={chain['first_index']} "
            f"declared={chain['declared_count']} resolved={chain['resolved_chain_length']} "
            f"match={chain['length_matches_declared_count']} terminal={chain['terminal_reason']} "
            f"names={names}"
        )
    lines += ["", "## Interpretation boundary", "", result["interpretation_boundary"]]
    (outdir / "CSMC_3D_EVIDENCE_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Read-only CLIP/CSMC schema-liveness / node-chain evidence probe"
    )
    ap.add_argument("clip", type=Path)
    ap.add_argument("--csmc", type=Path)
    ap.add_argument("--outdir", type=Path, default=Path("CSMC_3D_EVIDENCE_OUTPUT"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = inspect_evidence(args.clip, args.csmc)
    write_outputs(result, args.outdir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {args.outdir}")
        print(json.dumps(result["status"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
