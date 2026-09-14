import copy
import unittest

from static_evidence_slice_validator import (
    EXPECTED_EXE_SHA256,
    StaticEvidenceRejected,
    validate_slice,
)


def confirmed_serializer_slice():
    return {
        "schema_version": "csmc_modeler_static_evidence_slice_v2",
        "lane": "MODELER_CONSUMER_SIDE_STATIC_ANALYSIS",
        "evidence_id": "SYNTHETIC-FIELD-READ-001",
        "evidence_class": "EXPLICIT_SERIALIZER_FIELD_READ",
        "confidence": "CONFIRMED",
        "evidence_source_kind": "SYNTHETIC_UNIT_TEST",
        "exe_sha256": EXPECTED_EXE_SHA256,
        "direct_edge_kind": "DIRECT_READ",
        "caller_va": "0x140000100",
        "callee_va": "0x140000200",
        "function_va": "0x140000100",
        "class_or_template": "ODIChunkCellImporterT",
        "field_label": None,
        "read_or_write_primitive_va": "0x140000200",
        "width_bytes": 8,
        "endianness": "BE",
        "count_or_length_source": "bounded parent length field",
        "destination_summary": "synthetic destination field",
        "upstream_edge_summary": "synthetic bounded input cursor",
        "downstream_edge_summary": "synthetic destination use",
        "controlled_fixture_ref": None,
        "negative_control": "synthetic nearby unrelated reader excluded",
        "public_safe_pseudocode": "dst = read_be_u64(cursor)",
        "provenance_hash": "a" * 64,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "raw_private_bytes_embedded": False,
    }


class StaticEvidenceSliceValidatorTests(unittest.TestCase):
    def test_confirmed_serializer_slice_passes(self):
        result = validate_slice(confirmed_serializer_slice())
        self.assertTrue(result["proof_grade"])
        self.assertTrue(result["closes_requested_edge"])
        self.assertFalse(result["semantic_promotion"])

    def test_wrong_exe_hash_rejected(self):
        row = confirmed_serializer_slice()
        row["exe_sha256"] = "0" * 64
        with self.assertRaises(StaticEvidenceRejected):
            validate_slice(row)

    def test_raw_private_field_rejected_recursively(self):
        row = confirmed_serializer_slice()
        row["negative_control"] = {"raw_disassembly_dump": "private"}
        with self.assertRaises(StaticEvidenceRejected):
            validate_slice(row)

    def test_unknown_public_field_rejected(self):
        row = confirmed_serializer_slice()
        row["semantic_guess"] = "vertex"
        with self.assertRaises(StaticEvidenceRejected):
            validate_slice(row)

    def test_semantic_promotion_rejected(self):
        row = confirmed_serializer_slice()
        row["semantic_promotion"] = True
        with self.assertRaises(StaticEvidenceRejected):
            validate_slice(row)

    def test_confirmed_requires_direct_edge(self):
        row = confirmed_serializer_slice()
        row["direct_edge_kind"] = None
        with self.assertRaises(StaticEvidenceRejected):
            validate_slice(row)

    def test_confirmed_serializer_requires_width(self):
        row = confirmed_serializer_slice()
        row["width_bytes"] = None
        with self.assertRaises(StaticEvidenceRejected):
            validate_slice(row)

    def test_confirmed_serializer_rejects_na_endianness(self):
        row = confirmed_serializer_slice()
        row["endianness"] = "NA"
        with self.assertRaises(StaticEvidenceRejected):
            validate_slice(row)

    def test_candidate_can_be_recorded_without_proof_grade_edge(self):
        row = confirmed_serializer_slice()
        row["confidence"] = "CANDIDATE"
        row["direct_edge_kind"] = None
        row["read_or_write_primitive_va"] = None
        row["width_bytes"] = None
        row["endianness"] = None
        row["count_or_length_source"] = None
        row["destination_summary"] = None
        row["upstream_edge_summary"] = None
        row["downstream_edge_summary"] = None
        row["negative_control"] = None
        result = validate_slice(row)
        self.assertFalse(result["proof_grade"])
        self.assertFalse(result["closes_requested_edge"])

    def test_confirmed_fixture_match_requires_fixture_ref(self):
        row = confirmed_serializer_slice()
        row["evidence_class"] = "CONTROLLED_FIXTURE_TO_CONSUMER_MATCH"
        row["controlled_fixture_ref"] = None
        with self.assertRaises(StaticEvidenceRejected):
            validate_slice(row)

    def test_invalid_va_rejected(self):
        row = confirmed_serializer_slice()
        row["function_va"] = "140000100"
        with self.assertRaises(StaticEvidenceRejected):
            validate_slice(row)

    def test_runtime_dispatch_must_remain_false(self):
        row = confirmed_serializer_slice()
        row["runtime_dispatch"] = True
        with self.assertRaises(StaticEvidenceRejected):
            validate_slice(row)


if __name__ == "__main__":
    unittest.main()
