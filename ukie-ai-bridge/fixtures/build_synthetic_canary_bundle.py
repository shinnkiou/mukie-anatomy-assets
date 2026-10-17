"""Build a non-Blender synthetic canary evidence ZIP for CI verifier tests only."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import zlib
import zipfile


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def fake_png(width=128, height=128):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(((x * 17 + y * 3) & 255, (x * 5 + y * 19) & 255, (x ^ y) & 255, 255))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    comment = b"UKIE_SYNTHETIC_CI_ONLY\x00" + bytes((i * 73) & 255 for i in range(1400))
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"tEXt", comment)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    canary_id = "BLENDER_CANARY_CI_SYNTHETIC"
    job_id = "CANARY_JOB_CI_SYNTHETIC"
    root = pathlib.PurePosixPath(canary_id)
    source = b"UKIE_SYNTHETIC_CANARY_SOURCE" * 64
    source_sha = hashlib.sha256(source).hexdigest()

    manifest = {
        "schema_version": "ukie_blender_canary_v1",
        "canary_id": canary_id,
        "job_id": job_id,
        "status": "CANARY_LOCAL_PASS",
        "source": {
            "name": "canary_source.blend",
            "byte_size": len(source),
            "sha256": source_sha,
            "unchanged_after_analysis": True,
        },
        "exact_once": {"decision": "LOCAL_SAVED", "executed": True},
        "semantic_verification": {
            "status": "PASS",
            "vertices": 8,
            "polygons": 6,
            "blender_version": "4.2.23 LTS / SYNTHETIC_CI_ONLY",
        },
        "previews": {"front": True, "side": True},
        "ready_for_ai": False,
        "synthetic_ci_only": True,
    }
    scene = {
        "schema_version": "ukie_scene_report_v1",
        "objects": [{
            "name": "UKIE_CANARY_CUBE",
            "type": "MESH",
            "mesh": {"vertices": 8, "polygons": 6},
        }],
    }
    job_manifest = {
        "schema_version": "ukie_job_manifest_v2",
        "job_id": job_id,
        "status": "LOCAL_SAVED",
        "source": {"source_unchanged": True},
        "artifact_validation": {"status": "PASS"},
    }

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(str(root / "canary_manifest.json"), json.dumps(manifest))
        zf.writestr(str(root / "canary_source.blend"), source)
        jr = root / "jobs" / job_id
        zf.writestr(str(jr / "manifest.json"), json.dumps(job_manifest))
        zf.writestr(str(jr / "scene_before.json"), json.dumps(scene))
        zf.writestr(str(jr / "preview_front.png"), fake_png())
        zf.writestr(str(jr / "preview_side.png"), fake_png())

    print(hashlib.sha256(output.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
