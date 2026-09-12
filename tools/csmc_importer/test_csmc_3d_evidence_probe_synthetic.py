from __future__ import annotations

import hashlib
import sqlite3
import struct
import tempfile
from pathlib import Path

from csmc_3d_evidence_probe import inspect_evidence, write_outputs


def lp(s: bytes) -> bytes:
    return struct.pack("<I", len(s)) + s


def c3d_blob(kind: bytes, guid: bytes, body: bytes) -> bytes:
    logical = len(body)
    stored = ((logical + 7) // 8) * 8 + 8
    padded = body + b"\0" * (stored - len(body))
    return (
        lp(b"CLIP_STUDIO_3D_DATA2")
        + lp(kind)
        + guid
        + struct.pack("<III", 2, logical, stored)
        + padded
    )


def external_chunk(ext_id: str, blob: bytes) -> bytes:
    payload = len(ext_id).to_bytes(8, "big") + ext_id.encode("ascii")
    payload += len(blob).to_bytes(8, "big") + blob
    return b"CHNKExta" + len(payload).to_bytes(8, "big") + payload


def make_sqlite(path: Path, refs: dict[str, str]) -> bytes:
    con = sqlite3.connect(str(path))
    try:
        con.execute(
            "create table ParamScheme (TableName text, LabelName text, DataType integer, Flag integer, OwnerType integer, LockType integer, LockSpecified integer, LinkTable text)"
        )
        for table, fields in {
            "Canvas3DModelLoader": [("ModelData", 4)],
            "Manager3DOd": [("SceneData", 4)],
            "ModelData3D": [("Layer3DModelData", 4)],
            "Canvas3DModelBank": [("BankData", 4)],
            "ModelInfo3D": [
                ("ModelNodeInfoCount", 1),
                ("ModelNodeInfoFirstIndex", 1),
                ("DessindollShapeInfo", 4),
                ("DessindollBoneInfo", 4),
                ("PartsBody", 4),
                ("PartsMaterial", 4),
                ("PartsLayout", 4),
                ("PartsTransform", 4),
            ],
            "ModelNodeInfo3D": [
                ("NodeName", 3),
                ("NodeRotationR", 2),
                ("NodeRotationVX", 2),
                ("NodeRotationVY", 2),
                ("NodeRotationVZ", 2),
                ("NodeTranslationX", 2),
                ("NodeTranslationY", 2),
                ("NodeTranslationZ", 2),
                ("NodeScaleX", 2),
                ("NodeScaleY", 2),
                ("NodeScaleZ", 2),
                ("NextIndex", 1),
            ],
        }.items():
            for label, dtype in fields:
                con.execute(
                    "insert into ParamScheme values (?, ?, ?, 0, 0, 0, 0, null)",
                    (table, label, dtype),
                )

        con.execute('create table Canvas3DModelLoader (_PW_ID integer, ModelData blob)')
        con.execute('create table Manager3DOd (_PW_ID integer, SceneData blob)')
        con.execute('create table ModelData3D (_PW_ID integer, Layer3DModelData blob)')
        con.execute('create table Canvas3DModelBank (_PW_ID integer, BankData blob)')
        con.execute(
            'create table ModelInfo3D (_PW_ID integer, ModelNodeInfoCount integer, ModelNodeInfoFirstIndex integer, DessindollShapeInfo blob, DessindollBoneInfo blob, PartsBody blob, PartsMaterial blob, PartsLayout blob, PartsTransform blob)'
        )
        con.execute(
            'create table ModelNodeInfo3D (_PW_ID integer, NodeName text, NodeRotationR real, NodeRotationVX real, NodeRotationVY real, NodeRotationVZ real, NodeTranslationX real, NodeTranslationY real, NodeTranslationZ real, NodeScaleX real, NodeScaleY real, NodeScaleZ real, NextIndex integer)'
        )

        con.execute("insert into Canvas3DModelLoader values (1, ?)", (refs["model"].encode(),))
        con.execute("insert into Manager3DOd values (1, ?)", (refs["scene"].encode(),))
        con.execute("insert into ModelData3D values (1, ?)", (refs["layer"].encode(),))
        con.execute("insert into Canvas3DModelBank values (1, ?)", (refs["bank"].encode(),))
        con.execute(
            "insert into ModelInfo3D values (10, 1, 20, ?, ?, ?, ?, ?, ?)",
            (b"shape", b"bone", b"body", b"mat", b"layout", b"transform"),
        )
        con.execute(
            "insert into ModelNodeInfo3D values (20, 'BP3D_TEST_ROOT', 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, -1)"
        )
        con.commit()
    finally:
        con.close()
    return path.read_bytes()


def make_clip(path: Path) -> None:
    refs = {
        "model": "extrnlidMODEL",
        "scene": "extrnlidSCENE",
        "layer": "extrnlidLAYER",
        "bank": "extrnlidBANK",
    }
    guid = bytes.fromhex("00112233445566778899aabbccddeeff")
    chunks = [
        external_chunk(refs["model"], c3d_blob(b"catalog_character", guid, b"model-body")),
        external_chunk(refs["scene"], c3d_blob(b"scene", guid, b"scene-body")),
        external_chunk(refs["layer"], c3d_blob(b"layer", guid, b"layer-body")),
        external_chunk(refs["bank"], c3d_blob(b"bank", guid, b"bank-body")),
    ]

    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "db.sqlite"
        sql = make_sqlite(db, refs)
    chunks.append(b"CHNKSQLi" + len(sql).to_bytes(8, "big") + sql)
    chunks.append(b"CHNKFoot" + (0).to_bytes(8, "big"))

    header = b"CSFCHUNK" + b"\0" * 16
    path.write_bytes(header + b"".join(chunks))


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        clip = root / "synthetic.clip"
        out = root / "out"
        make_clip(clip)
        result = inspect_evidence(clip)
        write_outputs(result, out)

        assert result["probe_version"] == "csmc_3d_evidence_probe_v0.2"
        assert result["status"]["external_payloads"] == 4
        assert result["status"]["resolved_external_references"] == 4
        assert result["status"]["unresolved_external_references"] == 0
        assert result["schema_liveness"]["ModelInfo3D"]["state"] == "LIVE_ROWS"
        assert result["schema_liveness"]["ModelNodeInfo3D"]["state"] == "LIVE_ROWS"
        assert result["model_node_chains"][0]["first_index_resolved_by_pw_id"] is True
        assert result["model_node_chains"][0]["resolved_chain_length"] == 1
        assert result["model_node_chains"][0]["chain"][0]["NodeName"] == "BP3D_TEST_ROOT"
        assert result["model_info_blob_summaries"][0]["fields"]["DessindollBoneInfo"]["blob_len"] == 4
        assert (out / "CSMC_3D_EVIDENCE_REPORT.md").exists()
        assert len(list(out.iterdir())) == 7

        digest = hashlib.sha256(clip.read_bytes()).hexdigest()
        assert result["clip"]["sha256"] == digest

    print("synthetic evidence probe PASS")


if __name__ == "__main__":
    main()
