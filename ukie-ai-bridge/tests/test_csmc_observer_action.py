from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from bridge import csmc_observer_action


class FakeCompleted:
    returncode = 0
    stdout = "P4.1 synthetic complete\n"
    stderr = ""


def write_capture(path: Path, *, accepted: int = 0, hits: int = 3, failures: int = 1, dumped: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    diag = {
        "search_reason": "complete",
        "accepted_count": accepted,
        "magic_hit_count": hits,
        "search_failures": failures,
        "search_seconds": 2.75,
    }
    manifest = {
        "version": "P4.1.0",
        "contains_private_runtime_payload": dumped,
        "automatic_network_upload": False,
    }
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("runtime_memory_diagnostic.json", json.dumps(diag))
        zf.writestr("capture_manifest.json", json.dumps(manifest))


class CsmcObserverActionTests(unittest.TestCase):
    def test_p41_launch_and_zip_detection_are_fixed_and_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sidecar = root / csmc_observer_action.SIDECAR_BASENAME
            sidecar.write_text("# synthetic P4.1", encoding="utf-8")
            capture_root = root / "captures"

            def fake_runner(argv, **kwargs):
                self.assertEqual(
                    argv,
                    [
                        csmc_observer_action.POWERSHELL_EXE,
                        "-NoProfile",
                        "-NonInteractive",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(sidecar.resolve()),
                    ],
                )
                self.assertNotIn("env", kwargs)
                write_capture(capture_root / "CAPTURE_20260912_190000_P4_1.zip", accepted=1, dumped=True)
                return FakeCompleted()

            result = csmc_observer_action.run_capture(
                process_checker=lambda: True,
                runner=fake_runner,
                sidecar=sidecar,
                roots=[capture_root],
            )

            self.assertTrue(result["existing_modeler_session_used"])
            self.assertTrue(result["observer_launch_automated"])
            self.assertTrue(result["zip_detection_automated"])
            self.assertFalse(result["b_q_input_required"])
            self.assertFalse(result["modeler_launch_performed"])
            self.assertFalse(result["model_load_performed"])
            self.assertFalse(result["focus_change_performed"])
            self.assertEqual(result["candidate_count"], 1)
            self.assertEqual(result["magic_hit_count"], 3)
            self.assertTrue(result["payload_dumped"])
            self.assertEqual(result["observer_version"], "P4.1.0")
            self.assertEqual(result["artifact_transfer"], "LOCAL_FIXED_ROOT_ONLY")
            self.assertEqual(result["zip_name"], "CAPTURE_20260912_190000_P4_1.zip")
            self.assertEqual(len(result["zip_sha256"]), 64)

    def test_existing_zip_is_not_reused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sidecar = root / csmc_observer_action.SIDECAR_BASENAME
            sidecar.write_text("# synthetic P4.1", encoding="utf-8")
            capture_root = root / "captures"
            write_capture(capture_root / "CAPTURE_OLD_P4_1.zip")

            with self.assertRaises(csmc_observer_action.CsmcObserverActionError) as cm:
                csmc_observer_action.run_capture(
                    process_checker=lambda: True,
                    runner=lambda *args, **kwargs: FakeCompleted(),
                    sidecar=sidecar,
                    roots=[capture_root],
                )
            self.assertEqual(cm.exception.code, "OBSERVER_ZIP_MISSING")

    def test_modeler_absent_fails_before_observer_launch(self):
        runner = mock.Mock()
        with self.assertRaises(csmc_observer_action.CsmcObserverActionError) as cm:
            csmc_observer_action.run_capture(process_checker=lambda: False, runner=runner)
        self.assertEqual(cm.exception.code, "MODELER_NOT_RUNNING")
        runner.assert_not_called()

    def test_zip_metadata_is_size_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sidecar = root / csmc_observer_action.SIDECAR_BASENAME
            sidecar.write_text("# synthetic P4.1", encoding="utf-8")
            capture_root = root / "captures"

            def fake_runner(argv, **kwargs):
                capture_root.mkdir(parents=True, exist_ok=True)
                p = capture_root / "CAPTURE_BIG_P4_1.zip"
                with zipfile.ZipFile(p, "w") as zf:
                    zf.writestr("runtime_memory_diagnostic.json", "x" * (csmc_observer_action.MAX_METADATA_BYTES + 1))
                    zf.writestr("capture_manifest.json", "{}")
                return FakeCompleted()

            with self.assertRaises(csmc_observer_action.CsmcObserverActionError) as cm:
                csmc_observer_action.run_capture(
                    process_checker=lambda: True,
                    runner=fake_runner,
                    sidecar=sidecar,
                    roots=[capture_root],
                )
            self.assertEqual(cm.exception.code, "OBSERVER_METADATA_TOO_LARGE")


if __name__ == "__main__":
    unittest.main()
