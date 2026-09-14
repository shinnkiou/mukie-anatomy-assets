#!/usr/bin/env python3
from csmc_consumer_constrained_lab import (
    dedupe_survivors,
    generate_consumer_constrained_synthetic_50,
)
from csmc_serializer_field_read_gate import (
    EXPECTED_EXE_SHA256,
    apply_serializer_width_constraint,
    assess_serializer_field_read,
)


def confirmed_slice(width=2, bound=False):
    row = {
        "schema_version": "csmc_modeler_static_evidence_slice_v2",
        "lane": "MODELER_CONSUMER_SIDE_STATIC_ANALYSIS",
        "evidence_id": "SYNTHETIC_DQ_WIDTH_PROOF",
        "evidence_class": "EXPLICIT_SERIALIZER_FIELD_READ",
        "confidence": "CONFIRMED",
        "evidence_source_kind": "SYNTHETIC_TEST_ONLY",
        "exe_sha256": EXPECTED_EXE_SHA256,
        "direct_edge_kind": "DIRECT_READ",
        "function_va": "0x140000100",
        "read_or_write_primitive_va": "0x140000120",
        "width_bytes": width,
        "endianness": "LE",
        "count_or_length_source": "synthetic_direct_bound",
        "destination_summary": "synthetic vector destination",
        "upstream_edge_summary": "synthetic bounded input cursor",
        "downstream_edge_summary": "synthetic destination write",
        "negative_control": "synthetic sibling path uses different reader",
        "provenance_hash": "a" * 64,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "raw_private_bytes_embedded": False,
    }
    if bound:
        row["controlled_fixture_ref"] = "F02"
        row["field_label"] = "F02_DATA2_VARIABLE_PREFIX"
    return row


def current_survivors():
    base = dedupe_survivors(generate_consumer_constrained_synthetic_50())
    assert base["input_count"] == 50
    assert base["hard_reject_count"] == 3
    assert base["duplicate_count"] == 4
    assert base["survivor_count"] == 43
    return [item["candidate"] for item in base["survivors"]]


def run():
    candidates = current_survivors()

    # No proof is a strict no-op.
    waiting = apply_serializer_width_constraint(candidates, None)
    assert waiting["gate_status"] == "WAIT_FOR_PROOF"
    assert waiting["constraint_applied"] is False
    assert waiting["survivor_count"] == 43
    assert waiting["hard_reject_count"] == 0

    # A complete CONFIRMED read can answer 16-vs-32 structurally, but without an
    # explicit F02 binding it must not prune the F02 hypothesis population.
    unbound = confirmed_slice(width=2, bound=False)
    assessment = assess_serializer_field_read(unbound)
    assert assessment["dq_decisive"] is True
    assert assessment["dq_answer_bits"] == 16
    assert assessment["f02_binding_confirmed"] is False
    result = apply_serializer_width_constraint(candidates, unbound)
    assert result["gate_status"] == "DQ_RESOLVED_UNBOUND_TO_F02"
    assert result["constraint_applied"] is False
    assert result["survivor_count"] == 43

    # Explicit F02 binding permits scope-aware falsification only.
    bound16 = confirmed_slice(width=2, bound=True)
    result16 = apply_serializer_width_constraint(candidates, bound16)
    assert result16["gate_status"] == "DQ_RESOLVED_AND_F02_BOUND"
    assert result16["constraint_applied"] is True
    assert result16["hard_reject_count"] > 0
    assert result16["survivor_count"] < 43
    for row in result16["survivors"]:
        if row.get("consumer_scope") == "MODELDATA_CONSUMER_PATH" and row.get("read_width") is not None:
            assert row["read_width"] == 2
    # Unrelated-scope negative controls are intentionally preserved even when they
    # carry a contradictory width value.
    assert any(
        row.get("consumer_scope") == "UNRELATED_RECORD_FAMILY" and row.get("read_width") != 2
        for row in result16["survivors"]
    )

    bound32 = confirmed_slice(width=4, bound=True)
    result32 = apply_serializer_width_constraint(candidates, bound32)
    assert result32["constraint_applied"] is True
    assert result32["hard_reject_count"] > 0
    for row in result32["survivors"]:
        if row.get("consumer_scope") == "MODELDATA_CONSUMER_PATH" and row.get("read_width") is not None:
            assert row["read_width"] == 4

    # STRONG is recordable elsewhere but is not sufficient for this hard width
    # discriminator. Wrong binary identity is also a strict no-op.
    strong = confirmed_slice(width=2, bound=True)
    strong["confidence"] = "STRONG"
    assert assess_serializer_field_read(strong)["dq_decisive"] is False
    assert apply_serializer_width_constraint(candidates, strong)["survivor_count"] == 43

    wrong_binary = confirmed_slice(width=2, bound=True)
    wrong_binary["exe_sha256"] = "b" * 64
    assert assess_serializer_field_read(wrong_binary)["dq_decisive"] is False
    assert apply_serializer_width_constraint(candidates, wrong_binary)["survivor_count"] == 43

    # An unsupported width does not silently answer the binary discriminator.
    width8 = confirmed_slice(width=8, bound=True)
    assert assess_serializer_field_read(width8)["dq_decisive"] is False
    assert apply_serializer_width_constraint(candidates, width8)["constraint_applied"] is False

    for result in (waiting, result16, result32):
        assert result["semantic_promotion"] is False
        assert result["blender_emit"] is False
        assert result["runtime_dispatch"] is False

    print(
        "DQ_SER_WIDTH_GATE_PASS",
        "baseline=43",
        f"bound16_survivors={result16['survivor_count']}",
        f"bound32_survivors={result32['survivor_count']}",
    )


if __name__ == "__main__":
    run()
