from __future__ import annotations

import os
import unittest
from unittest import mock

from bridge import worker_credentials, worker_transport


class WorkerCredentialTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "DPAPI is Windows-only")
    def test_dpapi_round_trip(self):
        secret = "p018-test-secret-" + ("x" * 64)
        protected = worker_credentials.protect_secret(secret)
        self.assertNotIn(secret, protected)
        self.assertEqual(worker_credentials.unprotect_secret(protected), secret)

    def test_rejects_weak_secret(self):
        with mock.patch.object(worker_credentials, "protect_secret", return_value="opaque"):
            with self.assertRaises(worker_credentials.WorkerCredentialError):
                worker_credentials.save_credential({}, "short", path=mock.Mock())


class WorkerTransportTests(unittest.TestCase):
    def test_begin_pairing_sends_hash_not_secret(self):
        captured = {}

        def fake_request(payload, **kwargs):
            captured.update(payload)
            return {
                "ok": True,
                "pairing_id": "11111111-1111-1111-1111-111111111111",
                "pairing_code": "123456",
                "expires_at": "2026-09-11T15:00:00Z",
            }

        with mock.patch.object(worker_transport, "load_release_info", return_value={"release_key": "BRIDGE_P018_RUN_1"}), \
             mock.patch.object(worker_transport, "load_credential", return_value=None), \
             mock.patch.object(worker_transport, "device_name", return_value="TEST-PC"), \
             mock.patch.object(worker_transport, "_request", side_effect=fake_request), \
             mock.patch.object(worker_transport, "save_credential") as save:
            result = worker_transport.begin_pairing(open_browser=False)

        self.assertEqual(result["status"], "PAIRING_REQUIRED")
        self.assertEqual(captured["action"], "pair_request")
        self.assertEqual(len(captured["secret_hash"]), 64)
        self.assertNotIn("device_token", captured)
        self.assertTrue(save.called)

    def test_pair_status_binds_device_key_only_after_approval(self):
        credential = {
            "schema_version": "ukie_worker_credential_v1",
            "pairing_id": "pair-1",
            "device_key": None,
            "device_token": "x" * 64,
        }
        with mock.patch.object(worker_transport, "load_credential", return_value=dict(credential)), \
             mock.patch.object(worker_transport, "_request", return_value={"ok": True, "status": "APPROVED", "approved": True, "device_key": "device-key-123", "approved_at": "2026-09-11T14:00:00Z"}), \
             mock.patch.object(worker_transport, "save_credential") as save:
            result = worker_transport.refresh_pairing()
        self.assertEqual(result["status"], "PAIRED")
        self.assertEqual(result["device_key"], "device-key-123")
        self.assertTrue(save.called)

    def test_unknown_cloud_action_fails_closed(self):
        job = {"id": "job-1", "lease_owner": "lease-owner-123", "action": "arbitrary_shell"}
        with mock.patch.object(worker_transport, "_complete", return_value={"status": "FAILED", "job_key": "job-1"}) as complete:
            result = worker_transport.execute_claimed_job(job)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(complete.call_args.kwargs["error_code"], "WORKER_ACTION_NOT_ALLOWLISTED")

    def test_device_status_is_only_executable_action(self):
        job = {"id": "job-1", "lease_owner": "lease-owner-123", "action": "device_status"}
        fake_status = {"schema_version": "ukie_device_status_v1", "platform": {"system": "Windows"}}
        with mock.patch.object(worker_transport, "_complete", return_value={"status": "COMPLETED", "job_key": "job-1"}) as complete:
            result = worker_transport.execute_claimed_job(job, status_provider=lambda: fake_status)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(complete.call_args.kwargs["outcome"], "PASS")
        self.assertEqual(complete.call_args.kwargs["result"], fake_status)

    def test_request_body_has_hard_cap(self):
        with self.assertRaises(worker_transport.WorkerTransportError):
            worker_transport._request({"x": "a" * (70 * 1024)})


if __name__ == "__main__":
    unittest.main()
