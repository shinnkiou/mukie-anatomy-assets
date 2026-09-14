#!/usr/bin/env python3
import copy
import unittest

from csmc_analysis_c_render_part_residual_reconcile_c064 import validate


def good_record():
    return {
        "pipeline_stage": "STRUCTURAL_ONLY",
        "semantic_promotion_count": 0,
        "blender_emit_ready": False,
        "runtime_dispatch": False,
        "raw_private_bytes_published": False,
        "candidate": "TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE",
        "confidence_before": "LEVEL_4_CANDIDATE",
        "confidence_after": "LEVEL_4_CANDIDATE_REFINED_NOT_PROMOTED",
        "triple_common": {
            "length_qwords": 924,
            "length_bytes": 7392,
            "start_qwords": {"F03": 442, "F06": 453, "F07": 465},
            "v01_occurrence_qword": 531781,
        },
        "pre_common_shifts": {
            "F06_minus_F03_bytes": 88,
            "F07_minus_F03_bytes": 184,
            "F07_minus_F06_bytes": 96,
        },
        "logical_length_deltas": {
            "F06_minus_F03": 2555,
            "F07_minus_F03": 2651,
            "F07_minus_F06": 96,
        },
        "post_common_growth": {
            "F06_minus_F03_bytes": 2467,
            "F07_minus_F03_bytes": 2467,
        },
        "cadence_bytes": 2456,
        "other_bytes": 11,
        "boundary_scalar_negative_control": {
            "window_bytes": 2048,
            "candidate_configurations_evaluated": 40928,
            "hard_pass_count": 0,
            "rejection_scope": "DIRECT_RAW_SHARED_BOUNDARY_RELATIVE_SCALAR_ONLY",
        },
        "semantic_state": {
            "geometry": "UNRESOLVED",
            "index_topology": "UNRESOLVED",
            "serializer_field_read": "UNRESOLVED",
            "controlled_fixture_to_consumer_match": "UNRESOLVED",
        },
    }


class C064Tests(unittest.TestCase):
    def test_good_record_passes(self):
        self.assertEqual(validate(good_record()), [])

    def test_semantic_promotion_rejected(self):
        x = good_record(); x["semantic_promotion_count"] = 1
        self.assertTrue(validate(x))

    def test_blender_emit_rejected(self):
        x = good_record(); x["blender_emit_ready"] = True
        self.assertTrue(validate(x))

    def test_confidence_promotion_rejected(self):
        x = good_record(); x["confidence_after"] = "CONFIRMED"
        self.assertTrue(validate(x))

    def test_common_extent_mismatch_rejected(self):
        x = good_record(); x["triple_common"]["length_bytes"] = 7393
        self.assertTrue(validate(x))

    def test_shift_mismatch_rejected(self):
        x = good_record(); x["pre_common_shifts"]["F07_minus_F06_bytes"] = 88
        self.assertTrue(validate(x))

    def test_cadence_decomposition_mismatch_rejected(self):
        x = good_record(); x["other_bytes"] = 12
        self.assertTrue(validate(x))

    def test_scalar_pass_invalidates_rejection(self):
        x = good_record(); x["boundary_scalar_negative_control"]["hard_pass_count"] = 1
        self.assertTrue(validate(x))

    def test_scope_widening_rejected(self):
        x = good_record(); x["boundary_scalar_negative_control"]["rejection_scope"] = "ALL_COUNT_ENCODINGS"
        self.assertTrue(validate(x))

    def test_semantic_binding_rejected(self):
        x = good_record(); x["semantic_state"]["geometry"] = "CONFIRMED"
        self.assertTrue(validate(x))

    def test_runtime_dispatch_rejected(self):
        x = good_record(); x["runtime_dispatch"] = True
        self.assertTrue(validate(x))

    def test_private_publication_rejected(self):
        x = good_record(); x["raw_private_bytes_published"] = True
        self.assertTrue(validate(x))


if __name__ == "__main__":
    unittest.main()
