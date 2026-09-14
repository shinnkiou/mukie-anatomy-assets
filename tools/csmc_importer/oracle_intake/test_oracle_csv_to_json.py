import csv
import tempfile
import unittest
from pathlib import Path

from oracle_csv_to_json import build_observation_from_csv
from oracle_intake import OracleIntakeRejected


FIELDS = [
    "variant_id",
    "filename",
    "source_offset",
    "structural_region",
    "variant_file_sha256",
    "variant_character_blob_sha256",
    "oracle_result",
    "visible_effect",
    "error_class",
    "process_survival",
    "evidence_strength",
    "save_action_performed",
    "observer_session_id",
    "observed_at",
    "error_text_sha256",
    "load_time_ms",
    "affected_visible_component",
    "viewport_result_sha256",
    "screenshot_sha256",
]


def synthetic_manifest():
    variants = []
    for i in range(1, 31):
        variants.append(
            {
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
            }
        )
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


def csv_row(manifest, i=1, **overrides):
    source = manifest["variants"][i - 1]
    value = {
        "variant_id": source["variant_id"],
        "filename": f"fixture-{i}.csmc",
        "source_offset": source["payload_relative_offset"],
        "structural_region": source["region"],
        "variant_file_sha256": source["file_sha256"],
        "variant_character_blob_sha256": source["character_blob_sha256"],
        "oracle_result": "LOAD_ACCEPTED",
        "visible_effect": "VISIBLE_MODEL_UNCHANGED",
        "error_class": "NONE",
        "process_survival": "SURVIVED",
        "evidence_strength": "DIRECT_PHYSICAL_OBSERVATION",
        "save_action_performed": "FALSE",
        "observer_session_id": "TEST-SESSION",
        "observed_at": "2026-09-14T18:30:00+09:00",
        "error_text_sha256": "",
        "load_time_ms": "12.5",
        "affected_visible_component": "",
        "viewport_result_sha256": "",
        "screenshot_sha256": "",
    }
    value.update(overrides)
    return value


class OracleCsvToJsonTests(unittest.TestCase):
    def setUp(self):
        self.manifest = synthetic_manifest()
        self.tmp = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.tmp.name) / "obs.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def write_rows(self, rows):
        with self.csv_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def test_partial_direct_row_converts(self):
        self.write_rows([csv_row(self.manifest)])
        obs = build_observation_from_csv(self.manifest, self.csv_path, require_complete=False)
        self.assertEqual(len(obs["observations"]), 1)
        self.assertEqual(obs["observations"][0]["variant_id"], "M01")
        self.assertFalse(obs["save_actions_performed"])

    def test_save_true_rejected(self):
        self.write_rows([csv_row(self.manifest, save_action_performed="TRUE")])
        with self.assertRaises(OracleIntakeRejected):
            build_observation_from_csv(self.manifest, self.csv_path, require_complete=False)

    def test_wrong_provenance_hash_rejected(self):
        self.write_rows([csv_row(self.manifest, variant_file_sha256="f" * 64)])
        with self.assertRaises(OracleIntakeRejected):
            build_observation_from_csv(self.manifest, self.csv_path, require_complete=False)

    def test_blank_result_with_other_observation_data_rejected(self):
        self.write_rows(
            [csv_row(self.manifest, oracle_result="", visible_effect="VISIBLE_MODEL_CHANGED")]
        )
        with self.assertRaises(OracleIntakeRejected):
            build_observation_from_csv(self.manifest, self.csv_path, require_complete=False)

    def test_unobserved_template_row_is_skipped_for_partial(self):
        self.write_rows(
            [
                csv_row(
                    self.manifest,
                    oracle_result="",
                    visible_effect="",
                    error_class="",
                    process_survival="",
                    evidence_strength="",
                    observer_session_id="",
                    observed_at="",
                    load_time_ms="",
                )
            ]
        )
        obs = build_observation_from_csv(self.manifest, self.csv_path, require_complete=False)
        self.assertEqual(obs["observations"], [])

    def test_empty_full_observation_rejected(self):
        self.write_rows(
            [
                csv_row(
                    self.manifest,
                    oracle_result="",
                    visible_effect="",
                    error_class="",
                    process_survival="",
                    evidence_strength="",
                    observer_session_id="",
                    observed_at="",
                    load_time_ms="",
                )
            ]
        )
        with self.assertRaises(OracleIntakeRejected):
            build_observation_from_csv(self.manifest, self.csv_path, require_complete=True)


if __name__ == "__main__":
    unittest.main()
