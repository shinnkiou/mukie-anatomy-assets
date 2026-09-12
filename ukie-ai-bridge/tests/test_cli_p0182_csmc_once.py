from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from bridge import cli_p0182_csmc as cli


class CsmcCanaryOnceCliTests(unittest.TestCase):
    def test_once_reuses_existing_pairing_and_runs_single_cycle(self) -> None:
        pair = {"status": "ALREADY_PAIRED", "device_key": "device-test"}
        result = {"status": "IDLE", "heartbeat": "OK", "worker_version": cli.BRIDGE_VERSION}
        with mock.patch.object(cli.worker_transport, "begin_pairing", return_value=pair) as begin_pairing:
            with mock.patch.object(cli.worker_transport, "run_once", return_value=result) as run_once:
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = cli.main(["once"])
        self.assertEqual(rc, 0)
        begin_pairing.assert_called_once_with(open_browser=False)
        run_once.assert_called_once_with()
        self.assertIn("ALREADY_PAIRED", out.getvalue())
        self.assertIn("IDLE", out.getvalue())

    def test_once_does_not_create_pairing(self) -> None:
        with mock.patch.object(cli.worker_transport, "begin_pairing", return_value={"status": "PAIRING_REQUIRED"}):
            with mock.patch.object(cli.worker_transport, "run_once") as run_once:
                rc = cli.main(["once"])
        self.assertEqual(rc, 2)
        run_once.assert_not_called()

    def test_unknown_command_fails_closed(self) -> None:
        rc = cli.main(["powershell", "anything"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
