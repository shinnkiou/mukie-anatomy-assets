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

    def test_local_saved_job_replay_does_not_run_again(self):
        job = validate_job(copy.deepcopy(self.base))
        with tempfile.TemporaryDirectory() as tmp:
            store = BridgeStateStore(tmp)
            first_start = store.mark_started(job)
            self.assertEqual(first_start["decision"], "START")
            store.mark_local_saved(job, {"status": "LOCAL_SAVED", "sha256": "a" * 64})
            replay = store.mark_started(job)
            self.assertEqual(replay["decision"], "REPLAY_NO_EXECUTE")
            self.assertEqual(replay["receipt"]["attempt_count"], 1)
            self.assertEqual(replay["receipt"]["status"], "LOCAL_SAVED")

    def test_completed_job_replay_is_already_completed(self):
        job = validate_job(copy.deepcopy(self.base))
        with tempfile.TemporaryDirectory() as tmp:
            store = BridgeStateStore(tmp)
            store.mark_started(job)
            store.mark_completed(job, {"status": "VERIFIED", "sha256": "a" * 64})
            replay = store.mark_started(job)
            self.assertEqual(replay["decision"], "ALREADY_COMPLETED")
            self.assertEqual(replay["receipt"]["attempt_count"], 1)

    def test_failed_job_duplicate_is_not_silent_retry(self):
        job = validate_job(copy.deepcopy(self.base))
        with tempfile.TemporaryDirectory() as tmp:
            store = BridgeStateStore(tmp)
            store.mark_started(job)
            store.mark_failed(job, {"error_code": "TEST_FAILURE"})
            replay = store.mark_started(job)
            self.assertEqual(replay["decision"], "REPLAY_TERMINAL_FAILURE")
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
            self.assertEqual(payload["schema_version"], "ukie_bridge_state_v2")
            self.assertIn(job.job_id, payload["jobs"])

    def test_v1_state_migrates_without_losing_job_identity(self):
        job = validate_job(copy.deepcopy(self.base))
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            store = BridgeStateStore(root)
            root.mkdir(parents=True, exist_ok=True)
            store.path.write_text(json.dumps({
                "schema_version": "ukie_bridge_state_v1",
                "jobs": {
                    job.job_id: {
                        "identity": store._identity(job),
                        "status": "COMPLETED",
                        "attempt_count": 1,
                        "last_result": {"status": "VERIFIED"},
                    }
                },
                "install_batches": {},
                "tool_registry": {},
            }), encoding="utf-8")
            payload = store.load()
            self.assertEqual(payload["schema_version"], "ukie_bridge_state_v2")
            self.assertEqual(payload["jobs"][job.job_id]["identity"], store._identity(job))


if __name__ == "__main__":
    unittest.main()
