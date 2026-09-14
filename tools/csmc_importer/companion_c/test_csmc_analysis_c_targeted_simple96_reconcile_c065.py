#!/usr/bin/env python3
import unittest
from csmc_analysis_c_targeted_simple96_reconcile_c065 import validate


def good_record():
    return {
        "pipeline_stage": "STRUCTURAL_ONLY",
        "semantic_promotion_count": 0,
        "blender_emit_ready": False,
        "runtime_dispatch": False,
        "raw_private_bytes_published": False,
        "targeted_test": {
            "classification": "TARGETED_SIMPLE_96B_INSERTION_FAMILY_REJECTED",
            "family": "SIMPLE_96B_SINGLE_INSERTION_BEFORE_COMMON_BLOCK",
            "fixtures": ["CSMC_F06_CUBE_MAT2", "CSMC_F07_TWO_CUBES"],
            "delete_from": "F07_PRE_COMMON",
            "delete_length_bytes": 96,
            "exact_equality_required": True,
            "tolerance": 0,
            "multi_delete_allowed": False,
            "scopes": [
                {"scope": "FULL_PRE_COMMON", "hits": 0},
                {"scope": "TRAILING_2048_PLUS_INSERTION", "hits": 0, "shorter_bytes": 2048, "longer_bytes": 2144},
            ],
        },
        "preserved_source": {
            "triple_common_exact_bytes": 7392,
            "pre_common_shift_bytes": {"F06_minus_F03": 88, "F07_minus_F03": 184, "F07_minus_F06": 96},
            "render_part_residual_candidate": "LEVEL_4_REFINED_NOT_PROMOTED",
        },
        "frontier_decision": "RETURN_TO_PAUSED_WAITING_NEW_INDEPENDENT_EVIDENCE",
        "semantic_state": {
            "geometry": "UNRESOLVED",
            "index_topology": "UNRESOLVED",
            "serializer_field_read": "UNRESOLVED",
            "controlled_fixture_to_consumer_match": "UNRESOLVED",
        },
    }


class C065Tests(unittest.TestCase):
    def test_good(self): self.assertEqual(validate(good_record()), [])
    def test_promote_rejected(self):
        x=good_record(); x["semantic_promotion_count"]=1; self.assertTrue(validate(x))
    def test_blender_rejected(self):
        x=good_record(); x["blender_emit_ready"]=True; self.assertTrue(validate(x))
    def test_wrong_length_rejected(self):
        x=good_record(); x["targeted_test"]["delete_length_bytes"]=95; self.assertTrue(validate(x))
    def test_tolerance_rejected(self):
        x=good_record(); x["targeted_test"]["tolerance"]=1; self.assertTrue(validate(x))
    def test_multidelete_rejected(self):
        x=good_record(); x["targeted_test"]["multi_delete_allowed"]=True; self.assertTrue(validate(x))
    def test_scope_hit_rejected(self):
        x=good_record(); x["targeted_test"]["scopes"][0]["hits"]=1; self.assertTrue(validate(x))
    def test_scope_widening_rejected(self):
        x=good_record(); x["targeted_test"]["scopes"].append({"scope":"ARBITRARY_WINDOW","hits":0}); self.assertTrue(validate(x))
    def test_candidate_promotion_rejected(self):
        x=good_record(); x["preserved_source"]["render_part_residual_candidate"]="CONFIRMED"; self.assertTrue(validate(x))
    def test_unresolved_binding_required(self):
        x=good_record(); x["semantic_state"]["serializer_field_read"]="CONFIRMED"; self.assertTrue(validate(x))
    def test_frontier_must_pause(self):
        x=good_record(); x["frontier_decision"]="CONTINUE_BLIND_ENUMERATION"; self.assertTrue(validate(x))
    def test_private_publication_rejected(self):
        x=good_record(); x["raw_private_bytes_published"]=True; self.assertTrue(validate(x))


if __name__ == "__main__": unittest.main()
