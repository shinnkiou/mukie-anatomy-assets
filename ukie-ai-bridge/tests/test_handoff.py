import json
import pathlib
import tempfile
import unittest
import zipfile
from unittest import mock

from bridge import handoff
from fixtures.build_synthetic_acceptance_bundle import build_bundle


def acceptance_result_from_bundle(path: pathlib.Path) -> dict:
    with zipfile.ZipFile(path, "r") as zf:
        manifest_name = next(name for name in zf.namelist() if name.endswith("physical_acceptance_manifest.json"))
        value = json.loads(zf.read(manifest_name).decode("utf-8"))
    value["acceptance_bundle"] = {
        "path": str(path),
        "byte_size": path.stat().st_size,
        "sha256": handoff.sha256_file(path),
    }
    return value


class HandoffTests(unittest.TestCase):
    def test_configure_explicit_folder_creates_private_inbox(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config_path = root / "config" / "handoff.json"
            sync = root / "sync"
            sync.mkdir()
            result = handoff.configure_handoff(sync, config_path=config_path, interactive=False)
            self.assertEqual(result["schema_version"], handoff.CONFIG_SCHEMA)
            self.assertTrue(pathlib.Path(result["inbox"]).is_dir())
            self.assertEqual(pathlib.Path(result["inbox"]).name, handoff.INBOX_NAME)
            loaded = handoff.load_handoff_config(config_path)
            self.assertEqual(loaded["inbox"], result["inbox"])
            self.assertFalse(loaded["drive_readback_proven"])

    def test_missing_explicit_destination_is_not_silently_created(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            with self.assertRaises(handoff.HandoffError):
                handoff.configure_handoff(root / "does-not-exist", config_path=root / "handoff.json", interactive=False)

    def test_handoff_is_sha_verified_and_never_claims_cloud_readback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            bundle = root / "synthetic_acceptance.zip"
            build_bundle(bundle)
            acceptance = acceptance_result_from_bundle(bundle)
            sync_root = root / "sync"
            sync_root.mkdir()
            cfg = handoff.configure_handoff(sync_root, config_path=root / "handoff.json", interactive=False)
            result = handoff.handoff_acceptance(
                acceptance,
                config=cfg,
                allow_synthetic_test_fixture=True,
            )
            destination = pathlib.Path(result["local_destination"])
            self.assertTrue(destination.is_file())
            self.assertEqual(handoff.sha256_file(destination), acceptance["acceptance_bundle"]["sha256"])
            self.assertTrue(pathlib.Path(result["sha256_sidecar"]).is_file())
            self.assertTrue(pathlib.Path(result["handoff_json"]).is_file())
            self.assertTrue(result["sync_folder_copy_proven"])
            self.assertFalse(result["drive_cloud_presence_proven"])
            self.assertFalse(result["drive_readback_proven"])
            self.assertFalse(result["ready_for_ai"])

    def test_second_identical_handoff_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            bundle = root / "synthetic_acceptance.zip"
            build_bundle(bundle)
            acceptance = acceptance_result_from_bundle(bundle)
            sync_root = root / "sync"
            sync_root.mkdir()
            cfg = handoff.configure_handoff(sync_root, config_path=root / "handoff.json", interactive=False)
            first = handoff.handoff_acceptance(acceptance, config=cfg, allow_synthetic_test_fixture=True)
            second = handoff.handoff_acceptance(acceptance, config=cfg, allow_synthetic_test_fixture=True)
            self.assertEqual(first["local_destination"], second["local_destination"])
            self.assertEqual(second["copy_status"], "ALREADY_PRESENT_MATCH")

    def test_collision_with_different_content_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            bundle = root / "synthetic_acceptance.zip"
            build_bundle(bundle)
            acceptance = acceptance_result_from_bundle(bundle)
            sync_root = root / "sync"
            sync_root.mkdir()
            cfg = handoff.configure_handoff(sync_root, config_path=root / "handoff.json", interactive=False)
            first = handoff.handoff_acceptance(acceptance, config=cfg, allow_synthetic_test_fixture=True)
            pathlib.Path(first["local_destination"]).write_bytes(b"different")
            with self.assertRaises(handoff.HandoffError):
                handoff.handoff_acceptance(acceptance, config=cfg, allow_synthetic_test_fixture=True)

    def test_unbound_acceptance_is_blocked_before_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            bundle = root / "synthetic_acceptance.zip"
            build_bundle(bundle)
            acceptance = acceptance_result_from_bundle(bundle)
            acceptance["release_binding_status"] = "UNBOUND"
            sync_root = root / "sync"
            sync_root.mkdir()
            cfg = handoff.configure_handoff(sync_root, config_path=root / "handoff.json", interactive=False)
            with self.assertRaises(handoff.HandoffError):
                handoff.handoff_acceptance(acceptance, config=cfg, allow_synthetic_test_fixture=True)

    def test_orchestrator_resolves_config_before_starting_blender(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            fake_config = {"schema_version": handoff.CONFIG_SCHEMA, "inbox": str(root)}
            fake_acceptance = {"local_core_ready": True}
            fake_handoff = {"status": "LOCAL_HANDOFF_COMPLETE"}
            run = mock.Mock(return_value=fake_acceptance)
            with mock.patch.object(handoff, "ensure_handoff_config", return_value=fake_config) as ensure, \
                 mock.patch.object(handoff, "handoff_acceptance", return_value=fake_handoff) as send:
                result = handoff.run_acceptance_and_handoff(root / "work", {"release_key": "x"}, run)
            ensure.assert_called_once()
            run.assert_called_once()
            send.assert_called_once_with(fake_acceptance, config=fake_config)
            self.assertEqual(result["status"], "ACCEPTANCE_HANDOFF_COMPLETE")
            self.assertFalse(result["drive_readback_proven"])


if __name__ == "__main__":
    unittest.main()
