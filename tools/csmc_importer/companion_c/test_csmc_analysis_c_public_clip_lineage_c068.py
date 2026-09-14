from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from csmc_analysis_c_public_clip_lineage_c068 import (
    PublicClipSourceLineageRejected,
    reconcile_public_clip_source_lineage,
)


HERE = Path(__file__).resolve().parent
RECORD = HERE / "CSMC_ANALYSIS_C_PUBLIC_CLIP_SOURCE_LINEAGE_C068_20260914.json"


class C068SourceLineageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = json.loads(RECORD.read_text(encoding="utf-8"))

    def test_canonical_record_passes(self) -> None:
        result = reconcile_public_clip_source_lineage(self.base)
        self.assertEqual(result["guaranteed_origin_independent_source_count"], 0)
        self.assertEqual(result["known_origin_dependent_source_count"], 3)
        self.assertEqual(result["origin_independence_unknown_source_count"], 2)
        self.assertEqual(result["empirical_revalidation_source_count"], 3)
        self.assertTrue(result["structural_prior_retained"])
        self.assertFalse(result["source_count_may_be_used_as_independent_vote_count"])

    def test_rejects_independence_vote_inflation(self) -> None:
        bad = copy.deepcopy(self.base)
        bad["independence_accounting"]["guaranteed_origin_independent_source_count"] = 1
        with self.assertRaises(PublicClipSourceLineageRejected):
            reconcile_public_clip_source_lineage(bad)

    def test_rejects_wamsoft_as_origin_independent(self) -> None:
        bad = copy.deepcopy(self.base)
        row = next(x for x in bad["pinned_sources"] if x["repo"] == "wamsoft/clipparse")
        row["origin_independence"] = "INDEPENDENT"
        with self.assertRaises(PublicClipSourceLineageRejected):
            reconcile_public_clip_source_lineage(bad)

    def test_rejects_missing_wamsoft_starting_point(self) -> None:
        bad = copy.deepcopy(self.base)
        row = next(x for x in bad["pinned_sources"] if x["repo"] == "wamsoft/clipparse")
        row["upstream_sources"] = []
        with self.assertRaises(PublicClipSourceLineageRejected):
            reconcile_public_clip_source_lineage(bad)

    def test_rejects_clip_clai_lineage_erasure(self) -> None:
        bad = copy.deepcopy(self.base)
        row = next(x for x in bad["pinned_sources"] if x["repo"] == "youichi-uda/clip-clai")
        row["upstream_sources"] = ["Inochi2D/clip-d"]
        with self.assertRaises(PublicClipSourceLineageRejected):
            reconcile_public_clip_source_lineage(bad)

    def test_rejects_semantic_promotion(self) -> None:
        bad = copy.deepcopy(self.base)
        bad["prior_effect"]["semantic_promotion_count"] = 1
        with self.assertRaises(PublicClipSourceLineageRejected):
            reconcile_public_clip_source_lineage(bad)

    def test_rejects_direct_csmc_proof(self) -> None:
        bad = copy.deepcopy(self.base)
        bad["prior_effect"]["direct_csmc_evidence"] = True
        with self.assertRaises(PublicClipSourceLineageRejected):
            reconcile_public_clip_source_lineage(bad)

    def test_rejects_public_names_guiding_blind_discovery(self) -> None:
        bad = copy.deepcopy(self.base)
        bad["isolation"]["public_names_may_guide_blind_discovery"] = True
        with self.assertRaises(PublicClipSourceLineageRejected):
            reconcile_public_clip_source_lineage(bad)

    def test_rejects_physical_oracle_fabrication(self) -> None:
        bad = copy.deepcopy(self.base)
        bad["prior_effect"]["physical_f02_oracle_observations"] = 1
        with self.assertRaises(PublicClipSourceLineageRejected):
            reconcile_public_clip_source_lineage(bad)


if __name__ == "__main__":
    unittest.main()
