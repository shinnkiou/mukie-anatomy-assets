import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.install_manifest import (
    InstallManifestError,
    sha256_json,
    validate_approval_manifest,
    validate_resolved_manifest,
)


class InstallManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ROOT / "fixtures" / "install_approval.valid.json", encoding="utf-8") as f:
            cls.base = json.load(f)

    def test_valid_one_click_manifest(self):
        result = validate_approval_manifest(copy.deepcopy(self.base))
        self.assertEqual(result.batch_key, "INSTALL_BATCH_TEST_0001")
        self.assertTrue(result.requires_uac)
        self.assertFalse(result.requires_driver)
        self.assertEqual(result.manifest_sha256, sha256_json(self.base))

    def test_hash_is_stable_across_key_order(self):
        reordered = dict(reversed(list(self.base.items())))
        self.assertEqual(sha256_json(self.base), sha256_json(reordered))

    def test_reject_embedded_shell(self):
        payload = copy.deepcopy(self.base)
        payload["tools"][0]["command"] = "powershell.exe -NoProfile"
        with self.assertRaises(InstallManifestError):
            validate_approval_manifest(payload)

    def test_reject_unreviewed_tool(self):
        payload = copy.deepcopy(self.base)
        payload["tools"][0]["tool_key"] = "random_downloaded_exe"
        with self.assertRaises(InstallManifestError):
            validate_approval_manifest(payload)

    def test_reject_wrong_official_domain(self):
        payload = copy.deepcopy(self.base)
        payload["tools"][0]["official_url"] = "https://example.com/blender.zip"
        with self.assertRaises(InstallManifestError):
            validate_approval_manifest(payload)

    def test_resolved_manifest_must_bind_to_approval(self):
        approval = copy.deepcopy(self.base)
        digest = sha256_json(approval)
        resolved = {
            "schema_version": "ukie_install_resolution_v1",
            "approval_manifest_sha256": digest,
            "tools": [
                {
                    "tool_key": "blender_bp3d_4_2_23",
                    "source_type": "official_portable",
                    "version": "4.2.23",
                    "download_url": "https://download.blender.org/release/Blender4.2/example.zip",
                    "sha256": "a" * 64,
                },
                {
                    "tool_key": "sevenzip",
                    "source_type": "winget",
                    "package_id": "7zip.7zip",
                    "version": "24.00",
                },
                {
                    "tool_key": "renderdoc",
                    "source_type": "official_installer",
                    "version": "1.0",
                    "download_url": "https://renderdoc.org/example.exe",
                    "sha256": "b" * 64,
                },
            ],
        }
        result = validate_resolved_manifest(resolved, approval)
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["approval_manifest_sha256"], digest)

        tampered = copy.deepcopy(resolved)
        tampered["approval_manifest_sha256"] = "0" * 64
        with self.assertRaises(InstallManifestError):
            validate_resolved_manifest(tampered, approval)


if __name__ == "__main__":
    unittest.main()
