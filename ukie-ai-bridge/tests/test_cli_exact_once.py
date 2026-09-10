import argparse
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge import cli


class CliExactOnceTests(unittest.TestCase):
    def test_local_analyze_replay_does_not_call_executor_twice(self):
        with tempfile.TemporaryDirectory() as temp:
            state_root = pathlib.Path(temp) / "state"
            workspace = pathlib.Path(temp) / "workspace"
            args = argparse.Namespace(
                job=str(ROOT / "fixtures" / "job_analyze_blend.valid.json"),
                input=str(pathlib.Path(temp) / "unused.blend"),
                workspace=str(workspace),
                state_root=str(state_root),
            )
            fake_result = {
                "status": "LOCAL_SAVED",
                "job_id": "BRIDGE_TEST_000001",
                "artifact_validation": {"status": "PASS"},
            }
            with mock.patch.object(cli.bridge_main, "run_local_analyze", return_value=fake_result) as executor:
                first = cli.cmd_local_analyze_once(args)
                second = cli.cmd_local_analyze_once(args)

            self.assertEqual(first, 0)
            self.assertEqual(second, 0)
            self.assertEqual(executor.call_count, 1)

    def test_cli_validate_retry(self):
        code = cli.main(["validate-retry", str(ROOT / "fixtures" / "retry.valid.json")])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
