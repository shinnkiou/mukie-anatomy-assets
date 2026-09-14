import copy
import json
import unittest
from pathlib import Path

from public_architecture_prior_guard import PublicPriorRejected, validate_public_prior


HERE = Path(__file__).resolve().parent
MANIFEST_V1 = HERE / "CSMC_PUBLIC_CLIP_3D_ARCHITECTURE_PRIOR_V1.json"
MANIFEST_V2 = HERE / "CSMC_PUBLIC_CLIP_3D_ARCHITECTURE_PRIOR_V2.json"


def load_manifest(path=MANIFEST_V1):
    return json.loads(path.read_text(encoding="utf-8"))


class PublicArchitecturePriorGuardTests(unittest.TestCase):
    def test_v1_manifest_is_valid_non_proof(self):
        result = validate_public_prior(load_manifest(MANIFEST_V1))
        self.assertEqual(
            result["classification"],
            "PUBLIC_CLIP_3D_ARCHITECTURE_PRIOR_VALID_NON_PROOF",
        )
        self.assertFalse(result["proof_grade"])
        self.assertTrue(result["blind_preregistration_unchanged"])
        self.assertGreaterEqual(result["source_count"], 2)
        self.assertEqual(result["negative_control_count"], 0)

    def test_v2_manifest_is_valid_with_negative_controls(self):
        result = validate_public_prior(load_manifest(MANIFEST_V2))
        self.assertEqual(result["source_count"], 5)
        self.assertEqual(result["unique_repo_count"], 5)
        self.assertGreaterEqual(result["negative_control_count"], 2)
        self.assertFalse(result["proof_grade"])
        self.assertTrue(result["blind_preregistration_unchanged"])

    def test_direct_csmc_evidence_cannot_be_claimed(self):
        doc = load_manifest(MANIFEST_V2)
        doc["direct_csmc_evidence"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_public_prior_cannot_guide_blind_lane(self):
        doc = load_manifest(MANIFEST_V2)
        doc["may_guide_blind_preregistration"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_public_prior_cannot_close_static_gate(self):
        doc = load_manifest(MANIFEST_V2)
        doc["may_close_static_evidence_gate"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_semantic_promotion_rejected(self):
        doc = load_manifest(MANIFEST_V2)
        doc["semantic_promotion"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_blender_emit_rejected(self):
        doc = load_manifest(MANIFEST_V2)
        doc["blender_emit"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_runtime_dispatch_rejected(self):
        doc = load_manifest(MANIFEST_V2)
        doc["runtime_dispatch"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_observed_format_cannot_be_rewritten_as_csmc(self):
        doc = load_manifest(MANIFEST_V2)
        doc["observed_format"] = ".csmc"
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_candidate_names_are_post_blind_only(self):
        doc = load_manifest(MANIFEST_V2)
        doc["public_architecture_prior"]["candidate_name_usage"] = "BLIND_TARGETING"
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_required_architecture_names_cannot_disappear_silently(self):
        doc = load_manifest(MANIFEST_V2)
        doc["public_architecture_prior"]["candidate_public_names"].remove("ExternalChunk")
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_blind_lane_must_remain_sealed(self):
        doc = load_manifest(MANIFEST_V2)
        doc["next_use"]["blind_lane"] = "REOPEN_WITH_PUBLIC_NAMES"
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_source_requires_commit_and_license(self):
        doc = load_manifest(MANIFEST_V2)
        broken = copy.deepcopy(doc)
        broken["sources"][0]["commit"] = "short"
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(broken)
        broken = copy.deepcopy(doc)
        broken["sources"][0]["license"] = ""
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(broken)

    def test_v2_must_not_claim_source_independence(self):
        doc = load_manifest(MANIFEST_V2)
        doc["independence_not_assumed"] = False
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_v2_requires_declared_name_negative_control(self):
        doc = load_manifest(MANIFEST_V2)
        doc["public_negative_controls"] = [
            item
            for item in doc["public_negative_controls"]
            if item["id"] != "DECLARED_EXTERNAL_NAME_NOT_INSTANCE_PRESENCE"
        ]
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_v2_requires_dependency_negative_control(self):
        doc = load_manifest(MANIFEST_V2)
        doc["public_negative_controls"] = [
            item
            for item in doc["public_negative_controls"]
            if item["id"] != "TYPED_VIEW_NOT_INDEPENDENT_REPLICATION"
        ]
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_v2_dependency_role_requires_note(self):
        doc = load_manifest(MANIFEST_V2)
        for source in doc["sources"]:
            if source.get("role") == "DEPENDENT_TYPED_SCHEMA_CORROBORATION":
                source["dependency_note"] = ""
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_v2_requires_measured_negative_control_source(self):
        doc = load_manifest(MANIFEST_V2)
        for source in doc["sources"]:
            if source.get("role") == "INDEPENDENT_REDERIVATION_WITH_MEASURED_NEGATIVE_CONTROL":
                source["role"] = "OTHER"
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)


if __name__ == "__main__":
    unittest.main()
