#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest

from csmc_importer_lab_m1_acceptance_v2 import EXPECTED_CHECK_IDS, run_acceptance


class ImporterLabM1AcceptanceV2Tests(unittest.TestCase):
    def test_full_20_item_acceptance(self) -> None:
        report = run_acceptance()
        failed = [row for row in report["checks"] if row["status"] != "PASS"]
        failure_detail = json.dumps(failed, ensure_ascii=False, sort_keys=True, indent=2)
        self.assertEqual(20, report["check_count"])
        self.assertEqual(20, report["passed"], failure_detail)
        self.assertEqual(0, report["failed"], failure_detail)
        self.assertEqual("PASS", report["m1_acceptance_v2_status"], failure_detail)
        self.assertTrue(report["private_gen0_eligible"], failure_detail)
        self.assertFalse(report["semantic_promotion"])
        self.assertFalse(report["blender_emit"])
        self.assertFalse(report["runtime_dispatch"])
        observed_ids = tuple(row["id"] for row in report["checks"])
        self.assertEqual(EXPECTED_CHECK_IDS, observed_ids)
        self.assertTrue(all(row["status"] == "PASS" for row in report["checks"]), failure_detail)


if __name__ == "__main__":
    unittest.main(verbosity=2)
