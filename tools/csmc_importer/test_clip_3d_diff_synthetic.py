from __future__ import annotations

import importlib.util
import sqlite3
import struct
import tempfile
from pathlib import Path


def lp(b: bytes) -> bytes:
    return struct.pack('<I', len(b)) + b


def c3d(kind: str, guid_hex: str, payload: bytes) -> bytes:
    kind_b = kind.encode('ascii')
    logical = len(payload)
    stored = len(payload)
    return (
        lp(b'CLIP_STUDIO_3D_DATA2')
        + lp(kind_b)
        + bytes.fromhex(guid_hex)
        + struct.pack('<III', 2, logical, stored)
        + payload
    )


def exta(ext_id: str, blob: bytes) -> bytes:
    eid = ext_id.encode('ascii')
    payload = len(eid).to_bytes(8, 'big') + eid + len(blob).to_bytes(8, 'big') + blob
    return b'CHNKExta' + len(payload).to_bytes(8, 'big') + payload


def chunk(tag: bytes, payload: bytes) -> bytes:
    assert len(tag) == 8
    return tag + len(payload).to_bytes(8, 'big') + payload


def make_sqlite(path: Path, model_ref: str, scene_ref: str) -> bytes:
    con = sqlite3.connect(str(path))
    try:
        con.execute('create table Canvas3DModelLoader(ModelUuid text, ModelData blob)')
        con.execute('insert into Canvas3DModelLoader values(?,?)', ('model-uuid-synth', model_ref.encode('ascii')))
        con.execute('create table Manager3DOd(SceneData blob)')
        con.execute('insert into Manager3DOd values(?)', (scene_ref.encode('ascii'),))
        con.execute('create table CharacterInfo(CharacterUUID text)')
        con.execute('insert into CharacterInfo values(?)', ('character-uuid-synth',))
        con.execute('create table Project(ProjectInternalVersion text)')
        con.execute('insert into Project values(?)', ('1.1.0-test',))
        con.execute('''create table CameraInfo(
            CameraPositionX real, CameraPositionY real, CameraPositionZ real,
            CameraTargetX real, CameraTargetY real, CameraTargetZ real,
            CameraUpX real, CameraUpY real, CameraUpZ real, CameraTwist real,
            FrustumLeft real, FrustumRight real, FrustumTop real, FrustumBottom real,
            FrustumNear real, FrustumFar real, FrustumOrtho integer,
            ViewportWidth integer, ViewportHeight integer
        )''')
        con.execute('insert into CameraInfo values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            0.0, 1.0, 2.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0,
            -1.0, 1.0, 1.0, -1.0, 0.1, 1000.0, 0, 640, 480
        ))
        con.commit()
    finally:
        con.close()
    return path.read_bytes()


def build_clip(path: Path, scene_payload: bytes) -> None:
    model_ref = 'extrnlidSYNTHMODEL000000000000000000000001'
    scene_ref = 'extrnlidSYNTHSCENE000000000000000000000001'
    model_blob = c3d(
        'catalog_character',
        '00112233445566778899aabbccddeeff',
        b'MODEL_SYNTHETIC_PAYLOAD_0123456789',
    )
    scene_blob = c3d(
        'scene',
        'ffeeddccbbaa99887766554433221100',
        scene_payload,
    )
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / 'fixture.sqlite'
        sql_blob = make_sqlite(db, model_ref, scene_ref)
    raw = b'CSFCHUNK' + b'\x00' * 16
    raw += exta(model_ref, model_blob)
    raw += exta(scene_ref, scene_blob)
    raw += chunk(b'CHNKSQLi', sql_blob)
    raw += chunk(b'CHNKFoot', b'')
    path.write_bytes(raw)


def main() -> None:
    spec = importlib.util.spec_from_file_location('clip_3d_diff', Path(__file__).with_name('clip_3d_diff.py'))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as td:
        a = Path(td) / 'a.clip'
        b = Path(td) / 'b.clip'
        build_clip(a, b'SCENE_SYNTHETIC_PAYLOAD_AAAAA')
        build_clip(b, b'SCENE_SYNTHETIC_PAYLOAD_AABAA')
        result = mod.compare(a, b)

        assert result['identity_relation']['same_model_uuid'] is True
        assert result['identity_relation']['same_character_uuid'] is True
        assert result['identity_relation']['same_model_guid'] is True
        assert result['camera_equal'] is True
        assert result['model_diff']['exact_equal'] is True
        assert result['scene_diff']['exact_equal'] is False
        assert result['scene_diff']['different_bytes_including_length_delta'] == 1
        assert result['scene_diff']['first_difference'] is not None
        print('PASS synthetic .clip scene-only differential fixture')
        print('scene_first_difference=', result['scene_diff']['first_difference'])
        print('scene_different_bytes=', result['scene_diff']['different_bytes_including_length_delta'])
        print('model_exact_equal=', result['model_diff']['exact_equal'])
        print('camera_equal=', result['camera_equal'])


if __name__ == '__main__':
    main()
