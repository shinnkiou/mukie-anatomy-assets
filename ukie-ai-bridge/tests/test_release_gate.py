import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.release_gate import ReleasePromotionError, evaluate_release_promotion


def release(status="DRIVE_VERIFIED"):
    return {
        "release_key": "BRIDGE_TEST_RELEASE",
        "bridge_version": "0.7.1-p0.5.1",
        "status": status,
        "sha256": "a" * 64,
        "rollback_release_key": "BRIDGE_PREVIOUS_RELEASE",
    }


def canary(*, physical=True, synthetic=False, status="VERIFIED"):
    return {
        "canary_id": "BLENDER_CANARY_TEST",
        "release_key": "BRIDGE_TEST_RELEASE",
        "bridge_version": "0.7.1-p0.5.1",
        "status": status,
        "device_key": "WIN_PHYSICAL_TEST",
        "blender_version": "Blender 4.2.23 LTS",
        "bundle_sha256": "b" * 64,
        "drive_file_id": "DRIVE_CANARY_BUNDLE",
        "drive_readback_proven": True,
        "source_unchanged": True,
        "evidence_verification": {
            "schema_version": "ukie_canary_evidence_verification_v2",
            "status": "CANARY_EVIDENCE_VALID",
        },
        "exact_once_verification": {"decision": "LOCAL_SAVED", "executed": True},
        "semantic_verification": {"status": "PASS", "vertices": 8, "polygons": 6},
        "metadata": {
            "physical_windows_blender_test": physical,
            "synthetic_ci_only": synthetic,
        },
    }


def soak(**overrides):
    value = {
        "schema_version": "ukie_release_soak_v1",
        "release_key": "BRIDGE_TEST_RELEASE",
        "status": "PASS",
        "observed_hours": 24,
        "successful_jobs": 3,
        "crash_count": 0,
        "unresolved_high_failures": 0,
        "rollback_path_verified": True,
    }
    value.update(overrides)
    return value


class ReleaseGateTests(unittest.TestCase):
    def test_physical_canary_can_be_eligible_for_canary_pass(self):
        result = evaluate_release_promotion(release(), canary(), target="CANARY_PASS")
        self.assertTrue(result["eligible"])
        self.assertEqual(result["status"], "PROMOTION_ELIGIBLE")
        self.assertFalse(result["auto_update_eligible_after_promotion"])
        self.assertFalse(result["mutation_performed"])

    def test_synthetic_fixture_is_rejected_in_production_mode(self):
        result = evaluate_release_promotion(
            release(), canary(physical=False, synthetic=True), target="CANARY_PASS"
        )
        self.assertFalse(result["eligible"])
        failed = {item["key"] for item in result["failed_checks"]}
        self.assertIn("not_synthetic", failed)
        self.assertIn("physical_provenance", failed)

    def test_synthetic_fixture_can_exercise_test_only_branch(self):
        result = evaluate_release_promotion(
            release(),
            canary(physical=False, synthetic=True),
            target="CANARY_PASS",
            allow_synthetic_test_fixture=True,
        )
        self.assertTrue(result["eligible"])

    def test_missing_drive_readback_blocks(self):
        value = canary()
        value["drive_readback_proven"] = False
        result = evaluate_release_promotion(release(), value, target="CANARY_PASS")
        self.assertFalse(result["eligible"])
        self.assertIn("drive_readback_proven", {item["key"] for item in result["failed_checks"]})

    def test_wrong_blender_version_blocks(self):
        value = canary()
        value["blender_version"] = "Blender 5.2.1"
        result = evaluate_release_promotion(release(), value, target="CANARY_PASS")
        self.assertFalse(result["eligible"])
        self.assertIn("blender_pin", {item["key"] for item in result["failed_checks"]})

    def test_local_pass_only_is_not_enough(self):
        value = canary(status="LOCAL_PASS")
        result = evaluate_release_promotion(release(), value, target="CANARY_PASS")
        self.assertFalse(result["eligible"])
        self.assertIn("canary_status_verified", {item["key"] for item in result["failed_checks"]})

    def test_stable_requires_canary_pass_release_and_soak(self):
        result = evaluate_release_promotion(
            release(status="CANARY_PASS"), canary(), target="STABLE", soak=soak()
        )
        self.assertTrue(result["eligible"])
        self.assertTrue(result["auto_update_eligible_after_promotion"])

    def test_stable_rejects_short_soak_and_crash(self):
        result = evaluate_release_promotion(
            release(status="CANARY_PASS"),
            canary(),
            target="STABLE",
            soak=soak(observed_hours=2, crash_count=1),
        )
        self.assertFalse(result["eligible"])
        failed = {item["key"] for item in result["failed_checks"]}
        self.assertIn("soak_window", failed)
        self.assertIn("crash_count_zero", failed)

    def test_stable_cannot_skip_canary_pass_state(self):
        result = evaluate_release_promotion(release(), canary(), target="STABLE", soak=soak())
        self.assertFalse(result["eligible"])
        self.assertIn("release_already_canary_pass", {item["key"] for item in result["failed_checks"]})

    def test_unknown_target_rejected(self):
        with self.assertRaises(ReleasePromotionError):
            evaluate_release_promotion(release(), canary(), target="STABLE_NOW")


if __name__ == "__main__":
    unittest.main()
