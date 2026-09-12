from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bridge import csmc_observer_action


class FakeCompleted:
    returncode = 0
    stderr = ""

    def __init__(self, stdout: str):
        self.stdout = stdout


class CsmcObserverActionTests(unittest.TestCase):
    def test_one_shot_uses_fixed_sidecar_and_fixed_capture_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sidecar = root / csmc_observer_action.SIDECAR_BASENAME
            sidecar.write_bytes(b"synthetic-sidecar")
            local = root / "localapp"

            def fake_runner(argv, **kwargs):
                capture_root = Path(kwargs["env"]["UKIE_CSMC_OBSERVER_CAPTURE_ROOT"])
                capture_root.mkdir(parents=True, exist_ok=True)
                zip_path = capture_root / "capture.zip"
                zip_path.write_bytes(b"synthetic-zip")
                payload = {
                    "zip_path": str(zip_path),
                    "scan_reason": "complete",
                    "candidate_count": 0,
                    "read_failures": 1,
                    "search_seconds": 2.75,
                    "payload_dumped": False,
                }
                self.assertEqual(argv, [str(sidecar.resolve()), "--oneshot"])
                return FakeCompleted(csmc_observer_action.RESULT_PREFIX + json.dumps(payload) + "\n")

            with mock.patch.dict(os.environ, {"LOCALAPPDATA": str(local)}, clear=False):
                result = csmc_observer_action.run_capture(
                    process_checker=lambda: True,
                    runner=fake_runner,
                    sidecar=sidecar,
                )

            self.assertTrue(result["existing_modeler_session_used"])
            self.assertFalse(result["modeler_launch_performed"])
            self.assertFalse(result["model_load_performed"])
            self.assertFalse(result["focus_change_performed"])
            self.assertEqual(result["candidate_count"], 0)
            self.assertEqual(result["artifact_transfer"], "LOCAL_FIXED_ROOT_ONLY")
            self.assertEqual(result["zip_name"], "capture.zip")
            self.assertEqual(len(result["zip_sha256"]), 64)

    def test_modeler_absent_fails_without_launching_anything(self):
        with self.assertRaises(csmc_observer_action.CsmcObserverActionError) as cm:
            csmc_observer_action.run_capture(process_checker=lambda: False, runner=mock.Mock())
        self.assertEqual(cm.exception.code, "MODELER_NOT_RUNNING")

    def test_sidecar_output_cannot_escape_fixed_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sidecar = root / csmc_observer_action.SIDECAR_BASENAME
            sidecar.write_bytes(b"synthetic-sidecar")
            outside = root / "outside.zip"
            outside.write_bytes(b"outside")

            def fake_runner(argv, **kwargs):
                return FakeCompleted(csmc_observer_action.RESULT_PREFIX + json.dumps({"zip_path": str(outside)}) + "\n")

            with mock.patch.dict(os.environ, {"LOCALAPPDATA": str(root / "localapp")}, clear=False):
                with self.assertRaises(csmc_observer_action.CsmcObserverActionError) as cm:
                    csmc_observer_action.run_capture(
                        process_checker=lambda: True,
                        runner=fake_runner,
                        sidecar=sidecar,
                    )
            self.assertEqual(cm.exception.code, "OBSERVER_OUTPUT_OUTSIDE_FIXED_ROOT")


if __name__ == "__main__":
    unittest.main()
