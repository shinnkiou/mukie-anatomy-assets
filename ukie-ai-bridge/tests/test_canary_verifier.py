import hashlib
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.canary_verifier import CanaryVerificationError, verify_canary_bundle


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
    comment = b"UKIE_TEST\x00" + bytes((i * 73) & 255 for i in range(1400))
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"tEXt", comment)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )


def write_bundle(path: pathlib.Path, *, topology=(8, 6), source_tamper=False, traversal=False, png_tamper=False):
    canary_id = "BLENDER_CANARY_TEST"
    job_id = "CANARY_JOB_TEST"
    root = pathlib.PurePosixPath(canary_id)
    source = b"BLENDER_CANARY_SOURCE_BYTES" * 32
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
            "vertices": topology[0],
            "polygons": topology[1],
            "blender_version": "4.2.23 LTS",
        },
        "previews": {"front": True, "side": True},
        "ready_for_ai": False,
    }
    scene = {
        "schema_version": "ukie_scene_report_v1",
        "objects": [{
            "name": "UKIE_CANARY_CUBE",
            "type": "MESH",
            "mesh": {"vertices": topology[0], "polygons": topology[1]},
        }],
    }
    job_manifest = {
        "schema_version": "ukie_job_manifest_v2",
        "job_id": job_id,
        "status": "LOCAL_SAVED",
        "source": {"source_unchanged": True},
        "artifact_validation": {"status": "PASS"},
    }
    front = bytearray(fake_png())
    if png_tamper:
        front[-8] ^= 0x01
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(str(root / "canary_manifest.json"), json.dumps(manifest))
        zf.writestr(str(root / "canary_source.blend"), source + (b"TAMPER" if source_tamper else b""))
        jr = root / "jobs" / job_id
        zf.writestr(str(jr / "manifest.json"), json.dumps(job_manifest))
        zf.writestr(str(jr / "scene_before.json"), json.dumps(scene))
        zf.writestr(str(jr / "preview_front.png"), bytes(front))
        zf.writestr(str(jr / "preview_side.png"), fake_png())
        if traversal:
            zf.writestr("../escape.txt", "bad")


class CanaryVerifierTests(unittest.TestCase):
    def test_valid_bundle_passes_and_optional_readback_hash_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "canary.zip"
            write_bundle(path)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            result = verify_canary_bundle(path, sha)
            self.assertEqual(result["status"], "CANARY_EVIDENCE_VALID")
            self.assertTrue(result["drive_readback_proven"])
            self.assertEqual(result["semantic"]["vertices"], 8)
            self.assertEqual(result["semantic"]["polygons"], 6)
            self.assertGreaterEqual(result["previews"]["front"]["byte_size"], 1024)

    def test_path_traversal_is_rejected_without_extracting(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "canary.zip"
            write_bundle(path, traversal=True)
            with self.assertRaises(CanaryVerificationError):
                verify_canary_bundle(path)

    def test_tampered_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "canary.zip"
            write_bundle(path, source_tamper=True)
            with self.assertRaises(CanaryVerificationError):
                verify_canary_bundle(path)

    def test_topology_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "canary.zip"
            write_bundle(path, topology=(7, 6))
            with self.assertRaises(CanaryVerificationError):
                verify_canary_bundle(path)

    def test_wrong_expected_readback_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "canary.zip"
            write_bundle(path)
            with self.assertRaises(CanaryVerificationError):
                verify_canary_bundle(path, "0" * 64)

    def test_png_crc_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "canary.zip"
            write_bundle(path, png_tamper=True)
            with self.assertRaises(CanaryVerificationError):
                verify_canary_bundle(path)


if __name__ == "__main__":
    unittest.main()
