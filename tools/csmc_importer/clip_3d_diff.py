from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import struct
import tempfile
from pathlib import Path

CSF_MAGIC = b"CSFCHUNK"
CHNK_EXTA = b"CHNKExta"
CHNK_SQLI = b"CHNKSQLi"
C3D_MAGIC = b"CLIP_STUDIO_3D_DATA2"


def _chunks(raw: bytes):
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


def _exta(payload: bytes) -> tuple[str, bytes]:
    if len(payload) < 16:
        raise ValueError("truncated CHNKExta")
    n = int.from_bytes(payload[:8], "big")
    p = 8
    ext_id = payload[p:p + n].decode("ascii", "replace")
    p += n
    m = int.from_bytes(payload[p:p + 8], "big")
    p += 8
    blob = payload[p:p + m]
    if len(blob) != m:
        raise ValueError("truncated CHNKExta data")
    return ext_id, blob


def _lp(blob: bytes, off: int) -> tuple[bytes, int]:
    n = struct.unpack_from("<I", blob, off)[0]
    start = off + 4
    end = start + n
    if end > len(blob):
        raise ValueError("truncated LP string")
    return blob[start:end], end


def _c3d_meta(blob: bytes) -> dict:
    out = {
        "size": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
    }
    try:
        magic, off = _lp(blob, 0)
        kind, off = _lp(blob, off)
        out["magic"] = magic.decode("ascii", "replace")
        out["kind"] = kind.decode("ascii", "replace")
        if magic == C3D_MAGIC and off + 28 <= len(blob):
            out["guid_hex"] = blob[off:off + 16].hex()
            ver, logical, stored = struct.unpack_from("<III", blob, off + 16)
            out["inner_version"] = ver
            out["logical_size"] = logical
            out["stored_size"] = stored
            out["payload_offset"] = off + 28
    except Exception as exc:
        out["parse_error"] = str(exc)
    return out


def _read_ref(raw) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    return bytes(raw).decode("ascii", "replace")


def inspect_clip(path: str | Path) -> dict:
    p = Path(path)
    raw = p.read_bytes()
    ext = {}
    sql_blob = None
    for offset, tag, payload in _chunks(raw):
        if tag == CHNK_EXTA:
            ext_id, blob = _exta(payload)
            ext[ext_id] = {"offset": offset, "blob": blob}
        elif tag == CHNK_SQLI:
            sql_blob = payload

    if sql_blob is None:
        raise ValueError("CHNKSQLi not found")

    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "clip.sqlite"
        db.write_bytes(sql_blob)
        con = sqlite3.connect(str(db))
        try:
            model_ref = None
            scene_ref = None
            model_uuid = None
            character_uuid = None
            project_internal_version = None
            camera = None

            tables = {
                r[0] for r in con.execute(
                    "select name from sqlite_master where type='table'"
                )
            }
            if "Canvas3DModelLoader" in tables:
                row = con.execute(
                    "select ModelUuid, ModelData from Canvas3DModelLoader limit 1"
                ).fetchone()
                if row:
                    model_uuid = row[0]
                    model_ref = _read_ref(row[1])

            if "Manager3DOd" in tables:
                row = con.execute(
                    "select SceneData from Manager3DOd limit 1"
                ).fetchone()
                if row:
                    scene_ref = _read_ref(row[0])

            if "CharacterInfo" in tables:
                row = con.execute(
                    "select CharacterUUID from CharacterInfo limit 1"
                ).fetchone()
                if row:
                    character_uuid = row[0]

            if "Project" in tables:
                row = con.execute(
                    "select ProjectInternalVersion from Project limit 1"
                ).fetchone()
                if row:
                    project_internal_version = row[0]

            if "CameraInfo" in tables:
                cols = [r[1] for r in con.execute("pragma table_info(CameraInfo)")]
                row = con.execute("select * from CameraInfo limit 1").fetchone()
                if row:
                    d = dict(zip(cols, row))
                    keep = [
                        "CameraPositionX", "CameraPositionY", "CameraPositionZ",
                        "CameraTargetX", "CameraTargetY", "CameraTargetZ",
                        "CameraUpX", "CameraUpY", "CameraUpZ", "CameraTwist",
                        "FrustumLeft", "FrustumRight", "FrustumTop",
                        "FrustumBottom", "FrustumNear", "FrustumFar",
                        "FrustumOrtho", "ViewportWidth", "ViewportHeight",
                    ]
                    camera = {k: d.get(k) for k in keep}
        finally:
            con.close()

    model_blob = ext.get(model_ref, {}).get("blob") if model_ref else None
    scene_blob = ext.get(scene_ref, {}).get("blob") if scene_ref else None

    return {
        "path": str(p),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "project_internal_version": project_internal_version,
        "model_uuid": model_uuid,
        "character_uuid": character_uuid,
        "model_external_ref": model_ref,
        "scene_external_ref": scene_ref,
        "model_external_offset": ext.get(model_ref, {}).get("offset") if model_ref else None,
        "scene_external_offset": ext.get(scene_ref, {}).get("offset") if scene_ref else None,
        "model": _c3d_meta(model_blob) if model_blob is not None else None,
        "scene": _c3d_meta(scene_blob) if scene_blob is not None else None,
        "camera": camera,
        "_model_blob": model_blob,
        "_scene_blob": scene_blob,
    }


def _diff_bytes(a: bytes, b: bytes, cap: int = 100) -> dict:
    n = min(len(a), len(b))
    ranges = []
    count = 0
    first = None
    i = 0
    while i < n:
        if a[i] == b[i]:
            i += 1
            continue
        if first is None:
            first = i
        start = i
        while i < n and a[i] != b[i]:
            count += 1
            i += 1
        if len(ranges) < cap:
            ranges.append({"start": start, "end_exclusive": i, "length": i - start})
    if len(a) != len(b):
        if first is None:
            first = n
        count += abs(len(a) - len(b))
        if len(ranges) < cap:
            ranges.append({
                "start": n,
                "end_exclusive": max(len(a), len(b)),
                "length": abs(len(a) - len(b)),
                "reason": "length_difference",
            })

    blocks = n // 8
    same_blocks = sum(
        1 for i in range(blocks)
        if a[i * 8:(i + 1) * 8] == b[i * 8:(i + 1) * 8]
    )
    return {
        "exact_equal": a == b,
        "length_a": len(a),
        "length_b": len(b),
        "length_delta_b_minus_a": len(b) - len(a),
        "first_difference": first,
        "different_bytes_including_length_delta": count,
        "aligned_8byte_blocks_compared": blocks,
        "aligned_8byte_blocks_equal": same_blocks,
        "aligned_8byte_equal_fraction": same_blocks / blocks if blocks else None,
        "difference_ranges_first_100": ranges,
    }


def compare(a_path: str | Path, b_path: str | Path) -> dict:
    a = inspect_clip(a_path)
    b = inspect_clip(b_path)
    am = a.pop("_model_blob")
    bm = b.pop("_model_blob")
    ascene = a.pop("_scene_blob")
    bscene = b.pop("_scene_blob")

    return {
        "a": a,
        "b": b,
        "identity_relation": {
            "same_model_uuid": a["model_uuid"] == b["model_uuid"],
            "same_character_uuid": a["character_uuid"] == b["character_uuid"],
            "same_model_guid": (
                a["model"] and b["model"]
                and a["model"].get("guid_hex") == b["model"].get("guid_hex")
            ),
        },
        "camera_equal": a["camera"] == b["camera"],
        "model_diff": _diff_bytes(am or b"", bm or b""),
        "scene_diff": _diff_bytes(ascene or b"", bscene or b""),
    }


def _strip_private(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Read-only differential analyzer for CLIP documents containing 3D model + scene external chunks"
    )
    ap.add_argument("a")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.b:
        result = compare(args.a, args.b)
    else:
        result = _strip_private(inspect_clip(args.a))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
