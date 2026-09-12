import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.analyze_runner import preview_analyze_contract


class AnalyzeRunnerContractTests(unittest.TestCase):
    def test_visual_qa_previews_are_required(self):
        contract = preview_analyze_contract()
        names = {item["name"] for item in contract["files"]}
        self.assertIn("scene_before.json", names)
        self.assertIn("preview_front.png", names)
        self.assertIn("preview_side.png", names)
        self.assertIn("input.blend", names)
        self.assertIn("working.blend", names)

    def test_preview_minimum_is_nontrivial(self):
        contract = preview_analyze_contract()
        by_name = {item["name"]: item for item in contract["files"]}
        self.assertGreaterEqual(by_name["preview_front.png"]["min_bytes"], 1024)
        self.assertGreaterEqual(by_name["preview_side.png"]["min_bytes"], 1024)


if __name__ == "__main__":
    unittest.main()
