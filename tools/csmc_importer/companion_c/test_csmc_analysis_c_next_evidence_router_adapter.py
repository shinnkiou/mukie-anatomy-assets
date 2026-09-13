#!/usr/bin/env python3

import unittest

from csmc_analysis_c_next_evidence_router_adapter import reconcile_event


BASE = {
    "auto_semantic_promotion": False,
    "auto_blender_emit": False,
}
FULL_I2 = {2: 1, 3: 0, 8: 1, 14: 0, 15: 1, 21: 0}


class NextEvidenceRouterAdapterTests(unittest.TestCase):
    def test_empty_current_state_has_no_action(self):
        out = reconcile_event(dict(BASE))
        self.assertTrue(out["accepted"])
        self.assertEqual(out["status"], "NO_ADMISSIBLE_ACTION_CURRENT_DURABLE_CORPUS")
        self.assertEqual(out["selected_companion_actions"], [])

    def test_complete_c047_normalized_i2_goes_to_full_c040_validation(self):
        out = reconcile_event({
            **BASE,
            "i2_bits_by_record": FULL_I2,
            "i2_provenance_valid": True,
            "c047_residual_patch_accepted": True,
        })
        self.assertEqual(
            out["selected_companion_actions"][0]["action"],
            "ASSEMBLE_COMPLETE_I2_AND_RUN_C040_FULL_VALIDATOR",
        )

    def test_five_bit_i2_never_goes_directly_to_mainline_route(self):
        partial = dict(FULL_I2)
        partial.pop(21)
        out = reconcile_event({
            **BASE,
            "i2_bits_by_record": partial,
            "i2_provenance_valid": True,
        })
        self.assertEqual(
            out["selected_companion_actions"][0]["action"],
            "ROUTE_PARTIAL_I2_THROUGH_C047_ONLY",
        )

    def test_unvalidated_six_bit_i2_rejects(self):
        out = reconcile_event({
            **BASE,
            "i2_bits_by_record": FULL_I2,
            "i2_provenance_valid": True,
            "c047_residual_patch_accepted": False,
        })
        self.assertFalse(out["accepted"])

    def test_new_decisive_edge_reviews_only_that_edge(self):
        out = reconcile_event({
            **BASE,
            "decisive_owner_edges": ["EXPLICIT_PARENT_LENGTH_FIELD", "NOT_VALID"],
        })
        action = out["selected_companion_actions"][0]
        self.assertEqual(action["action"], "REVIEW_NEW_BOUNDARY_LOCAL_OWNER_EDGE_ONLY")
        self.assertEqual(action["scope"], ["EXPLICIT_PARENT_LENGTH_FIELD"])
        self.assertFalse(action["rerun_c045_search"])

    def test_short_unlock_alias_normalizes_to_c040_class(self):
        out = reconcile_event({**BASE, "validated_unlock_classes": ["I3"]})
        action = out["selected_companion_actions"][0]
        self.assertEqual(action["action"], "PROCESS_VALIDATED_STATIC_UNLOCK_CLASS_ONLY")
        self.assertEqual(
            action["scope"],
            ["I3_INTERPRETABLE_CONTROLLED_PAIR_OR_LABELED_DIFFERENTIAL"],
        )

    def test_external_pair_requires_prior_i1_validation(self):
        out = reconcile_event({
            **BASE,
            "external_authorized_pair_present": True,
            "external_pair_hash_match_verified": True,
            "i1_static_validation_accepted": False,
        })
        self.assertFalse(out["accepted"])
        self.assertEqual(out["selected_companion_actions"], [])

    def test_i1_validated_external_pair_only_allows_preregistered_probe(self):
        out = reconcile_event({
            **BASE,
            "external_authorized_pair_present": True,
            "external_pair_hash_match_verified": True,
            "i1_static_validation_accepted": True,
        })
        action = out["selected_companion_actions"][0]
        self.assertEqual(action["action"], "ALLOW_PREREGISTERED_FIXED_ROLE_PROBE_ONLY")
        self.assertFalse(action["posthoc_window_widening"])
        self.assertFalse(action["acquire_pair"])

    def test_runtime_flag_cannot_reauthorize_runtime(self):
        out = reconcile_event({**BASE, "runtime_dispatch_requested": True})
        self.assertFalse(out["accepted"])
        self.assertFalse(out["runtime_dispatch"])

    def test_acquisition_request_is_rejected(self):
        out = reconcile_event({**BASE, "acquisition_requested": True})
        self.assertFalse(out["accepted"])
        self.assertFalse(out["evidence_acquisition"])

    def test_multiple_valid_static_inputs_stay_nonsemantic(self):
        out = reconcile_event({
            **BASE,
            "decisive_owner_edges": ["EXPLICIT_CONSUMER_CROSSREF"],
            "validated_unlock_classes": ["I1", "I4"],
        })
        self.assertEqual(len(out["selected_companion_actions"]), 2)
        self.assertFalse(out["semantic_promotion"])
        self.assertFalse(out["blender_emit"])
        self.assertFalse(out["mainline_mutation"])
        self.assertFalse(out["rio26_mutation"])


if __name__ == "__main__":
    unittest.main()
