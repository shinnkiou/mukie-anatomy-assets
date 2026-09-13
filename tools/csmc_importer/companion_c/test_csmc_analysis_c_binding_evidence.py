import unittest
from csmc_analysis_c_binding_evidence import classify

BASE = {
    "binding_id": "SYN",
    "current_payload_mapping": True,
    "bounded_region_id": "REGIME_plus965/RF_00/child_x",
    "codec_evidence_level": "CONFIRMED_ENCODING",
    "exact_decode_fit_instances": 0,
    "same_structural_role_recurrence": False,
    "controlled_differential": False,
    "known_input_correlation": False,
    "localized_effect": False,
    "semantic_slot": None,
}


class BindingEvidenceTests(unittest.TestCase):
    def test_no_fit_no_binding(self):
        self.assertEqual(classify(dict(BASE)), "NO_BINDING")

    def test_single_fit_candidate_only(self):
        e = dict(BASE)
        e["exact_decode_fit_instances"] = 1
        self.assertEqual(classify(e), "CANDIDATE_CODEC_BINDING")

    def test_recurrent_fit_confirms_codec_binding(self):
        e = dict(BASE)
        e["exact_decode_fit_instances"] = 2
        e["same_structural_role_recurrence"] = True
        self.assertEqual(classify(e), "CONFIRMED_CODEC_BINDING")

    def test_semantic_promotion_requires_full_bridge(self):
        e = dict(BASE)
        e["exact_decode_fit_instances"] = 3
        e["same_structural_role_recurrence"] = True
        e["semantic_slot"] = "transform"
        e["controlled_differential"] = True
        self.assertEqual(classify(e), "CONFIRMED_CODEC_BINDING")
        e["known_input_correlation"] = True
        e["localized_effect"] = True
        self.assertEqual(classify(e), "CONFIRMED_SEMANTIC_BINDING")


if __name__ == "__main__":
    unittest.main()
