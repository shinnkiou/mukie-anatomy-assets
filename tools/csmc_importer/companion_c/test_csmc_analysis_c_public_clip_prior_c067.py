from __future__ import annotations

import copy
import unittest

from csmc_analysis_c_public_clip_prior_c067 import (
    PublicClipPriorReconciliationRejected,
    reconcile_public_clip_prior,
)


def prior():
    return {
        "schema": "csmc_public_clip_3d_architecture_prior_v1",
        "lane": "PUBLIC_EXTERNAL_ARCHITECTURE_CORROBORATION",
        "status": "PUBLIC_PRIOR_NOT_CSMC_PROOF",
        "observed_format": ".clip",
        "target_format": ".csmc",
        "direct_csmc_evidence": False,
        "may_guide_blind_preregistration": False,
        "may_close_static_evidence_gate": False,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "sources": [
            {"repo": "Aodaruma/clipfile-rs", "commit": "bd88467fa80e63ad48c6c713fbfb5a8a116d798a", "license": "MIT"},
            {"repo": "youichi-uda/clip-clai", "commit": "76edfbf393868687107c2cdfdb750a70ca9ba7fe", "license": "MIT"},
            {"repo": "LavenderSnek/clipdecode", "commit": "e5347a65202bc399bdd730d13187bc32aabdd4fa", "license": "LGPL-2.1"},
        ],
        "public_architecture_prior": {
            "candidate_public_names": [
                "ExternalChunk", "ExternalTableAndColumnName", "Canvas3DModelBank",
                "Canvas3DModelLoader", "ModelData3D", "Manager3DOd", "ModelData",
            ],
            "candidate_name_usage": "POST_BLIND_NON_PROOF_CORROBORATION_ONLY",
        },
        "source_dependency_warning": "Public projects may share earlier community references.",
        "next_use": {"blind_lane": "UNCHANGED_AND_SEALED"},
    }


class PublicClipPriorC067Tests(unittest.TestCase):
    def test_current_state_is_quarantined_until_blind_result(self):
        result = reconcile_public_clip_prior(prior())
        self.assertEqual(result["classification"], "PUBLIC_PRIOR_ADMITTED_QUARANTINED_PENDING_BLIND_RESULT")
        self.assertFalse(result["proof_grade"])
        self.assertFalse(result["semantic_promotion"])

    def test_rejects_prior_guiding_blind(self):
        doc = prior()
        doc["may_guide_blind_preregistration"] = True
        with self.assertRaises(PublicClipPriorReconciliationRejected):
            reconcile_public_clip_prior(doc)

    def test_rejects_csmc_direct_evidence_claim(self):
        doc = prior()
        doc["direct_csmc_evidence"] = True
        with self.assertRaises(PublicClipPriorReconciliationRejected):
            reconcile_public_clip_prior(doc)

    def test_rejects_source_pin_swap(self):
        doc = prior()
        doc["sources"][0]["commit"] = "0" * 40
        with self.assertRaises(PublicClipPriorReconciliationRejected):
            reconcile_public_clip_prior(doc)

    def test_sealed_blind_result_can_match_only_post_blind(self):
        blind = {
            "schema_version": "csmc_blind_static_result_summary_v1",
            "sealed": True,
            "discovery_basis": "BLIND_DIRECT_DATA_FLOW",
            "used_public_prior_during_discovery": False,
            "path_tokens": ["UnrelatedReader", "ExternalChunk", "Canvas3DModelLoader"],
        }
        result = reconcile_public_clip_prior(prior(), blind_result_sealed=True, blind_result=blind)
        self.assertEqual(result["classification"], "POST_BLIND_NON_PROOF_CORROBORATION_MATCH_AVAILABLE")
        self.assertEqual(result["matched_public_names"], ["Canvas3DModelLoader", "ExternalChunk"])
        self.assertFalse(result["static_evidence_gate_closed"])

    def test_post_blind_nonmatch_must_not_force_result(self):
        blind = {
            "schema_version": "csmc_blind_static_result_summary_v1",
            "sealed": True,
            "discovery_basis": "BLIND_DIRECT_DATA_FLOW",
            "used_public_prior_during_discovery": False,
            "path_tokens": ["DifferentReaderPath"],
        }
        result = reconcile_public_clip_prior(prior(), blind_result_sealed=True, blind_result=blind)
        self.assertEqual(result["classification"], "POST_BLIND_NO_PUBLIC_PRIOR_MATCH_DO_NOT_FORCE")
        self.assertEqual(result["matched_public_names"], [])

    def test_rejects_contaminated_blind_result(self):
        blind = {
            "schema_version": "csmc_blind_static_result_summary_v1",
            "sealed": True,
            "discovery_basis": "BLIND_DIRECT_DATA_FLOW",
            "used_public_prior_during_discovery": True,
            "path_tokens": ["ExternalChunk"],
        }
        with self.assertRaises(PublicClipPriorReconciliationRejected):
            reconcile_public_clip_prior(prior(), blind_result_sealed=True, blind_result=blind)

    def test_rejects_wrong_observed_format(self):
        doc = prior()
        doc["observed_format"] = ".csmc"
        with self.assertRaises(PublicClipPriorReconciliationRejected):
            reconcile_public_clip_prior(doc)


if __name__ == "__main__":
    unittest.main()
