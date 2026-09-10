import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.blender_canary import _verify_scene_report


class BlenderCanarySemanticTests(unittest.TestCase):
    def _write(self, payload):
        temp = tempfile.TemporaryDirectory()
        path = pathlib.Path(temp.name) / "scene_before.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return temp, path

    def test_expected_cube_passes(self):
        temp, path = self._write({
            "objects": [{
                "name": "UKIE_CANARY_CUBE",
                "mesh": {"vertices": 8, "polygons": 6},
            }],
            "blender_version": "4.2.23",
            "python_version": "3.x",
        })
        try:
            result = _verify_scene_report(path)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["vertices"], 8)
            self.assertEqual(result["polygons"], 6)
        finally:
            temp.cleanup()

    def test_wrong_topology_fails(self):
        temp, path = self._write({
            "objects": [{
                "name": "UKIE_CANARY_CUBE",
                "mesh": {"vertices": 7, "polygons": 6},
            }]
        })
        try:
            result = _verify_scene_report(path)
            self.assertEqual(result["status"], "FAIL")
        finally:
            temp.cleanup()

    def test_missing_cube_fails(self):
        temp, path = self._write({"objects": []})
        try:
            result = _verify_scene_report(path)
            self.assertEqual(result["status"], "FAIL")
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
