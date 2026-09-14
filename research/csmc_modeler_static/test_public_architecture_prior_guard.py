import copy
import json
import unittest
from pathlib import Path

from public_architecture_prior_guard import PublicPriorRejected, validate_public_prior


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "CSMC_PUBLIC_CLIP_3D_ARCHITECTURE_PRIOR_V1.json"


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class PublicArchitecturePriorGuardTests(unittest.TestCase):
    def test_canonical_manifest_is_valid_non_proof(self):
        result = validate_public_prior(load_manifest())
        self.assertEqual(
            result["classification"],
            "PUBLIC_CLIP_3D_ARCHITECTURE_PRIOR_VALID_NON_PROOF",
        )
        self.assertFalse(result["proof_grade"])
        self.assertTrue(result["blind_preregistration_unchanged"])
        self.assertGreaterEqual(result["source_count"], 2)

    def test_direct_csmc_evidence_cannot_be_claimed(self):
        doc = load_manifest()
        doc["direct_csmc_evidence"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_public_prior_cannot_guide_blind_lane(self):
        doc = load_manifest()
        doc["may_guide_blind_preregistration"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_public_prior_cannot_close_static_gate(self):
        doc = load_manifest()
        doc["may_close_static_evidence_gate"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_semantic_promotion_rejected(self):
        doc = load_manifest()
        doc["semantic_promotion"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_blender_emit_rejected(self):
        doc = load_manifest()
        doc["blender_emit"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_runtime_dispatch_rejected(self):
        doc = load_manifest()
        doc["runtime_dispatch"] = True
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_observed_format_cannot_be_rewritten_as_csmc(self):
        doc = load_manifest()
        doc["observed_format"] = ".csmc"
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_candidate_names_are_post_blind_only(self):
        doc = load_manifest()
        doc["public_architecture_prior"]["candidate_name_usage"] = "BLIND_TARGETING"
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_required_architecture_names_cannot_disappear_silently(self):
        doc = load_manifest()
        doc["public_architecture_prior"]["candidate_public_names"].remove("ExternalChunk")
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_blind_lane_must_remain_sealed(self):
        doc = load_manifest()
        doc["next_use"]["blind_lane"] = "REOPEN_WITH_PUBLIC_NAMES"
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(doc)

    def test_source_requires_commit_and_license(self):
        doc = load_manifest()
        broken = copy.deepcopy(doc)
        broken["sources"][0]["commit"] = "short"
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(broken)
        broken = copy.deepcopy(doc)
        broken["sources"][0]["license"] = ""
        with self.assertRaises(PublicPriorRejected):
            validate_public_prior(broken)


if __name__ == "__main__":
    unittest.main()
