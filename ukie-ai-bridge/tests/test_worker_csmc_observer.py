from __future__ import annotations

import unittest
from unittest import mock

from bridge import worker_transport_csmc


class WorkerCsmcObserverTests(unittest.TestCase):
    def test_allowlist_adds_only_narrow_csmc_action(self):
        self.assertEqual(worker_transport_csmc.ALLOWED_ACTIONS, frozenset({"device_status", "csmc_observer_capture"}))

    def test_canary_transport_is_isolated_from_production(self):
        self.assertNotEqual(worker_transport_csmc.CSMC_CANARY_EDGE_URL, worker_transport_csmc.PRODUCTION_EDGE_URL)
        self.assertTrue(worker_transport_csmc.PRODUCTION_EDGE_URL.endswith("/ukie-worker-transport"))
        self.assertTrue(worker_transport_csmc.CSMC_CANARY_EDGE_URL.endswith("/ukie-worker-transport-csmc-canary"))
        self.assertEqual(worker_transport_csmc.base.EDGE_URL, worker_transport_csmc.CSMC_CANARY_EDGE_URL)

    def test_canary_never_creates_a_new_pairing(self):
        credential = {"device_key": "device-key-123", "device_token": "t" * 64}
        with mock.patch.object(worker_transport_csmc.base, "load_credential", return_value=credential), \
             mock.patch.object(worker_transport_csmc.base, "_request") as request:
            result = worker_transport_csmc.begin_pairing(open_browser=True)
        self.assertEqual(result["status"], "ALREADY_PAIRED")
        self.assertFalse(result["canary_pairing_created"])
        request.assert_not_called()

    def test_missing_existing_pairing_fails_closed(self):
        with mock.patch.object(worker_transport_csmc.base, "load_credential", return_value=None):
            with self.assertRaises(worker_transport_csmc.WorkerTransportError):
                worker_transport_csmc.begin_pairing(open_browser=False)

    def test_heartbeat_sends_only_canary_auth_probe(self):
        credential = {"device_key": "device-key-123", "device_token": "t" * 64}
        with mock.patch.object(worker_transport_csmc.base, "load_credential", return_value=credential), \
             mock.patch.object(worker_transport_csmc.base, "_request", return_value={"ok": True, "status": "CSMC_CANARY_ONLINE"}) as request:
            result = worker_transport_csmc.heartbeat()
        self.assertEqual(result["status"], "CSMC_CANARY_ONLINE")
        self.assertEqual(request.call_args.args[0], {"action": "heartbeat"})
        self.assertEqual(request.call_args.kwargs["device_key"], credential["device_key"])
        self.assertEqual(request.call_args.kwargs["device_token"], credential["device_token"])

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
