import json
import pathlib
import tempfile
import unittest

from bridge import cloud_intake
from fixtures.build_synthetic_cloud_triplet import build_triplet, RELEASE_KEY


class CloudDiscoveryTests(unittest.TestCase):
    def test_no_candidates_is_waiting_not_failure(self):
        result = cloud_intake.classify_discovery([])
        self.assertEqual(result["status"], "WAITING_FOR_SYNC")
        self.assertEqual(result["complete_count"], 0)
        self.assertFalse(result["ready_for_ai"])

    def test_complete_triplet_is_grouped(self):
        files = [
            {"id": "z", "name": "UKIE_PHYSICAL_ACCEPTANCE__BRIDGE_P1__PHYSICAL_ACCEPTANCE_1.zip", "size": 100},
            {"id": "s", "name": "UKIE_PHYSICAL_ACCEPTANCE__BRIDGE_P1__PHYSICAL_ACCEPTANCE_1.zip.sha256", "size": 90},
            {"id": "h", "name": "UKIE_PHYSICAL_ACCEPTANCE__BRIDGE_P1__PHYSICAL_ACCEPTANCE_1.zip.handoff.json", "size": 500},
        ]
        result = cloud_intake.classify_discovery(files)
        self.assertEqual(result["complete_count"], 1)
        self.assertEqual(result["ambiguous_count"], 0)
        self.assertEqual(result["incomplete_count"], 0)
        self.assertEqual(result["complete"][0]["status"], "COMPLETE")

    def test_partial_is_ignored(self):
        files = [{"id": "p", "name": "UKIE_PHYSICAL_ACCEPTANCE__BRIDGE_P1__PHYSICAL_ACCEPTANCE_1.zip.partial"}]
        result = cloud_intake.classify_discovery(files)
        self.assertEqual(result["status"], "WAITING_FOR_SYNC")
        self.assertEqual(len(result["ignored"]), 1)

    def test_missing_member_stays_incomplete(self):
        files = [
            {"id": "z", "name": "UKIE_PHYSICAL_ACCEPTANCE__BRIDGE_P1__PHYSICAL_ACCEPTANCE_1.zip"},
            {"id": "h", "name": "UKIE_PHYSICAL_ACCEPTANCE__BRIDGE_P1__PHYSICAL_ACCEPTANCE_1.zip.handoff.json"},
        ]
        result = cloud_intake.classify_discovery(files)
        self.assertEqual(result["incomplete_count"], 1)
        self.assertIn("sha256", result["incomplete"][0]["missing"])

    def test_duplicate_name_is_ambiguous(self):
        base = "UKIE_PHYSICAL_ACCEPTANCE__BRIDGE_P1__PHYSICAL_ACCEPTANCE_1.zip"
        files = [
            {"id": "z1", "name": base},
            {"id": "z2", "name": base},
            {"id": "s", "name": base + ".sha256"},
            {"id": "h", "name": base + ".handoff.json"},
        ]
        result = cloud_intake.classify_discovery(files)
        self.assertEqual(result["ambiguous_count"], 1)
        self.assertEqual(result["complete_count"], 0)


class CloudIntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.triplet = build_triplet(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_synthetic_triplet_validates_only_when_explicit_test_mode(self):
        result = cloud_intake.verify_cloud_intake(
            self.triplet["bundle"],
            self.triplet["sha_sidecar"],
            self.triplet["handoff"],
            expected_release_key=RELEASE_KEY,
            allow_synthetic_test_fixture=True,
        )
        self.assertEqual(result["status"], "CLOUD_INTAKE_LOCAL_VALID")
        self.assertTrue(result["triplet_verified"])
        self.assertFalse(result["drive_readback_proven"])
        self.assertFalse(result["ready_for_ai"])
        self.assertFalse(result["promotion_performed"])

    def test_provider_bound_test_marks_drive_readback_only_with_three_distinct_ids(self):
        result = cloud_intake.verify_cloud_intake(
            self.triplet["bundle"],
            self.triplet["sha_sidecar"],
            self.triplet["handoff"],
            provider_metadata={
                "provider": "GOOGLE_DRIVE",
                "file_ids": {"zip": "drive_zip", "sha256": "drive_sha", "handoff": "drive_json"},
                "fetched_at": "2026-09-10T00:00:03Z",
            },
            expected_release_key=RELEASE_KEY,
            allow_synthetic_test_fixture=True,
        )
        self.assertEqual(result["status"], "DRIVE_READBACK_VERIFIED")
        self.assertTrue(result["cloud_presence_proven"])
        self.assertTrue(result["drive_readback_proven"])
        self.assertFalse(result["ready_for_ai"])

    def test_production_path_rejects_synthetic_acceptance(self):
        with self.assertRaises(cloud_intake.CloudIntakeError):
            cloud_intake.verify_cloud_intake(
                self.triplet["bundle"],
                self.triplet["sha_sidecar"],
                self.triplet["handoff"],
                expected_release_key=RELEASE_KEY,
                allow_synthetic_test_fixture=False,
            )

    def test_sha_mismatch_is_blocked(self):
        pathlib.Path(self.triplet["sha_sidecar"]).write_text("0" * 64 + "  " + self.triplet["base_name"] + "\n", encoding="ascii")
        with self.assertRaises(cloud_intake.CloudIntakeError):
            cloud_intake.verify_cloud_intake(
                self.triplet["bundle"],
                self.triplet["sha_sidecar"],
                self.triplet["handoff"],
                allow_synthetic_test_fixture=True,
            )

    def test_release_mismatch_is_blocked(self):
        with self.assertRaises(cloud_intake.CloudIntakeError):
            cloud_intake.verify_cloud_intake(
                self.triplet["bundle"],
                self.triplet["sha_sidecar"],
                self.triplet["handoff"],
                expected_release_key="BRIDGE_P_OTHER",
                allow_synthetic_test_fixture=True,
            )

    def test_handoff_cannot_preclaim_drive_readback(self):
        handoff = pathlib.Path(self.triplet["handoff"])
        value = json.loads(handoff.read_text(encoding="utf-8"))
        value["drive_readback_proven"] = True
        handoff.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(cloud_intake.CloudIntakeError):
            cloud_intake.verify_cloud_intake(
                self.triplet["bundle"],
                self.triplet["sha_sidecar"],
                self.triplet["handoff"],
                allow_synthetic_test_fixture=True,
            )


if __name__ == "__main__":
    unittest.main()
