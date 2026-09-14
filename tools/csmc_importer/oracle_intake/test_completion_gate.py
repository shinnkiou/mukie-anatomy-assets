import unittest

from completion_gate import validate_physical_completion_gate
from oracle_intake import OracleIntakeRejected


def row(variant_id="M01", **overrides):
    value = {
        "variant_id": variant_id,
        "oracle_result": "LOAD_ACCEPTED",
        "visible_effect": "VISIBLE_MODEL_UNCHANGED",
        "process_survival": "SURVIVED",
        "evidence_strength": "DIRECT_PHYSICAL_OBSERVATION",
        "observed_at": "2026-09-14T18:30:00+09:00",
    }
    value.update(overrides)
    return value


def complete_observation():
    return {"observations": [row(f"M{i:02d}") for i in range(1, 31)]}


class CompletionGateTests(unittest.TestCase):
    def test_complete_direct_observations_pass(self):
        result = validate_physical_completion_gate(
            complete_observation(), {"complete": True}, require_complete=True
        )
        self.assertTrue(result["physical_complete"])
        self.assertEqual(result["unresolved_row_count"], 0)
        self.assertEqual(result["classification"], "PHYSICAL_ORACLE_COMPLETE")

    def test_unknown_load_rejected_for_complete(self):
        obs = complete_observation()
        obs["observations"][0]["oracle_result"] = "UNKNOWN"
        with self.assertRaises(OracleIntakeRejected):
            validate_physical_completion_gate(obs, {"complete": True}, require_complete=True)

    def test_unknown_visible_rejected_for_complete(self):
        obs = complete_observation()
        obs["observations"][0]["visible_effect"] = "UNKNOWN"
        with self.assertRaises(OracleIntakeRejected):
            validate_physical_completion_gate(obs, {"complete": True}, require_complete=True)

    def test_unknown_process_rejected_for_complete(self):
        obs = complete_observation()
        obs["observations"][0]["process_survival"] = "UNKNOWN"
        with self.assertRaises(OracleIntakeRejected):
            validate_physical_completion_gate(obs, {"complete": True}, require_complete=True)

    def test_non_direct_evidence_rejected_for_complete(self):
        obs = complete_observation()
        obs["observations"][0]["evidence_strength"] = "UNKNOWN"
        with self.assertRaises(OracleIntakeRejected):
            validate_physical_completion_gate(obs, {"complete": True}, require_complete=True)

    def test_invalid_timestamp_rejected(self):
        obs = {"observations": [row(observed_at="not-a-time")]}
        with self.assertRaises(OracleIntakeRejected):
            validate_physical_completion_gate(obs, {"complete": False}, require_complete=False)

    def test_naive_timestamp_rejected(self):
        obs = {"observations": [row(observed_at="2026-09-14T18:30:00")]}
        with self.assertRaises(OracleIntakeRejected):
            validate_physical_completion_gate(obs, {"complete": False}, require_complete=False)

    def test_partial_unknown_is_recorded_but_not_complete(self):
        obs = {"observations": [row(oracle_result="UNKNOWN", visible_effect="UNKNOWN")]}
        result = validate_physical_completion_gate(obs, {"complete": False}, require_complete=False)
        self.assertFalse(result["physical_complete"])
        self.assertEqual(result["unresolved_row_count"], 1)
        self.assertEqual(result["classification"], "PHYSICAL_ORACLE_PARTIAL_OR_UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
