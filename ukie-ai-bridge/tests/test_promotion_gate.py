import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.promotion_gate import evaluate_promotion


FOUNDATION = {
    "windows_ci_pass": True,
    "packaged_exe_selftest_pass": True,
    "drive_package_readback_sha_match": True,
    "rollback_release_key": "BRIDGE_P051_RUN_34480746569",
}


def full_ready():
    return {
        **FOUNDATION,
        "physical_windows_handshake": True,
        "blender_version": "4.2.23",
        "physical_canary_local_pass": True,
        "canary_drive_readback_sha_match": True,
        "canary_evidence_status": "CANARY_EVIDENCE_VALID",
        "canary_source_unchanged": True,
        "preview_front_verified": True,
        "preview_side_verified": True,
        "windows_gpu_detected": True,
        "blender_gpu_detected": True,
        "gpu_workload_pass": True,
        "drive_blender_drive_roundtrip_pass": True,
        "exact_once_replay_test_pass": True,
        "timeout_recovery_test_pass": True,
    }


class PromotionGateTests(unittest.TestCase):
    def test_foundation_evidence_passes_foundation_only(self):
        foundation = evaluate_promotion(FOUNDATION, "FOUNDATION_VERIFIED")
        self.assertEqual(foundation["status"], "PASS")

        canary = evaluate_promotion(FOUNDATION, "CANARY_PASS")
        self.assertEqual(canary["status"], "BLOCKED")
        self.assertIn("physical_windows_handshake", canary["missing_gates"])
        self.assertFalse(canary["auto_update_eligible"])

    def test_ready_for_ai_requires_all_physical_runtime_gates(self):
        evidence = full_ready()
        result = evaluate_promotion(evidence, "READY_FOR_AI")
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["auto_update_eligible"])

        evidence["gpu_workload_pass"] = False
        blocked = evaluate_promotion(evidence, "READY_FOR_AI")
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertIn("gpu_workload", blocked["missing_gates"])

    def test_auto_update_never_inherits_ready_for_ai(self):
        evidence = full_ready()
        result = evaluate_promotion(evidence, "AUTO_UPDATE_ELIGIBLE")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("rollback_test", result["missing_gates"])
        self.assertIn("crash_free_runs", result["missing_gates"])
        self.assertIn("update_signature", result["missing_gates"])
        self.assertIn("human_policy_approval", result["missing_gates"])
        self.assertFalse(result["auto_update_eligible"])

    def test_auto_update_requires_separate_human_policy_and_three_runs(self):
        evidence = {
            **full_ready(),
            "rollback_test_pass": True,
            "crash_free_canary_runs": 3,
            "update_signature_verified": True,
            "human_auto_update_policy_approval": True,
        }
        result = evaluate_promotion(evidence, "AUTO_UPDATE_ELIGIBLE")
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["auto_update_eligible"])

    def test_wrong_blender_version_blocks_physical_promotion(self):
        evidence = full_ready()
        evidence["blender_version"] = "5.2.1"
        result = evaluate_promotion(evidence, "CANARY_PASS")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("blender_pin", result["missing_gates"])


if __name__ == "__main__":
    unittest.main()
