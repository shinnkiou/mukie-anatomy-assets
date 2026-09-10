import hashlib
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.canary_verifier import CanaryVerificationError, verify_canary_bundle


def fake_png(width=512, height=512):
    header = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height)
    header += b"\x08\x06\x00\x00\x00" + b"\x00\x00\x00\x00"
    return header + (b"P" * 1200)


def write_bundle(path: pathlib.Path, *, topology=(8, 6), source_tamper=False, traversal=False):
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
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(str(root / "canary_manifest.json"), json.dumps(manifest))
        zf.writestr(str(root / "canary_source.blend"), source + (b"TAMPER" if source_tamper else b""))
        jr = root / "jobs" / job_id
        zf.writestr(str(jr / "manifest.json"), json.dumps(job_manifest))
        zf.writestr(str(jr / "scene_before.json"), json.dumps(scene))
        zf.writestr(str(jr / "preview_front.png"), fake_png())
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


if __name__ == "__main__":
    unittest.main()
