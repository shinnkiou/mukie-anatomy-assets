import unittest

from csmc_analysis_c_handoff_contract import REQUIRED_UNLOCKS, validate
from csmc_analysis_c_parser_skeleton import build_parser_state
from csmc_analysis_c_pipeline_contract import CONFIRMED_SEMANTIC, analyze


class IntegrationReviewContractTests(unittest.TestCase):
    def _safe_package(self):
        return {
            "merge_policy": "NO_AUTOMATIC_MERGE",
            "pipeline_stage": "STRUCTURAL_ONLY",
            "semantic_promotion_count": 0,
            "blender_mesh_emit_ready": False,
            "blender_scene_emit_ready": False,
            "future_unlock_inputs": sorted(REQUIRED_UNLOCKS),
            "isolation": {
                "runtime_jobs": 0,
                "modeler_actions": 0,
                "worker_actions": 0,
                "rio26_mutations": 0,
                "mainline_mutations": 0,
                "public_repository_contains_private_payload": False,
                "automatic_integration": False,
            },
        }

    def test_reference_handoff_accepts_only_non_mutating_state(self):
        package = self._safe_package()
        self.assertTrue(validate(package)["accepted"])
        package["isolation"]["runtime_jobs"] = 1
        self.assertFalse(validate(package)["accepted"])

    def test_v2_automatic_integration_alias_is_rejected(self):
        package = self._safe_package()
        package["isolation"]["automatic_integration"] = True
        result = validate(package)
        self.assertFalse(result["accepted"])
        self.assertIn("automatic_integration_true", result["errors"])

    def test_v2_private_payload_alias_is_rejected(self):
        package = self._safe_package()
        package["isolation"]["public_repository_contains_private_payload"] = True
        result = validate(package)
        self.assertFalse(result["accepted"])
        self.assertIn("private_bytes_public", result["errors"])

    def test_missing_isolation_guardrail_is_rejected(self):
        package = self._safe_package()
        del package["isolation"]["worker_actions"]
        result = validate(package)
        self.assertFalse(result["accepted"])
        self.assertIn("missing_worker_actions", result["errors"])

    def test_pipeline_never_promotes_semantics_implicitly(self):
        state = analyze({
            "intake_accepted": True,
            "route_state": "LIVE_RESOLVED_EDGE",
            "structural_ir_valid": True,
            "codec_binding_level": "CONFIRMED_CODEC_BINDING",
            "semantic_slots": {},
        })
        self.assertEqual(state["pipeline_stage"], "CODEC_BOUND")
        self.assertFalse(state["mesh_emit_ready"])
        self.assertFalse(state["implicit_semantic_promotion"])

    def test_mesh_gate_requires_geometry_and_index(self):
        state = analyze({
            "intake_accepted": True,
            "route_state": "LIVE_RESOLVED_EDGE",
            "structural_ir_valid": True,
            "codec_binding_level": "CONFIRMED_CODEC_BINDING",
            "semantic_slots": {
                "geometry": CONFIRMED_SEMANTIC,
                "index": CONFIRMED_SEMANTIC,
            },
        })
        self.assertTrue(state["mesh_emit_ready"])
        self.assertFalse(state["scene_emit_ready"])

    def test_parser_blocks_current_unresolved_semantics(self):
        minimal_ir = {
            "structural_grammar": {
                "boundary_classes_observed": ["LOCAL_EXTINCTION_CANDIDATE"],
                "record_families": [{"family_id": "RF_00", "length_blocks": 48, "semantic_role": "UNRESOLVED"}],
            },
            "semantic_slots": {
                "geometry": {"status": "UNRESOLVED", "confidence": 0.0, "evidence_ids": []},
                "index": {"status": "UNRESOLVED", "confidence": 0.0, "evidence_ids": []},
            },
        }
        owner_map = {
            "importer_routes": {
                "character": {"source": "Canvas3DModelLoader.ModelData", "target_kind": "catalog_character"}
            }
        }
        numeric = {"confirmed_encoding_ids": ["COUNTED_BE_NUMERIC_ACTIVE_MANAGER3DOD"], "semantic_slots_promoted": []}
        record_owner = {
            "record_family_count": 1,
            "record_instance_count": 22,
            "coarse_route_correlation": {"route": "character"},
        }
        state = build_parser_state(minimal_ir, owner_map, numeric, record_owner)
        self.assertFalse(state["semantic_gate"]["can_emit_blender_geometry"])
        self.assertEqual(state["semantic_gate"]["blocked_slots"], ["geometry", "index"])
        self.assertEqual(state["codec_annotation"]["binding_count"], 0)


if __name__ == "__main__":
    unittest.main()
