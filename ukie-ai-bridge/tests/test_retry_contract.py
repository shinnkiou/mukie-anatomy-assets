import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.retry_contract import RetryContractError, validate_retry_contract


class RetryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ROOT / "fixtures" / "retry.valid.json", encoding="utf-8") as handle:
            cls.base = json.load(handle)

    def test_valid_retry_requires_new_job_id(self):
        value = validate_retry_contract(copy.deepcopy(self.base))
        self.assertEqual(value.parent_job_id, "BRIDGE_TEST_000001")
        self.assertEqual(value.new_job_id, "BRIDGE_TEST_000001_RETRY_01")
        self.assertEqual(value.attempt_no, 1)

    def test_reject_same_job_id(self):
        payload = copy.deepcopy(self.base)
        payload["new_job_id"] = payload["parent_job_id"]
        with self.assertRaises(RetryContractError):
            validate_retry_contract(payload)

    def test_reject_arbitrary_shell(self):
        payload = copy.deepcopy(self.base)
        payload["powershell"] = "Write-Host unsafe"
        with self.assertRaises(RetryContractError):
            validate_retry_contract(payload)

    def test_reject_unbounded_attempt(self):
        payload = copy.deepcopy(self.base)
        payload["attempt_no"] = 100000
        with self.assertRaises(RetryContractError):
            validate_retry_contract(payload)


if __name__ == "__main__":
    unittest.main()
