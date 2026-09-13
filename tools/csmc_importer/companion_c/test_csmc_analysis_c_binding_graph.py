import unittest
from csmc_analysis_c_binding_graph import build_graph, has_path


class BindingGraphTests(unittest.TestCase):
    def test_current_record_to_codec_path_absent(self):
        g = build_graph()
        self.assertFalse(g["paths"]["record_to_confirmed_codec"])
        self.assertEqual(g["counts"]["record_to_confirmed_codec_bindings"], 0)

    def test_current_record_to_semantic_paths_absent(self):
        g = build_graph()
        self.assertFalse(g["paths"]["record_to_geometry_or_index"])
        self.assertFalse(g["paths"]["record_to_transform_or_hierarchy"])

    def test_character_route_to_record_family_path_exists(self):
        g = build_graph()
        self.assertTrue(has_path(g["edges"], ["ROUTE_character"], ["RF_00"]))

    def test_synthetic_codec_bridge_changes_only_codec_reachability(self):
        g = build_graph()
        edges = list(g["edges"]) + [
            {"source": "RF_00", "target": "CODEC_counted_be_numeric", "level": "SYNTHETIC", "evidence": "SYN"}
        ]
        self.assertTrue(has_path(edges, ["RF_00"], ["CODEC_counted_be_numeric"]))
        self.assertFalse(has_path(edges, ["RF_00"], ["SEM_geometry", "SEM_index"]))


if __name__ == "__main__":
    unittest.main()
