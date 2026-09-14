import json
import tempfile
import unittest
from pathlib import Path

import csmc_static_relevance_ranker as ranker


class RankerTests(unittest.TestCase):
    def test_direct_target_beats_high_fanin_runtime_helper(self):
        rows = [
            {
                "rank": "1",
                "score": "100000",
                "address": "1000",
                "name": "__security_check_cookie",
                "caller_count": "12000",
                "callee_count": "1",
                "targets": "",
                "reasons": "callee_of:2000",
            },
            {
                "rank": "200",
                "score": "800",
                "address": "2000",
                "name": "FUN_2000",
                "caller_count": "1",
                "callee_count": "8",
                "targets": "alpha",
                "reasons": "target_string:alpha, caller_of:3000",
            },
        ]
        ranked = ranker.rerank(rows)
        self.assertEqual(ranked[0]["address"], "2000")
        self.assertEqual(ranked[0]["semantic_promotion"], False)

    def test_unknown_high_fanin_is_downweighted_without_name_filter(self):
        low_fanin = {
            "score": "100",
            "address": "3000",
            "name": "FUN_3000",
            "caller_count": "1",
            "callee_count": "4",
            "targets": "",
            "reasons": "",
        }
        high_fanin = {
            "score": "100",
            "address": "4000",
            "name": "FUN_4000",
            "caller_count": "10000",
            "callee_count": "4",
            "targets": "",
            "reasons": "",
        }
        ranked = ranker.rerank([high_fanin, low_fanin])
        self.assertEqual(ranked[0]["address"], "3000")

    def test_cli_helpers_emit_blind_safe_metadata(self):
        rows = [
            {
                "rank": "7",
                "score": "42",
                "address": "5000",
                "name": "FUN_5000",
                "caller_count": "2",
                "callee_count": "3",
                "targets": "beta",
                "reasons": "raw_target:beta",
            }
        ]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            out = td / "out.tsv"
            meta = td / "meta.json"
            ranker.write_tsv(out, ranker.rerank(rows))
            ranker.write_metadata(meta, td / "input.tsv", ranker.rerank(rows))
            payload = json.loads(meta.read_text(encoding="utf-8"))
            self.assertTrue(payload["blind_safe"])
            self.assertFalse(payload["semantic_promotion"])
            self.assertFalse(payload["product_specific_constants"])
            self.assertIn("focused_score", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
