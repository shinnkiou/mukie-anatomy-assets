from copy import deepcopy
import unittest
from csmc_analysis_c_parser_skeleton import build_parser_state


def fixtures():
    ir = {
        "structural_grammar": {
            "boundary_classes_observed": ["LOCAL_EXTINCTION_CANDIDATE", "MIXED_REUSE_REPACK_CANDIDATE"],
            "record_families": [
                {"family_id": "RF_00", "length_blocks": 48, "preserve_signature": "0000110", "semantic_role": "UNRESOLVED"}
            ],
        },
        "semantic_slots": {
            "geometry": {"status": "UNRESOLVED", "confidence": 0.0, "evidence_ids": []},
            "index": {"status": "UNRESOLVED", "confidence": 0.0, "evidence_ids": []},
            "transform": {"status": "UNRESOLVED", "confidence": 0.0, "evidence_ids": []},
            "material": {"status": "UNRESOLVED", "confidence": 0.0, "evidence_ids": []},
            "hierarchy": {"status": "UNRESOLVED", "confidence": 0.0, "evidence_ids": []},
        },
    }
    owner = {
        "importer_routes": {
            "character": {"source": "Canvas3DModelLoader.ModelData", "target_kind": "catalog_character", "semantic_payload_role": "UNRESOLVED"},
            "scene": {"source": "Manager3DOd.SceneData", "target_kind": "scene", "semantic_payload_role": "UNRESOLVED"},
        }
    }
    numeric = {
        "confirmed_encoding_ids": ["COUNTED_BE_NUMERIC_ACTIVE_MANAGER3DOD"],
        "semantic_slots_promoted": [],
    }
    record_owner = {
        "record_family_count": 5,
        "record_instance_count": 22,
        "coarse_route_correlation": {"route": "character"},
    }
    return ir, owner, numeric, record_owner


class ParserSkeletonTests(unittest.TestCase):
    def test_current_evidence_blocks_blender_emit(self):
        state = build_parser_state(*fixtures())
        self.assertFalse(state["semantic_gate"]["can_emit_blender_geometry"])
        self.assertEqual(state["semantic_gate"]["blocked_slots"], ["geometry", "index"])

    def test_confirmed_codec_does_not_bind_to_record_family(self):
        state = build_parser_state(*fixtures())
        self.assertEqual(state["codec_annotation"]["binding_count"], 0)
        self.assertEqual(state["structural_normalization"]["character_regimes"][0]["internal_section_owner"], "UNRESOLVED")

    def test_candidate_semantics_still_block_emit(self):
        ir, owner, numeric, record_owner = fixtures()
        ir["semantic_slots"]["geometry"] = {"status": "CANDIDATE", "confidence": 0.9, "evidence_ids": ["E1"]}
        ir["semantic_slots"]["index"] = {"status": "CANDIDATE", "confidence": 0.9, "evidence_ids": ["E2"]}
        state = build_parser_state(ir, owner, numeric, record_owner)
        self.assertFalse(state["semantic_gate"]["can_emit_blender_geometry"])

    def test_synthetic_confirmed_geometry_and_index_can_open_gate(self):
        ir, owner, numeric, record_owner = fixtures()
        ir["semantic_slots"]["geometry"] = {"status": "CONFIRMED", "confidence": 0.9, "evidence_ids": ["SYN_GEOM"]}
        ir["semantic_slots"]["index"] = {"status": "CONFIRMED", "confidence": 0.9, "evidence_ids": ["SYN_INDEX"]}
        state = build_parser_state(ir, owner, numeric, record_owner)
        self.assertTrue(state["semantic_gate"]["can_emit_blender_geometry"])
        self.assertEqual(state["semantic_gate"]["blocked_slots"], [])


if __name__ == "__main__":
    unittest.main()
