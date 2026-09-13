#!/usr/bin/env python3

import unittest

from csmc_analysis_c_i2_residual_patch import (
    SIG_A,
    SIG_B,
    TRUSTED_QUOTA,
    validate_residual_patch,
)

ASSIGNMENT = {
    2: SIG_A,
    3: SIG_A,
    8: SIG_A,
    14: SIG_B,
    15: SIG_B,
    21: SIG_B,
}


def q24_observations(omit=None):
    return [
        {
            "record_index": index,
            "position": "q24",
            "equal_bit": 0 if signature == SIG_A else 1,
        }
        for index, signature in ASSIGNMENT.items()
        if index != omit
    ]


def base_manifest(observations):
    return {
        "side_lane_isolated": True,
        "provenance_hash": "a" * 64,
        "corpus_id": "public-safe-plus965-aggregate",
        "container_route": "character",
        "regime_id": "plus965",
        "auto_semantic_promotion": False,
        "auto_blender_emit": False,
        "observations": observations,
    }


class I2ResidualPatchTests(unittest.TestCase):
    def test_six_q24_observations_close_gap(self):
        out = validate_residual_patch(base_manifest(q24_observations()))
        self.assertTrue(out["accepted"])
        self.assertTrue(out["residual_gap_closed"])
        self.assertIsNone(out["quota_derived_record_index"])

    def test_six_q27_observations_are_equivalent(self):
        observations = [
            {
                "record_index": index,
                "position": "q27",
                "equal_bit": 1 if signature == SIG_A else 0,
            }
            for index, signature in ASSIGNMENT.items()
        ]
        out = validate_residual_patch(base_manifest(observations))
        self.assertTrue(out["accepted"])
        self.assertEqual(out["resolved_signatures"]["2"], SIG_A)
        self.assertEqual(out["resolved_signatures"]["21"], SIG_B)

    def test_five_observations_plus_trusted_quota_derive_sixth(self):
        manifest = base_manifest(q24_observations(omit=21))
        manifest.update(
            use_trusted_quota_assist=True,
            trusted_signature_quota=TRUSTED_QUOTA,
            quota_provenance_hash="b" * 64,
        )
        out = validate_residual_patch(manifest)
        self.assertTrue(out["accepted"])
        self.assertEqual(out["quota_derived_record_index"], 21)
        self.assertEqual(out["quota_derived_signature"], SIG_B)

    def test_five_observations_without_quota_assist_reject(self):
        out = validate_residual_patch(base_manifest(q24_observations(omit=21)))
        self.assertFalse(out["accepted"])

    def test_bad_quota_provenance_rejects(self):
        manifest = base_manifest(q24_observations(omit=21))
        manifest.update(
            use_trusted_quota_assist=True,
            trusted_signature_quota=TRUSTED_QUOTA,
            quota_provenance_hash="bad",
        )
        self.assertFalse(validate_residual_patch(manifest)["accepted"])

    def test_duplicate_record_rejects(self):
        observations = q24_observations()
        observations[-1]["record_index"] = 2
        self.assertFalse(validate_residual_patch(base_manifest(observations))["accepted"])

    def test_non_residual_record_rejects(self):
        observations = q24_observations()
        observations[-1]["record_index"] = 20
        self.assertFalse(validate_residual_patch(base_manifest(observations))["accepted"])

    def test_boolean_equality_bit_rejects(self):
        observations = q24_observations()
        observations[-1]["equal_bit"] = True
        self.assertFalse(validate_residual_patch(base_manifest(observations))["accepted"])

    def test_raw_payload_field_rejects(self):
        manifest = base_manifest(q24_observations())
        manifest["raw_bytes"] = "forbidden"
        self.assertFalse(validate_residual_patch(manifest)["accepted"])

    def test_bad_provenance_rejects(self):
        manifest = base_manifest(q24_observations())
        manifest["provenance_hash"] = "bad"
        self.assertFalse(validate_residual_patch(manifest)["accepted"])

    def test_six_observations_that_break_3_3_quota_reject(self):
        observations = q24_observations()
        observations[-1]["equal_bit"] = 0
        self.assertFalse(validate_residual_patch(base_manifest(observations))["accepted"])


if __name__ == "__main__":
    unittest.main()
