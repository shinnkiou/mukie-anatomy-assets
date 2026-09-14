import unittest

from tools.csmc_importer.importer_lab.lab_core import (
    ManifestRejected,
    dedupe_manifests,
    genotype_hash,
    make_synthetic_manifest,
    phenotype_hash,
    score_candidate,
    validate_gen0_plan,
    validate_holdout_ledger,
    validate_manifest,
)
from tools.csmc_importer.importer_lab.synthetic_runner import run_synthetic_batch


class ImporterLabM0M1Tests(unittest.TestCase):
    def test_valid_manifest(self):
        validate_manifest(make_synthetic_manifest())

    def test_semantic_assertion_rejected(self):
        with self.assertRaises(ManifestRejected):
            validate_manifest(make_synthetic_manifest(candidate_semantic="VERTEX"))

    def test_whole_payload_scope_rejected(self):
        with self.assertRaises(ManifestRejected):
            validate_manifest(make_synthetic_manifest(source_scope="WHOLE_PAYLOAD"))

    def test_absolute_offset_field_rejected(self):
        m = make_synthetic_manifest()
        m["absolute_offset"] = 1234
        with self.assertRaises(ManifestRejected):
            validate_manifest(m)

    def test_three_field_mutation_rejected(self):
        with self.assertRaises(ManifestRejected):
            validate_manifest(make_synthetic_manifest(mutation_fields=["a", "b", "c"]))

    def test_allowed_coupled_mutation(self):
        validate_manifest(make_synthetic_manifest(mutation_fields=["element_type", "endianness"]))

    def test_genotype_dedupe_ignores_candidate_id(self):
        a = make_synthetic_manifest("A")
        b = make_synthetic_manifest("B")
        self.assertEqual(genotype_hash(a), genotype_hash(b))
        unique, dupes = dedupe_manifests([a, b])
        self.assertEqual(len(unique), 1)
        self.assertEqual(dupes, ["B"])

    def test_genotype_changes_on_structural_parameter(self):
        a = make_synthetic_manifest("A")
        b = make_synthetic_manifest("B", relative_offset_bytes=4)
        self.assertNotEqual(genotype_hash(a), genotype_hash(b))

    def test_phenotype_hash_is_behavioral(self):
        a = {"parsed_ranges": [[0, 8]], "element_counts": {"x": 2}, "relationship_outcomes": {"r": True}}
        b = dict(a)
        b["comment"] = "ignored"
        self.assertEqual(phenotype_hash(a), phenotype_hash(b))

    def test_parse_success_gets_no_direct_points(self):
        result = score_candidate({"parse_valid": True, "hard_constraints_pass": True})
        self.assertEqual(result["score"], 0.0)

    def test_visual_and_numeric_plausibility_do_not_score(self):
        result = score_candidate({
            "parse_valid": True,
            "hard_constraints_pass": True,
            "visual_similarity": 1.0,
            "generic_numeric_plausibility": 1.0,
        })
        self.assertEqual(result["score"], 0.0)

    def test_full_frozen_score_is_100(self):
        metrics = {"parse_valid": True, "hard_constraints_pass": True}
        for key in ["controlled_differential", "withheld_validation", "negative_controls", "structural_consistency", "consumer_evidence", "simplicity"]:
            metrics[key] = 1.0
        self.assertEqual(score_candidate(metrics)["score"], 100.0)

    def test_v01_locked_audit_ledger(self):
        validate_holdout_ledger({"V01": {"role": "LOCKED_AUDIT_SET", "pristine_holdout": False}, "semantic_promotion": False})

    def test_v01_cannot_be_called_pristine(self):
        with self.assertRaises(ManifestRejected):
            validate_holdout_ledger({"V01": {"role": "LOCKED_AUDIT_SET", "pristine_holdout": True}, "semantic_promotion": False})

    def test_gen0_frozen_family_plan(self):
        validate_gen0_plan({
            "candidate_family_counts": {
                "LOCAL_BOUNDARY_LENGTH": 14,
                "COUNT_SCALAR_CODEC": 10,
                "LOCAL_RECORD_LAYOUT": 10,
                "CROSS_BLOCK_RELATIONSHIP": 6,
                "REFERENCE_DOMAIN": 5,
                "NEGATIVE_CONTROL": 5,
            },
            "semantic_scope": "UNRESOLVED_LOCAL_SUBBLOCK_GRAMMAR_ONLY",
            "private_csmc_execution": False,
        })

    def test_batch_limit(self):
        with self.assertRaises(ManifestRejected):
            dedupe_manifests([make_synthetic_manifest(str(i), relative_offset_bytes=i % 65) for i in range(51)])

    def test_synthetic_runner_pass_crash_timeout(self):
        manifests = [
            make_synthetic_manifest("PASS", relative_offset_bytes=0),
            make_synthetic_manifest("CRASH", relative_offset_bytes=4),
            make_synthetic_manifest("TIMEOUT", relative_offset_bytes=8),
        ]
        result = run_synthetic_batch(
            manifests,
            behaviors={"PASS": "PASS", "CRASH": "RAISE", "TIMEOUT": "SLEEP"},
            concurrency=2,
            timeout_s=0.15,
        )
        statuses = {row["candidate_id"]: row["status"] for row in result["results"]}
        self.assertEqual(statuses["PASS"], "OK")
        self.assertEqual(statuses["CRASH"], "CRASH_ISOLATED")
        self.assertEqual(statuses["TIMEOUT"], "TIMEOUT")
        self.assertFalse(result["semantic_promotion"])
        self.assertFalse(result["blender_emit"])

    def test_deterministic_replay(self):
        manifests = [make_synthetic_manifest("A", relative_offset_bytes=0), make_synthetic_manifest("B", relative_offset_bytes=4)]
        a = run_synthetic_batch(manifests, concurrency=1)
        b = run_synthetic_batch(manifests, concurrency=2)
        self.assertEqual(a["replay_fingerprint"], b["replay_fingerprint"])

    def test_concurrency_above_two_rejected(self):
        with self.assertRaises(ValueError):
            run_synthetic_batch([make_synthetic_manifest()], concurrency=3)


if __name__ == "__main__":
    unittest.main()
