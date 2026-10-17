import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.validator import JobValidationError, validate_job


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ROOT / "fixtures" / "job_analyze_blend.valid.json", encoding="utf-8") as f:
            cls.base = json.load(f)

    def test_valid_analyze_job(self):
        job = validate_job(copy.deepcopy(self.base))
        self.assertEqual(job.action, "analyze_blend")
        self.assertEqual(job.project, "BRIDGE_TEST")
        self.assertEqual(job.original_filename, "テスト立方体.blend")

    def test_reject_arbitrary_powershell(self):
        payload = copy.deepcopy(self.base)
        payload["powershell"] = "Write-Host unsafe"
        with self.assertRaises(JobValidationError):
            validate_job(payload)

    def test_reject_unknown_action(self):
        payload = copy.deepcopy(self.base)
        payload["action"] = "run_any_exe"
        with self.assertRaises(JobValidationError):
            validate_job(payload)

    def test_reject_bad_sha(self):
        payload = copy.deepcopy(self.base)
        payload["input"]["sha256"] = "not-a-sha"
        with self.assertRaises(JobValidationError):
            validate_job(payload)

    def test_reject_unbounded_timeout(self):
        payload = copy.deepcopy(self.base)
        payload["timeout_seconds"] = 999999
        with self.assertRaises(JobValidationError):
            validate_job(payload)


if __name__ == "__main__":
    unittest.main()
