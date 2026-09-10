import copy
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.state_store import BridgeStateStore, StateConflictError
from bridge.validator import validate_job


class StateStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ROOT / "fixtures" / "job_analyze_blend.valid.json", encoding="utf-8") as f:
            cls.base = json.load(f)

    def test_same_job_replay_does_not_create_second_job(self):
        job = validate_job(copy.deepcopy(self.base))
        with tempfile.TemporaryDirectory() as tmp:
            store = BridgeStateStore(tmp)
            first = store.register_job(job)
            second = store.register_job(job)
            self.assertEqual(first["decision"], "NEW_JOB")
            self.assertEqual(second["decision"], "REPLAY_EXISTING")
            self.assertEqual(len(store.snapshot()["jobs"]), 1)

    def test_completed_job_replay_is_already_completed(self):
        job = validate_job(copy.deepcopy(self.base))
        with tempfile.TemporaryDirectory() as tmp:
            store = BridgeStateStore(tmp)
            store.mark_started(job)
            store.mark_completed(job, {"status": "VERIFIED", "sha256": "a" * 64})
            replay = store.mark_started(job)
            self.assertEqual(replay["decision"], "ALREADY_COMPLETED")
            self.assertEqual(replay["receipt"]["attempt_count"], 1)

    def test_same_job_id_with_different_input_is_conflict(self):
        first_payload = copy.deepcopy(self.base)
        second_payload = copy.deepcopy(self.base)
        second_payload["input"]["sha256"] = "f" * 64
        first = validate_job(first_payload)
        second = validate_job(second_payload)
        with tempfile.TemporaryDirectory() as tmp:
            store = BridgeStateStore(tmp)
            store.register_job(first)
            with self.assertRaises(StateConflictError):
                store.register_job(second)

    def test_atomic_state_is_valid_json(self):
        job = validate_job(copy.deepcopy(self.base))
        with tempfile.TemporaryDirectory() as tmp:
            store = BridgeStateStore(tmp)
            store.register_job(job)
            with store.path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["schema_version"], "ukie_bridge_state_v1")
            self.assertIn(job.job_id, payload["jobs"])


if __name__ == "__main__":
    unittest.main()
