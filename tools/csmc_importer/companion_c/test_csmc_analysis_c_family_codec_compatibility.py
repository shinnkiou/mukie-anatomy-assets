#!/usr/bin/env python3

import unittest

from csmc_analysis_c_family_codec_compatibility import (
    evaluate_default_matrix,
    evaluate_family_wide_role,
)


class FamilyCodecCompatibilityTests(unittest.TestCase):
    def test_q21_only_size_three_families_remain_family_wide_compatible(self):
        result = evaluate_default_matrix()["CONTROL_ZONE_Q21"]
        self.assertEqual(
            result["compatible_family_ids"],
            ["F48_0000111", "F48_0001110", "F49_0000111"],
        )
        self.assertEqual(
            result["eliminated_family_ids"],
            ["F48_0000110", "F49_1000111"],
        )
        self.assertEqual(result["compatible_record_count_if_family_wide"], 9)

    def test_q25_excludes_only_size_seven_family(self):
        result = evaluate_default_matrix()["PRESERVED_ISLAND_Q25"]
        self.assertEqual(result["eliminated_family_ids"], ["F48_0000110"])
        self.assertEqual(result["compatible_record_count_if_family_wide"], 15)

    def test_q0_whole_record_keeps_all_families(self):
        result = evaluate_default_matrix()["WHOLE_RECORD_Q0"]
        self.assertEqual(result["eliminated_family_ids"], [])
        self.assertEqual(result["compatible_record_count_if_family_wide"], 22)

    def test_q0_stable_prefix_keeps_all_families(self):
        result = evaluate_default_matrix()["STABLE_PREFIX_Q0"]
        self.assertEqual(result["eliminated_family_ids"], [])
        self.assertEqual(result["compatible_record_count_if_family_wide"], 22)

    def test_compatibility_never_confirms_binding_or_semantics(self):
        for result in evaluate_default_matrix().values():
            self.assertFalse(result["binding_confirmed"])
            self.assertFalse(result["semantic_promotion"])

    def test_primary_preregistered_scan_surface_is_never_reduced(self):
        for result in evaluate_default_matrix().values():
            self.assertFalse(result["primary_preregistered_scan_surface_reduced"])

    def test_missing_surface_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_family_wide_role("X", {"A": 7})

    def test_negative_or_boolean_ceiling_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_family_wide_role("X", {"A": 7, "B": -1})
        with self.assertRaises(ValueError):
            evaluate_family_wide_role("X", {"A": True, "B": 7})

    def test_invalid_family_size_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_family_wide_role("X", {"A": 7, "B": 7}, {"F": 0})


if __name__ == "__main__":
    unittest.main()
