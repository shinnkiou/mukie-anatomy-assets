import copy
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.job_controller import execute_once
from bridge.state_store import BridgeStateStore
from bridge.validator import validate_job


class JobControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ROOT / "fixtures" / "job_analyze_blend.valid.json", encoding="utf-8") as f:
            cls.base = json.load(f)

    def test_duplicate_delivery_calls_executor_only_once(self):
        job = validate_job(copy.deepcopy(self.base))
        calls = {"count": 0}

        def executor():
            calls["count"] += 1
            return {"status": "LOCAL_SAVED", "artifact": "scene_before.json"}

        with tempfile.TemporaryDirectory() as tmp:
            store = BridgeStateStore(tmp)
            first = execute_once(job, store, executor)
            second = execute_once(job, store, executor)

        self.assertTrue(first["executed"])
        self.assertFalse(second["executed"])
        self.assertEqual(second["decision"], "REPLAY_NO_EXECUTE")
        self.assertEqual(calls["count"], 1)

    def test_failed_duplicate_is_not_automatic_retry(self):
        job = validate_job(copy.deepcopy(self.base))
        calls = {"count": 0}

        def executor():
            calls["count"] += 1
            return {"status": "FAILED", "error_code": "TEST_FAIL"}

        with tempfile.TemporaryDirectory() as tmp:
            store = BridgeStateStore(tmp)
            first = execute_once(job, store, executor)
            second = execute_once(job, store, executor)

        self.assertEqual(first["decision"], "FAILED")
        self.assertEqual(second["decision"], "REPLAY_TERMINAL_FAILURE")
        self.assertEqual(calls["count"], 1)

    def test_completed_is_reserved_and_not_repeated(self):
        job = validate_job(copy.deepcopy(self.base))
        calls = {"count": 0}

        def executor():
            calls["count"] += 1
            return {"status": "COMPLETED", "readback_verified": True}

        with tempfile.TemporaryDirectory() as tmp:
            store = BridgeStateStore(tmp)
            first = execute_once(job, store, executor)
            second = execute_once(job, store, executor)

        self.assertEqual(first["decision"], "COMPLETED")
        self.assertEqual(second["decision"], "ALREADY_COMPLETED")
        self.assertEqual(calls["count"], 1)


if __name__ == "__main__":
    unittest.main()
