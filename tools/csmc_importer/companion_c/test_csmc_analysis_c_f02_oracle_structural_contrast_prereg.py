from __future__ import annotations

import copy
import unittest

from csmc_analysis_c_f02_oracle_structural_contrast_prereg import (
    DIRECT,
    EXPECTED,
    PROJECTION_SCHEMA,
    RECEIPT_SCHEMA,
    SENTINEL9,
    SOURCE_BATCH_ID,
    SOURCE_MANIFEST_SHA256,
    StructuralContrastRejected,
    analyze_public_projection,
    canonical_sha256,
)


def row(variant: str, load: str = "LOAD_ACCEPTED", visible: str = "VISIBLE_MODEL_UNCHANGED", survival: str = "SURVIVED"):
    offset, region = EXPECTED[variant]
    return {
        "variant_id": variant,
        "source_offset": offset,
        "structural_region": region,
        "variant_file_sha256": "a" * 64,
        "variant_character_blob_sha256": "b" * 64,
        "oracle_result": load,
        "visible_effect": visible,
        "error_class": None,
        "error_text_sha256": None,
        "load_time_ms": 10,
        "affected_visible_component": None,
        "viewport_result_sha256": None,
        "screenshot_sha256": None,
        "process_survival": survival,
        "evidence_strength": DIRECT,
        "observer_session_id": "synthetic-session",
        "observed_at": "2026-09-14T19:00:00+09:00",
        "xor01_verified_from_source_manifest": True,
    }


def packet(rows, physical_complete=False):
    projection = {
        "schema_version": PROJECTION_SCHEMA,
        "source_batch_id": SOURCE_BATCH_ID,
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "observations": rows,
        "semantic_promotion": False,
        "blender_emit": False,
        "diagnostic_only": True,
        "not_semantic_proof": True,
    }
    n = len(rows)
    complete = n == 30 and {r["variant_id"] for r in rows} == set(EXPECTED)
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "source_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "observation_raw_sha256": "c" * 64,
        "public_projection_canonical_sha256": canonical_sha256(projection),
        "validation": {
            "accepted": True,
            "complete": complete,
            "observed_count": n,
            "direct_observation_count": n,
            "unknown_count": 0,
            "semantic_promotion": False,
            "blender_emit": False,
        },
        "physical_completion_gate": {
            "coverage_complete": complete,
            "physical_complete": physical_complete,
            "observed_count": n,
            "direct_observation_count": n,
            "unresolved_row_count": 0,
            "unresolved_rows": [],
        },
        "semantic_promotion": False,
        "blender_emit": False,
        "diagnostic_only": True,
    }
    return projection, receipt


class StructuralContrastPreregTests(unittest.TestCase):
    def test_benign_sentinel9_is_partial_direct_without_flags(self):
        projection, receipt = packet([row(v) for v in SENTINEL9])
        result = analyze_public_projection(projection, receipt)
        self.assertEqual(result["classification"], "STRUCTURAL_CONTRAST_PARTIAL_DIRECT")
        self.assertTrue(result["sentinel9_complete"])
        self.assertEqual(result["preregistered_structural_flags"], [])
        self.assertFalse(result["semantic_promotion"])
        self.assertFalse(result["blender_emit"])

    def test_boundary_triplet_disruption_flag_is_preregistered(self):
        rows = [row(v) for v in SENTINEL9]
        for variant in ("M13", "M14"):
            target = next(r for r in rows if r["variant_id"] == variant)
            target["oracle_result"] = "LOAD_REJECTED"
            target["visible_effect"] = "NOT_VISIBLE"
        projection, receipt = packet(rows)
        result = analyze_public_projection(projection, receipt)
        self.assertIn("BOUNDARY_TRIPLET_LOAD_DISRUPTION_CANDIDATE", result["preregistered_structural_flags"])
        self.assertEqual(result["interpretation_scope"], "STRUCTURAL_LOAD_VISIBILITY_ONLY")

    def test_framing_edge_disruption_flag(self):
        rows = [row(v) for v in SENTINEL9]
        target = next(r for r in rows if r["variant_id"] == "M23")
        target["oracle_result"] = "ERROR_DIALOG"
        target["visible_effect"] = "NOT_VISIBLE"
        projection, receipt = packet(rows)
        result = analyze_public_projection(projection, receipt)
        self.assertIn("FRAMING_EDGE_LOAD_DISRUPTION_CANDIDATE", result["preregistered_structural_flags"])
        self.assertIn("FRAMING_SENTINEL_DISAGREEMENT", result["preregistered_structural_flags"])

    def test_complete_30_requires_physical_complete_receipt(self):
        rows = [row(v) for v in EXPECTED]
        projection, receipt = packet(rows, physical_complete=True)
        result = analyze_public_projection(projection, receipt, require_complete=True)
        self.assertEqual(result["classification"], "STRUCTURAL_CONTRAST_COMPLETE_DIRECT")
        self.assertTrue(result["complete_30"])

    def test_rejects_wrong_offset(self):
        projection, receipt = packet([row("M01")])
        projection["observations"][0]["source_offset"] = 9
        receipt["public_projection_canonical_sha256"] = canonical_sha256(projection)
        with self.assertRaises(StructuralContrastRejected):
            analyze_public_projection(projection, receipt)

    def test_rejects_non_direct_or_unknown_rows(self):
        projection, receipt = packet([row("M01")])
        projection["observations"][0]["evidence_strength"] = "UNKNOWN"
        receipt["public_projection_canonical_sha256"] = canonical_sha256(projection)
        receipt["validation"]["direct_observation_count"] = 0
        receipt["physical_completion_gate"]["direct_observation_count"] = 0
        with self.assertRaises(StructuralContrastRejected):
            analyze_public_projection(projection, receipt)

    def test_rejects_projection_hash_swap(self):
        projection, receipt = packet([row("M01")])
        receipt["public_projection_canonical_sha256"] = "d" * 64
        with self.assertRaises(StructuralContrastRejected):
            analyze_public_projection(projection, receipt)

    def test_rejects_semantic_or_raw_row_fields(self):
        for field in ("candidate_semantic", "raw_payload"):
            with self.subTest(field=field):
                projection, receipt = packet([row("M01")])
                projection["observations"][0][field] = "forbidden"
                receipt["public_projection_canonical_sha256"] = canonical_sha256(projection)
                with self.assertRaises(StructuralContrastRejected):
                    analyze_public_projection(projection, receipt)

    def test_rejects_duplicate_variant(self):
        projection, receipt = packet([row("M01"), row("M01")])
        with self.assertRaises(StructuralContrastRejected):
            analyze_public_projection(projection, receipt)

    def test_partial_cannot_auto_authorize_numbered_run(self):
        projection, receipt = packet([row(v) for v in SENTINEL9])
        result = analyze_public_projection(projection, receipt)
        self.assertFalse(result["numbered_run_auto_authorized"])
        self.assertTrue(result["not_semantic_proof"])


if __name__ == "__main__":
    unittest.main()
