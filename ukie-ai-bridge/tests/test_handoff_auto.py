import json
import pathlib
import tempfile
import unittest
import zipfile
from unittest import mock

from bridge import handoff
from bridge import handoff_auto
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


class AutoHandoffTests(unittest.TestCase):
    def test_auto_detected_drive_creates_private_inbox(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            drive = root / "My Drive"
            drive.mkdir()
            config = root / "config" / "handoff.json"
            discovery = {
                "status": "FOUND",
                "selected": str(drive),
                "candidates": [str(drive)],
                "confidence": "COMMON_LAYOUT",
            }
            with mock.patch.object(handoff_auto, "discover_drive_sync_root", return_value=discovery):
                result = handoff_auto.configure_handoff_auto(config_path=config)
            self.assertEqual(result["target_kind"], handoff_auto.DRIVE_TARGET)
            self.assertTrue(result["drive_sync_candidate"])
            self.assertEqual(pathlib.Path(result["inbox"]).parent, drive.resolve())
            self.assertEqual(pathlib.Path(result["inbox"]).name, handoff.INBOX_NAME)
            self.assertFalse(result["drive_readback_proven"])

    def test_missing_drive_falls_back_without_picker(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            outbox = root / "local-outbox"
            config = root / "config" / "handoff.json"
            discovery = {"status": "NOT_FOUND", "selected": None, "candidates": [], "confidence": "NONE"}
            with mock.patch.object(handoff_auto, "discover_drive_sync_root", return_value=discovery), \
                 mock.patch.object(handoff_auto, "default_local_outbox", return_value=outbox):
                result = handoff_auto.configure_handoff_auto(config_path=config)
            self.assertEqual(result["target_kind"], handoff_auto.LOCAL_TARGET)
            self.assertFalse(result["drive_sync_candidate"])
            self.assertIsNone(result["sync_root"])
            self.assertEqual(pathlib.Path(result["inbox"]), outbox.resolve())
            self.assertTrue(outbox.is_dir())
            self.assertFalse(result["drive_readback_proven"])
            self.assertFalse(result["ready_for_ai"])

    def test_local_fallback_receipt_never_claims_drive_sync(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            bundle = root / "synthetic_acceptance.zip"
            build_bundle(bundle)
            acceptance = acceptance_result_from_bundle(bundle)
            outbox = root / "local-outbox"
            config = root / "config" / "handoff.json"
            discovery = {"status": "NOT_FOUND", "selected": None, "candidates": [], "confidence": "NONE"}
            with mock.patch.object(handoff_auto, "discover_drive_sync_root", return_value=discovery), \
                 mock.patch.object(handoff_auto, "default_local_outbox", return_value=outbox):
                handoff_auto.configure_handoff_auto(config_path=config)
                result = handoff_auto.run_acceptance_and_handoff_auto(
                    root / "work",
                    {"release_key": "unused-by-fixture"},
                    lambda workspace, state_root, release_info: acceptance,
                    config_path=config,
                )
            receipt = result["handoff"]
            self.assertEqual(result["status"], "ACCEPTANCE_LOCAL_OUTBOX_COMPLETE")
            self.assertTrue(receipt["local_outbox_copy_proven"])
            self.assertFalse(receipt["sync_folder_copy_proven"])
            self.assertFalse(receipt["drive_cloud_presence_proven"])
            self.assertFalse(receipt["drive_readback_proven"])
            self.assertFalse(receipt["ready_for_ai"])
            sidecar = json.loads(pathlib.Path(receipt["handoff_json"]).read_text(encoding="utf-8"))
            self.assertFalse(sidecar["sync_folder_copy_proven"])
            self.assertTrue(sidecar["local_outbox_copy_proven"])

    def test_stale_config_is_backed_up_and_recovered(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = root / "config" / "handoff.json"
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({
                "schema_version": handoff.CONFIG_SCHEMA,
                "inbox": str(root / "missing"),
            }), encoding="utf-8")
            outbox = root / "recovered-outbox"
            discovery = {"status": "NOT_FOUND", "selected": None, "candidates": [], "confidence": "NONE"}
            with mock.patch.object(handoff_auto, "discover_drive_sync_root", return_value=discovery), \
                 mock.patch.object(handoff_auto, "default_local_outbox", return_value=outbox):
                result = handoff_auto.ensure_handoff_config_auto(config)
            self.assertEqual(result["target_kind"], handoff_auto.LOCAL_TARGET)
            self.assertTrue(result["stale_config_backup"])
            self.assertTrue(pathlib.Path(result["stale_config_backup"]).is_file())
            self.assertIn("handoff destination is not a directory", result["recovered_from_config_error"])


if __name__ == "__main__":
    unittest.main()
