import unittest
from pathlib import Path
from static_evidence_slice_validator import validate_file

HERE = Path(__file__).resolve().parent


class FullSnapshotEvidenceV1Tests(unittest.TestCase):
    def test_modeldata_confirmed(self):
        r = validate_file(HERE / "CSMC_FULL_SNAPSHOT_EVIDENCE_MODELDATA_V1_20260914.json")
        self.assertTrue(r["accepted"])
        self.assertTrue(r["proof_grade"])
        self.assertFalse(r["closes_requested_edge"])
        self.assertEqual(r["evidence_class"], "EXPLICIT_MODELDATA_LOOKUP")
        self.assertEqual(r["confidence"], "CONFIRMED")

    def test_externalchunk_confirmed(self):
        r = validate_file(HERE / "CSMC_FULL_SNAPSHOT_EVIDENCE_EXTERNALCHUNK_V1_20260914.json")
        self.assertTrue(r["accepted"])
        self.assertTrue(r["proof_grade"])
        self.assertFalse(r["closes_requested_edge"])
        self.assertEqual(r["evidence_class"], "EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP")
        self.assertEqual(r["confidence"], "CONFIRMED")

    def test_canvas_loader_stays_candidate(self):
        r = validate_file(HERE / "CSMC_FULL_SNAPSHOT_EVIDENCE_CANVAS3D_LOADER_CANDIDATE_V1_20260914.json")
        self.assertTrue(r["accepted"])
        self.assertFalse(r["proof_grade"])
        self.assertFalse(r["closes_requested_edge"])
        self.assertEqual(r["evidence_class"], "EXPLICIT_CANVAS3D_LOAD_ENTRY")
        self.assertEqual(r["confidence"], "CANDIDATE")


if __name__ == "__main__":
    unittest.main()
