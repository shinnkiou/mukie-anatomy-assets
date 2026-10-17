import hashlib
import pathlib
import tempfile
import unittest
import zipfile
from unittest import mock

from bridge import blender_bootstrap
from bridge import blender_selector


class BlenderSelectorTests(unittest.TestCase):
    def test_exact_pin_is_selected_over_other_versions(self):
        rows = [
            {"exists": True, "path": "old", "usable": True, "version": "3.4.1", "version_line": "Blender 3.4.1", "return_code": 0, "is_pinned": False},
            {"exists": True, "path": "pin", "usable": True, "version": blender_selector.PIN, "version_line": f"Blender {blender_selector.PIN}", "return_code": 0, "is_pinned": True},
        ]
        with mock.patch.object(blender_selector, "_candidate_paths", return_value=[pathlib.Path("old"), pathlib.Path("pin")]), \
             mock.patch.object(blender_selector, "_probe", side_effect=rows):
            selected = blender_selector.select_pinned_blender()
        self.assertTrue(selected["found"])
        self.assertEqual(selected["path"], "pin")
        self.assertEqual(selected["version"], blender_selector.PIN)
        self.assertEqual(selected["alternatives"][0]["version"], "3.4.1")

    def test_other_version_only_is_not_accepted(self):
        row = {"exists": True, "path": "old", "usable": True, "version": "3.4.1", "version_line": "Blender 3.4.1", "return_code": 0, "is_pinned": False}
        with mock.patch.object(blender_selector, "_candidate_paths", return_value=[pathlib.Path("old")]), \
             mock.patch.object(blender_selector, "_probe", return_value=row):
            selected = blender_selector.select_pinned_blender()
        self.assertFalse(selected["found"])
        self.assertEqual(selected["required_version"], blender_selector.PIN)
        self.assertEqual(selected["alternatives"][0]["version"], "3.4.1")


class BlenderBootstrapTests(unittest.TestCase):
    def test_expected_sha_extracts_only_windows_zip_hash(self):
        expected = "a" * 64
        text = f"{'b'*64}  blender-4.2.23-linux-x64.tar.xz\n{expected}  {blender_bootstrap.ZIP_NAME}\n"
        self.assertEqual(blender_bootstrap._expected_sha(text), expected)

    def test_safe_extract_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("../escape.txt", b"bad")
            with self.assertRaises(blender_bootstrap.BlenderBootstrapError):
                blender_bootstrap._safe_extract(archive, root / "dest")

    def test_safe_extract_allows_expected_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            archive = root / "ok.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr(f"blender-{blender_selector.PIN}-windows-x64/blender.exe", b"fixture")
            destination = root / "dest"
            blender_bootstrap._safe_extract(archive, destination)
            self.assertTrue((destination / f"blender-{blender_selector.PIN}-windows-x64" / "blender.exe").is_file())

    def test_bootstrap_returns_existing_pin_without_download(self):
        existing = {"found": True, "path": "C:/pin/blender.exe", "version": blender_selector.PIN}
        with mock.patch.object(blender_bootstrap, "select_pinned_blender", return_value=existing), \
             mock.patch.object(blender_bootstrap, "_download") as download:
            result = blender_bootstrap.bootstrap_pinned_blender()
        self.assertEqual(result["status"], "ALREADY_INSTALLED")
        self.assertFalse(result["download_performed"])
        download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
