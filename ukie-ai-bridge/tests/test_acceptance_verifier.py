import hashlib
import json
import pathlib
import tempfile
import unittest
import zipfile

from bridge.acceptance_verifier import AcceptanceVerificationError, verify_acceptance_bundle
from fixtures.build_synthetic_acceptance_bundle import build_bundle


class AcceptanceVerifierTests(unittest.TestCase):
    def _bundle(self, root: pathlib.Path) -> pathlib.Path:
        path = root / "synthetic_acceptance.zip"
        build_bundle(path)
        return path

    def _rewrite_manifest(self, source: pathlib.Path, destination: pathlib.Path, mutate) -> None:
        with zipfile.ZipFile(source, "r") as src, zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as dst:
            for info in src.infolist():
                data = src.read(info.filename)
                if pathlib.PurePosixPath(info.filename).name == "physical_acceptance_manifest.json":
                    value = json.loads(data.decode("utf-8"))
                    mutate(value)
                    data = json.dumps(value).encode("utf-8")
                dst.writestr(info.filename, data)

    def test_synthetic_fixture_can_exercise_positive_test_only_path(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self._bundle(pathlib.Path(temp))
            result = verify_acceptance_bundle(bundle, allow_synthetic_test_fixture=True)
            self.assertEqual(result["status"], "ACCEPTANCE_EVIDENCE_VALID")
            self.assertTrue(result["core"]["ready"])
            self.assertTrue(result["gpu"]["ready_for_gpu_render"])
            self.assertTrue(result["synthetic_ci_only"])
            self.assertFalse(result["physical_provenance"])
            self.assertFalse(result["drive_readback_proven"])
            self.assertFalse(result["promotion_input_ready"])
            self.assertFalse(result["ready_for_ai"])

    def test_production_mode_rejects_synthetic_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self._bundle(pathlib.Path(temp))
            with self.assertRaises(AcceptanceVerificationError):
                verify_acceptance_bundle(bundle)

    def test_drive_hash_can_be_proven_without_turning_synthetic_physical(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self._bundle(pathlib.Path(temp))
            digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
            result = verify_acceptance_bundle(
                bundle,
                digest,
                "BRIDGE_P09_RUN_99999999999",
                allow_synthetic_test_fixture=True,
            )
            self.assertTrue(result["drive_readback_proven"])
            self.assertFalse(result["physical_provenance"])
            self.assertFalse(result["promotion_input_ready"])

    def test_wrong_drive_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self._bundle(pathlib.Path(temp))
            with self.assertRaises(AcceptanceVerificationError):
                verify_acceptance_bundle(bundle, "0" * 64, allow_synthetic_test_fixture=True)

    def test_release_key_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self._bundle(pathlib.Path(temp))
            with self.assertRaises(AcceptanceVerificationError):
                verify_acceptance_bundle(
                    bundle,
                    expected_release_key="BRIDGE_P09_RUN_OTHER",
                    allow_synthetic_test_fixture=True,
                )

    def test_ready_for_ai_self_promotion_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            bundle = self._bundle(root)
            tampered = root / "tampered.zip"
            self._rewrite_manifest(bundle, tampered, lambda value: value.__setitem__("ready_for_ai", True))
            with self.assertRaises(AcceptanceVerificationError):
                verify_acceptance_bundle(tampered, allow_synthetic_test_fixture=True)

    def test_unbound_release_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            bundle = self._bundle(root)
            tampered = root / "unbound.zip"
            self._rewrite_manifest(bundle, tampered, lambda value: value.__setitem__("release_binding_status", "UNBOUND"))
            with self.assertRaises(AcceptanceVerificationError):
                verify_acceptance_bundle(tampered, allow_synthetic_test_fixture=True)

    def test_nested_canary_hash_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            bundle = self._bundle(root)
            tampered = root / "nested_tampered.zip"
            with zipfile.ZipFile(bundle, "r") as src, zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_DEFLATED) as dst:
                for info in src.infolist():
                    data = src.read(info.filename)
                    if pathlib.PurePosixPath(info.filename).name.startswith("BLENDER_CANARY_") and info.filename.endswith(".zip"):
                        data += b"tamper"
                    dst.writestr(info.filename, data)
            with self.assertRaises(AcceptanceVerificationError):
                verify_acceptance_bundle(tampered, allow_synthetic_test_fixture=True)


if __name__ == "__main__":
    unittest.main()
