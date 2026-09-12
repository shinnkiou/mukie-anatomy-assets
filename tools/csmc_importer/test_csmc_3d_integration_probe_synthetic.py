from __future__ import annotations

import hashlib
import sqlite3
import struct
import tempfile
from pathlib import Path

from csmc_3d_integration_probe import inspect_clip, write_outputs


def lp(b: bytes) -> bytes:
    return struct.pack("<I", len(b)) + b


def c3d(kind: bytes, guid_byte: int, payload: bytes) -> bytes:
    logical = len(payload)
    stored = ((logical + 7) // 8) * 8 + 8
    body = payload + b"\0" * (stored - len(payload))
    return (
        lp(b"CLIP_STUDIO_3D_DATA2")
        + lp(kind)
        + bytes([guid_byte]) * 16
        + struct.pack("<III", 2, logical, stored)
        + body
    )


def exta(ext_id: str, blob: bytes) -> bytes:
    b = ext_id.encode("ascii")
    return len(b).to_bytes(8, "big") + b + len(blob).to_bytes(8, "big") + blob


def chunk(tag: bytes, payload: bytes) -> bytes:
    return tag + len(payload).to_bytes(8, "big") + payload


def build_sqlite(path: Path, refs: dict[str, str]) -> None:
    con = sqlite3.connect(str(path))
    try:
        con.executescript(
            """
            create table Canvas3DModelLoader(_PW_ID integer primary key, ModelData blob);
            create table Manager3DOd(_PW_ID integer primary key, SceneData blob);
            create table ModelData3D(_PW_ID integer primary key, Layer3DModelData blob);
            create table Canvas3DModelBank(_PW_ID integer primary key, BankData blob);
            create table ModelInfo3D(
              _PW_ID integer primary key,
              ModelNodeInfoCount integer,
              ModelNodeInfoFirstIndex integer,
              DessindollShapeInfo blob,
              DessindollBoneInfo blob,
              PartsBody blob,
              PartsMaterial blob,
              PartsLayout blob,
              PartsTransform blob
            );
            create table ModelNodeInfo3D(
              _PW_ID integer primary key,
              NodeName text,
              NodeRotationR real,
              NodeRotationVX real,
              NodeRotationVY real,
              NodeRotationVZ real,
              NodeTranslationX real,
              NodeTranslationY real,
              NodeTranslationZ real,
              NodeScaleX real,
              NodeScaleY real,
              NodeScaleZ real,
              NextIndex integer
            );
            """
        )
        con.execute("insert into Canvas3DModelLoader values(1, ?)", (refs["model"].encode(),))
        con.execute("insert into Manager3DOd values(1, ?)", (refs["scene"].encode(),))
        con.execute("insert into ModelData3D values(1, ?)", (refs["layer"].encode(),))
        con.execute("insert into Canvas3DModelBank values(1, ?)", (refs["bank"].encode(),))
        con.execute(
            "insert into ModelInfo3D values(1,1,10,?,?,?,?,?,?)",
            (b"shape", b"bone", b"body", b"mat", b"layout", b"transform"),
        )
        con.execute(
            "insert into ModelNodeInfo3D values(10,'BP3D_TEST_ROOT',1,0,0,0,0,0,0,1,1,1,-1)"
        )
        con.commit()
    finally:
        con.close()


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        refs = {
            "model": "extrnlidMODEL",
            "scene": "extrnlidSCENE",
            "layer": "extrnlidLAYER",
            "bank": "extrnlidBANK",
        }
        db = root / "clip.sqlite"
        build_sqlite(db, refs)
        sql_blob = db.read_bytes()

        blobs = {
            refs["model"]: c3d(b"catalog_character", 0x11, b"MODEL" * 11),
            refs["scene"]: c3d(b"scene", 0x22, b"SCENE" * 9),
            refs["layer"]: c3d(b"layer3d", 0x33, b"LAYER" * 7),
            refs["bank"]: c3d(b"bank", 0x44, b"BANK" * 13),
        }

        raw = b"CSFCHUNK" + b"\0" * 16
        for ref, blob in blobs.items():
            raw += chunk(b"CHNKExta", exta(ref, blob))
        raw += chunk(b"CHNKSQLi", sql_blob)
        raw += chunk(b"CHNKFoot", b"")

        clip = root / "synthetic.clip"
        clip.write_bytes(raw)
        result = inspect_clip(clip)

        assert result["status"]["external_payloads"] == 4
        assert result["status"]["reference_edges"] == 4
        assert result["status"]["resolved_references"] == 4
        assert result["status"]["unresolved_references"] == 0
        assert result["sqlite_3d_tables"]["focus_tables"]["ModelInfo3D"]["present"] is True
        assert result["sqlite_3d_tables"]["focus_tables"]["ModelNodeInfo3D"]["row_count"] == 1
        assert result["sqlite_3d_tables"]["focus_tables"]["ModelNodeInfo3D"]["rows"][0]["NodeName"] == "BP3D_TEST_ROOT"
        assert result["external_payload_index"][refs["model"]]["c3d"]["kind"] == "catalog_character"
        assert result["external_payload_index"][refs["scene"]]["c3d"]["kind"] == "scene"

        outdir = root / "out"
        write_outputs(result, outdir)
        expected = {
            "CSMC_3D_INTEGRATION_REPORT.json",
            "CSMC_3D_REFERENCE_GRAPH.json",
            "CSMC_EXTERNAL_PAYLOAD_INDEX.json",
            "CSMC_SQLITE_3D_TABLES.json",
            "CSMC_BINARY_REGION_MAP.json",
            "CSMC_PROBE_REPORT.md",
        }
        assert expected == {p.name for p in outdir.iterdir()}

        print("synthetic integration probe PASS")
        print("clip_sha256", hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
