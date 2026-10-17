import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.experiment_manifest import ExperimentManifestError, validate_experiment_manifest


class ExperimentManifestTests(unittest.TestCase):
    def base(self):
        return {
            "schema_version": "ukie_experiment_v1",
            "experiment_id": "EXP_0001",
            "project": "CSMC",
            "source": {"model_id": "VRM_BASE", "sha256": "a" * 64},
            "parent_experiment_id": None,
            "root_experiment_id": "EXP_0001",
            "generation": 0,
            "control_group": False,
            "changes": [
                {
                    "type": "vertex_position",
                    "target": {"object": "Body", "vertex_index": 10, "axis": "X"},
                    "delta": 0.001,
                }
            ],
            "toolchain": {"bridge_version": "0.3.0-p0.2", "blender": "4.2.23"},
        }

    def test_single_change_is_valid(self):
        validated = validate_experiment_manifest(self.base())
        self.assertEqual(validated.change_type, "vertex_position")
        self.assertEqual(len(validated.manifest_sha256), 64)

    def test_multiple_changes_rejected(self):
        payload = self.base()
        payload["changes"].append(copy.deepcopy(payload["changes"][0]))
        with self.assertRaises(ExperimentManifestError):
            validate_experiment_manifest(payload)

    def test_control_must_have_zero_changes(self):
        payload = self.base()
        payload["control_group"] = True
        with self.assertRaises(ExperimentManifestError):
            validate_experiment_manifest(payload)

    def test_control_without_changes_is_valid(self):
        payload = self.base()
        payload["control_group"] = True
        payload["changes"] = []
        validated = validate_experiment_manifest(payload)
        self.assertIsNone(validated.change_type)

    def test_child_requires_parent(self):
        payload = self.base()
        payload["experiment_id"] = "EXP_0002"
        payload["generation"] = 1
        with self.assertRaises(ExperimentManifestError):
            validate_experiment_manifest(payload)

    def test_forbidden_shell_field_rejected_anywhere(self):
        payload = self.base()
        payload["changes"][0]["shell"] = "unsafe"
        with self.assertRaises(ExperimentManifestError):
            validate_experiment_manifest(payload)


if __name__ == "__main__":
    unittest.main()
