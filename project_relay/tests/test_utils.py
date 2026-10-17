from __future__ import annotations

import tempfile
import time
import unittest
import zipfile
from pathlib import Path

from project_relay.relay_utils import bounded_find, fresh_since, redact_secrets, validate_zip


class RelayUtilsTests(unittest.TestCase):
    def test_redact_secrets(self) -> None:
        text = "API_KEY=abc123\nAuthorization: Bearer topsecret\npassword=hunter2"
        redacted = redact_secrets(text)
        self.assertNotIn("abc123", redacted)
        self.assertNotIn("topsecret", redacted)
        self.assertNotIn("hunter2", redacted)
        self.assertGreaterEqual(redacted.count("<REDACTED_SECRET>"), 3)

    def test_bounded_find_respects_depth(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a").mkdir()
            (root / "a" / "one.zip").write_bytes(b"1")
            (root / "a" / "b").mkdir()
            (root / "a" / "b" / "two.zip").write_bytes(b"2")
            shallow = bounded_find([root], "*.zip", max_depth=1)
            deep = bounded_find([root], "*.zip", max_depth=3)
            self.assertEqual([p.name for p in shallow], ["one.zip"])
            self.assertEqual({p.name for p in deep}, {"one.zip", "two.zip"})

    def test_validate_zip_and_required_entries(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "result.zip"
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("result.json", "{}")
            info = validate_zip(path, ["result.json", "SUCCESS"])
            self.assertTrue(info["valid_zip"])
            self.assertTrue(info["crc_ok"])
            self.assertEqual(info["missing_required"], ["SUCCESS"])

    def test_fresh_since_rejects_old_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "old.txt"
            path.write_text("old", encoding="utf-8")
            start = time.time() + 5
            self.assertFalse(fresh_since(path, start, tolerance_seconds=0))


if __name__ == "__main__":
    unittest.main()
