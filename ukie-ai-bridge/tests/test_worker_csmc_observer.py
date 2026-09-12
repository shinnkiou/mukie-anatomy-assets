from __future__ import annotations

import unittest
from unittest import mock

from bridge import worker_transport_csmc


class WorkerCsmcObserverTests(unittest.TestCase):
    def test_allowlist_adds_only_narrow_csmc_action(self):
        self.assertEqual(worker_transport_csmc.ALLOWED_ACTIONS, frozenset({"device_status", "csmc_observer_capture"}))

    def test_csmc_action_returns_bounded_metadata_only(self):
        job = {"id": "job-1", "lease_owner": "lease-owner-1", "action": "csmc_observer_capture"}
        result_payload = {
            "schema_version": "ukie_csmc_observer_capture_v1",
            "candidate_count": 0,
            "zip_name": "capture.zip",
            "zip_size": 123,
            "zip_sha256": "a" * 64,
            "artifact_transfer": "LOCAL_FIXED_ROOT_ONLY",
        }
        with mock.patch.object(worker_transport_csmc, "_complete", return_value={"status": "COMPLETED"}) as complete:
            result = worker_transport_csmc.execute_claimed_job(job, observer_provider=lambda: result_payload)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(complete.call_args.kwargs["outcome"], "PASS")
        self.assertEqual(complete.call_args.kwargs["result"], result_payload)

    def test_unknown_action_still_fails_closed(self):
        job = {"id": "job-1", "lease_owner": "lease-owner-1", "action": "arbitrary_shell"}
        with mock.patch.object(worker_transport_csmc, "_complete", return_value={"status": "FAILED"}) as complete:
            result = worker_transport_csmc.execute_claimed_job(job)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(complete.call_args.kwargs["error_code"], "WORKER_ACTION_NOT_ALLOWLISTED")

    def test_cloud_job_fields_are_not_forwarded_to_observer_provider(self):
        job = {
            "id": "job-1",
            "lease_owner": "lease-owner-1",
            "action": "csmc_observer_capture",
            "input_refs": {"script_path": "C:/evil.ps1", "output_path": "D:/escape", "keys": "B,Q"},
        }
        provider = mock.Mock(return_value={"schema_version": "ukie_csmc_observer_capture_v1"})
        with mock.patch.object(worker_transport_csmc, "_complete", return_value={"status": "COMPLETED"}):
            worker_transport_csmc.execute_claimed_job(job, observer_provider=provider)
        provider.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
