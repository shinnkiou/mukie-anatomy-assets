import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.toolchain import TOOL_SPECS, discover_toolchain


class ToolchainDiscoveryTests(unittest.TestCase):
    def test_discovery_is_bounded_and_structured(self):
        result = discover_toolchain(include_hash=False)
        self.assertEqual(result["schema_version"], "ukie_tool_discovery_v1")
        self.assertEqual(result["strategy"], "PATH_AND_KNOWN_LOCATIONS_ONLY")
        self.assertFalse(result["recursive_drive_scan"])
        self.assertEqual(len(result["tools"]), len(TOOL_SPECS))
        for tool in result["tools"]:
            self.assertIn(tool["status"], {"FOUND", "NOT_FOUND", "ERROR"})
            self.assertIn("tool_key", tool)


if __name__ == "__main__":
    unittest.main()
