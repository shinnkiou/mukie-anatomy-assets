import copy
import unittest

from tools.csmc_importer.oracle_intake.oracle_intake import (
    OracleIntakeRejected,
    SOURCE_MANIFEST_SHA256,
    public_safe_projection,
    validate_oracle_observation,
    validate_source_manifest,
)


def synthetic_manifest():
    variants = []
    for i in range(1, 31):
        variants.append({
            "variant_id": f"M{i:02d}",
            "payload_relative_offset": i * 8,
            "region": "PREFIX_INTERIOR" if i <= 10 else "INVARIANT_BOUNDARY",
            "file_sha256": f"{i:064x}"[-64:],
            "character_blob_sha256": f"{(i + 100):064x}"[-64:],
            "character_blob_diff_byte_count": 1,
            "xor_mask_hex": "01",
            "sqlite_readback_ok": True,
            "frame_rule_still_holds": True,
            "modeler_load_result": "PENDING_MANUAL_ORACLE",
        })
    return {
        "batch_id": "CSMC_F02_SINGLE_BYTE_XOR01_30_20260914",
        "base_fixture": "CSMC_F02_QUAD",
        "variant_count": 30,
        "mutation_rule": "exactly one character-BLOB byte XOR 0x01 per variant",
        "raw_bytes_embedded": False,
        "semantic_promotion": False,
        "runtime_dispatch": False,
        "variants": variants,
    }


def observation_from_manifest(manifest):
    rows = []
    for source in manifest["variants"]:
        rows.append({
            "variant_id": source["variant_id"],
            "source_offset": source["payload_relative_offset"],
            "structural_region": source["region"],
            "variant_file_sha256": source["file_sha256"],
            "variant_character_blob_sha256": source["character_blob_sha256"],
            "oracle_result": "LOAD_ACCEPTED",
            "visible_effect": "VISIBLE_MODEL_UNCHANGED",
            "error_class": "NONE",
            "error_text_sha256": None,
            "load_time_ms": 12.5,
            "affected_visible_component": None,
            "viewport_result_sha256": "a" * 64,
            "screenshot_sha256": None,
            "process_survival": "SURVIVED",
            "evidence_strength": "DIRECT_PHYSICAL_OBSERVATION",
            "save_action_performed": False,
            "observer_session_id": "SYNTHETIC-SESSION",
            "observed_at": "2026-09-14T17:30:00+09:00",
        })
    return {
        "schema_version": "csmc_f02_mutation_oracle_30_v1",
        "source_batch_id": "CSMC_F02_SINGLE_BYTE_XOR01_30_20260914",
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "save_actions_performed": False,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_mutation": False,
        "observations": rows,
    }


class OracleIntakeTests(unittest.TestCase):
    def setUp(self):
        self.manifest = synthetic_manifest()
        self.obs = observation_from_manifest(self.manifest)

    def test_source_manifest_accepts_bound_hash_argument(self):
        self.assertEqual(len(validate_source_manifest(self.manifest, SOURCE_MANIFEST_SHA256)), 30)

    def test_wrong_manifest_hash_rejected(self):
        with self.assertRaises(OracleIntakeRejected):
            validate_source_manifest(self.manifest, "0" * 64)

    def test_complete_observation_accepted(self):
        result = validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)
        self.assertTrue(result["complete"])
        self.assertEqual(result["observed_count"], 30)
        self.assertEqual(result["classification"], "PHYSICAL_ORACLE_COMPLETE")

    def test_missing_row_rejected_for_complete(self):
        self.obs["observations"].pop()
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_partial_checkpoint_allowed_only_when_requested(self):
        self.obs["observations"] = self.obs["observations"][:9]
        result = validate_oracle_observation(
            self.manifest, SOURCE_MANIFEST_SHA256, self.obs, require_complete=False
        )
        self.assertFalse(result["complete"])
        self.assertEqual(result["classification"], "PHYSICAL_ORACLE_PARTIAL_CHECKPOINT")

    def test_duplicate_variant_rejected(self):
        self.obs["observations"][1] = copy.deepcopy(self.obs["observations"][0])
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_wrong_source_offset_rejected(self):
        self.obs["observations"][0]["source_offset"] += 1
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_wrong_variant_hash_rejected(self):
        self.obs["observations"][0]["variant_file_sha256"] = "f" * 64
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_save_action_rejected_per_row(self):
        self.obs["observations"][0]["save_action_performed"] = True
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_save_action_rejected_session_level(self):
        self.obs["save_actions_performed"] = True
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_semantic_field_rejected(self):
        self.obs["observations"][0]["candidate_semantic"] = "VERTEX"
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_semantic_promotion_must_remain_false(self):
        self.obs["semantic_promotion"] = True
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_blender_emit_must_remain_false(self):
        self.obs["blender_emit"] = True
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_runtime_mutation_must_remain_false(self):
        self.obs["runtime_mutation"] = True
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_crash_process_survival_conflict_rejected(self):
        row = self.obs["observations"][0]
        row["oracle_result"] = "CRASH"
        row["process_survival"] = "SURVIVED"
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_load_reject_visible_comparison_conflict_rejected(self):
        row = self.obs["observations"][0]
        row["oracle_result"] = "LOAD_REJECTED"
        row["visible_effect"] = "VISIBLE_MODEL_CHANGED"
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)

    def test_public_projection_strips_private_and_save_fields(self):
        self.obs["observations"][0]["byte_before_hex"] = "aa"
        self.obs["observations"][0]["byte_after_hex"] = "ab"
        projected = public_safe_projection(self.obs)
        row = projected["observations"][0]
        self.assertNotIn("byte_before_hex", row)
        self.assertNotIn("byte_after_hex", row)
        self.assertNotIn("save_action_performed", row)
        self.assertTrue(row["xor01_verified_from_source_manifest"])
        self.assertFalse(projected["semantic_promotion"])

    def test_invalid_sha_rejected(self):
        self.obs["observations"][0]["screenshot_sha256"] = "not-a-hash"
        with self.assertRaises(OracleIntakeRejected):
            validate_oracle_observation(self.manifest, SOURCE_MANIFEST_SHA256, self.obs)


if __name__ == "__main__":
    unittest.main()
