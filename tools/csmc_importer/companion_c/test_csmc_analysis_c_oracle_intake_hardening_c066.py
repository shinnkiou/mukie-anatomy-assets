#!/usr/bin/env python3
import unittest
from csmc_analysis_c_oracle_intake_hardening_c066 import validate


def good_record():
    return {
        "pipeline_stage": "STRUCTURAL_ONLY",
        "source_batch_id": "CSMC_F02_SINGLE_BYTE_XOR01_30_20260914",
        "source_manifest_raw_sha256": "751f05dfff9d5308dfd96421d5bce43e6785de2cb385fb28a8c97c565c6cc891",
        "source_manifest_raw_sha_bound": True,
        "verify_raw_sha_before_json_parse": True,
        "expected_variant_count": 30,
        "existing_observation_contract_preserved": True,
        "fail_closed_cli": True,
        "physical_observations_acquired": 0,
        "physical_oracle_status": "PENDING_MANUAL_ORACLE",
        "launch_modeler": False,
        "generate_mutations": False,
        "save_allowed": False,
        "serialization_trigger_allowed": False,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "mainline_mutation": False,
        "rio26_mutation": False,
        "raw_private_bytes_published": False,
        "semantic_state": {
            "geometry": "UNRESOLVED",
            "index_topology": "UNRESOLVED",
            "explicit_serializer_field_read": "UNRESOLVED",
            "controlled_fixture_to_consumer_match": "UNRESOLVED",
        },
        "receipt_contract": {
            "schema_version": "csmc_f02_mutation_oracle_intake_receipt_v1",
            "source_manifest_raw_sha256": True,
            "observation_raw_sha256": True,
            "public_projection_canonical_sha256": True,
            "diagnostic_only": True,
            "semantic_promotion": False,
            "blender_emit": False,
        },
    }


class C066Tests(unittest.TestCase):
    def test_good(self): self.assertEqual(validate(good_record()), [])
    def test_manifest_hash_swap_rejected(self):
        x=good_record(); x["source_manifest_raw_sha256"]="0"*64; self.assertTrue(validate(x))
    def test_hash_after_parse_rejected(self):
        x=good_record(); x["verify_raw_sha_before_json_parse"]=False; self.assertTrue(validate(x))
    def test_wrong_batch_rejected(self):
        x=good_record(); x["source_batch_id"]="OTHER"; self.assertTrue(validate(x))
    def test_wrong_count_rejected(self):
        x=good_record(); x["expected_variant_count"]=29; self.assertTrue(validate(x))
    def test_contract_change_rejected(self):
        x=good_record(); x["existing_observation_contract_preserved"]=False; self.assertTrue(validate(x))
    def test_physical_claim_rejected(self):
        x=good_record(); x["physical_observations_acquired"]=1; self.assertTrue(validate(x))
    def test_modeler_launch_rejected(self):
        x=good_record(); x["launch_modeler"]=True; self.assertTrue(validate(x))
    def test_save_rejected(self):
        x=good_record(); x["save_allowed"]=True; self.assertTrue(validate(x))
    def test_semantic_promotion_rejected(self):
        x=good_record(); x["semantic_promotion"]=True; self.assertTrue(validate(x))
    def test_serializer_claim_rejected(self):
        x=good_record(); x["semantic_state"]["explicit_serializer_field_read"]="CONFIRMED"; self.assertTrue(validate(x))
    def test_receipt_missing_hash_rejected(self):
        x=good_record(); x["receipt_contract"]["observation_raw_sha256"]=False; self.assertTrue(validate(x))
    def test_receipt_not_diagnostic_rejected(self):
        x=good_record(); x["receipt_contract"]["diagnostic_only"]=False; self.assertTrue(validate(x))
    def test_raw_private_publication_rejected(self):
        x=good_record(); x["raw_private_bytes_published"]=True; self.assertTrue(validate(x))


if __name__ == "__main__": unittest.main()
