#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from lab import generate_synthetic_candidates, validate_manifest, genotype_hash
from run_m1_acceptance import run_acceptance

class LabAcceptanceTests(unittest.TestCase):
    def test_generator_yields_50_unique_canonical_manifests(self):
        rows = generate_synthetic_candidates(50)
        self.assertEqual(50, len(rows))
        self.assertEqual(50, len({genotype_hash(r) for r in rows}))
        self.assertTrue(all(not validate_manifest(r) for r in rows))

    def test_full_m1_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            report = run_acceptance(Path(td))
            self.assertEqual("PASS", report["m1_status"])
            self.assertEqual(16, report["passed"])
            self.assertTrue(report["m2_eligible"])
            self.assertFalse(report["m2_started"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
