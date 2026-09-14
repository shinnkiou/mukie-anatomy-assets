#!/usr/bin/env python3
from csmc_modeldata_serializer_bridge_gate import (
    EXPECTED_EXE_SHA256,
    EXPECTED_SNAPSHOT_SHA256,
    apply_provenance_bound_width_constraint,
    assess_modeldata_serializer_bridge,
    assess_provenance_bound_width,
)


def bridge():
    return {
        "schema_version": "csmc_modeldata_serializer_bridge_evidence_v1",
        "evidence_id": "SYNTH_BRIDGE_C02_TO_READER",
        "source_anchor_ref": "C02",
        "source_function_va": "0x140d45d30",
        "target_reader_va": "0x140000100",
        "edge_kind": "FACTORY_LOOKUP",
        "consumer_scope": "MODELDATA_CONSUMER_PATH",
        "consumer_object_provenance": "ModelData registry object -> Canvas3DModelLoader -> synthetic serializer reader",
        "negative_control": "BankData sibling route does not reach this reader",
        "provenance_hash": "b" * 64,
        "exe_sha256": EXPECTED_EXE_SHA256,
        "snapshot_sha256": EXPECTED_SNAPSHOT_SHA256,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "raw_private_bytes_embedded": False,
    }


def width(scope="MODELDATA_CONSUMER_PATH", width_bytes=2, bound=True):
    row = {
        "schema_version": "csmc_modeler_static_evidence_slice_v2",
        "lane": "MODELER_CONSUMER_SIDE_STATIC_ANALYSIS",
        "evidence_id": "SYNTH_WIDTH_PROOF",
        "evidence_class": "EXPLICIT_SERIALIZER_FIELD_READ",
        "confidence": "CONFIRMED",
        "evidence_source_kind": "SYNTHETIC_TEST_ONLY",
        "exe_sha256": EXPECTED_EXE_SHA256,
        "direct_edge_kind": "DIRECT_READ",
        "function_va": "0x140000100",
        "read_or_write_primitive_va": "0x140000120",
        "width_bytes": width_bytes,
        "endianness": "LE",
        "count_or_length_source": "synthetic_direct_bound",
        "destination_summary": "synthetic vector destination",
        "upstream_edge_summary": "synthetic bounded cursor",
        "downstream_edge_summary": "synthetic destination write",
        "negative_control": "synthetic sibling reader differs",
        "provenance_hash": "a" * 64,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "raw_private_bytes_embedded": False,
        "consumer_scope": scope,
        "bridge_evidence_ref": "SYNTH_BRIDGE_C02_TO_READER",
    }
    if bound:
        row["controlled_fixture_ref"] = "F02"
        row["field_label"] = "F02_DATA2_VARIABLE_PREFIX"
    return row


def run():
    candidates = [
        {"candidate_id": "M16", "consumer_scope": "MODELDATA_CONSUMER_PATH", "read_width": 2},
        {"candidate_id": "M32", "consumer_scope": "MODELDATA_CONSUMER_PATH", "read_width": 4},
        {"candidate_id": "NEG", "consumer_scope": "UNRELATED_RECORD_FAMILY", "read_width": 4},
    ]

    b = bridge()
    assert assess_modeldata_serializer_bridge(b)["bridge_admissible"] is True

    # The canonical width gate may be complete, but without a bridge it cannot prune.
    no_bridge = apply_provenance_bound_width_constraint(candidates, width(), None)
    assert no_bridge["constraint_applied"] is False
    assert no_bridge["survivor_count"] == 3

    # Provenance-bound 16-bit evidence can invoke the existing width gate.
    r16 = apply_provenance_bound_width_constraint(candidates, width(width_bytes=2), b)
    assert r16["constraint_applied"] is True
    assert r16["hard_reject_count"] == 1
    assert {r["candidate_id"] for r in r16["survivors"]} == {"M16", "NEG"}

    # Provenance-bound 32-bit evidence symmetrically prunes the 16-bit in-scope candidate.
    r32 = apply_provenance_bound_width_constraint(candidates, width(width_bytes=4), b)
    assert r32["constraint_applied"] is True
    assert {r["candidate_id"] for r in r32["survivors"]} == {"M32", "NEG"}

    # C-069 CHNKSQLi/ExternalChunk corridor cannot be relabeled into serializer width evidence.
    chunk = width(scope="CHNKSQLI_EXTERNALCHUNK_CORRIDOR", width_bytes=2)
    chunk_result = assess_provenance_bound_width(chunk, b)
    assert chunk_result["status"] == "WIDTH_EVIDENCE_SCOPE_MISMATCH"
    assert chunk_result["candidate_pruning_allowed"] is False

    # Candidate typed serializer names without an admitted bridge remain no-op.
    typed = width(scope="MODELDATA_CONSUMER_PATH", width_bytes=2)
    typed["bridge_evidence_ref"] = "UNPROVEN_TYPED_VTABLE"
    typed_result = assess_provenance_bound_width(typed, b)
    assert typed_result["candidate_pruning_allowed"] is False

    # Wrong source identity prevents bridge admission.
    bad_bridge = bridge(); bad_bridge["snapshot_sha256"] = "0" * 64
    assert assess_modeldata_serializer_bridge(bad_bridge)["bridge_admissible"] is False
    assert apply_provenance_bound_width_constraint(candidates, width(), bad_bridge)["constraint_applied"] is False

    for result in (r16, r32, no_bridge):
        assert result["semantic_promotion"] is False
        assert result["blender_emit"] is False
        assert result["runtime_dispatch"] is False

    print("MODELDATA_SERIALIZER_BRIDGE_GATE_PASS baseline=3 bound16=2 bound32=2")


if __name__ == "__main__":
    run()
