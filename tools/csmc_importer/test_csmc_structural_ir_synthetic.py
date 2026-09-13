#!/usr/bin/env python3
from __future__ import annotations

from csmc_structural_ir import SCHEMA_VERSION, validate_ir

SHA_A = "a" * 64
SHA_B = "b" * 64


def fixture():
    return {
        "schema_version": SCHEMA_VERSION,
        "source": {"clip_sha256": SHA_A, "csmc_sha256": SHA_B, "raw_bytes_embedded": False},
        "ir_axes": ["length_blocks", "preserve_signature", "boundary_class"],
        "boundaries": [
            {
                "id": "BND_LOCAL",
                "class": "local_extinction",
                "from_delta_blocks": 197,
                "to_delta_blocks": 195,
                "net_relative_size_bytes": -16,
                "barrier_matches_old_delta": 0,
                "barrier_matches_new_delta": 0,
                "complete_cross_serialization_extinction": True,
                "semantic_owner": "unresolved",
            },
            {
                "id": "BND_REPACK",
                "class": "mixed_reuse_repack",
                "from_delta_blocks": 1000,
                "to_delta_blocks": 2000,
                "net_relative_size_bytes": 8000,
                "barrier_matches_old_delta": 3,
                "barrier_matches_new_delta": 4,
                "complete_cross_serialization_extinction": False,
                "semantic_owner": "unresolved",
            },
        ],
        "record_families": [
            {"length_blocks": 48, "preserve_signature": "0000110", "count": 7, "semantic_record_type": "unresolved"},
            {"length_blocks": 48, "preserve_signature": "0000111", "count": 3, "semantic_record_type": "unresolved"},
            {"length_blocks": 48, "preserve_signature": "0001110", "count": 3, "semantic_record_type": "unresolved"},
            {"length_blocks": 49, "preserve_signature": "0000111", "count": 3, "semantic_record_type": "unresolved"},
            {"length_blocks": 49, "preserve_signature": "1000111", "count": 6, "semantic_record_type": "unresolved"},
        ],
        "semantic_claims": {
            "geometry": "unresolved",
            "index_buffer": "unresolved",
            "uv": "unresolved",
            "material": "unresolved",
            "texture": "unresolved",
            "bone_hierarchy": "unresolved",
            "bind_pose": "unresolved",
            "bone_indices": "unresolved",
            "skin_weights": "unresolved",
        },
        "guardrails": {
            "public_safe": True,
            "aggregate_only": True,
            "contains_raw_payload": False,
            "contains_literal_qwords": False,
            "blender_import_proven": False,
        },
    }


def test_valid():
    assert validate_ir(fixture()) == []


def test_axes_cannot_collapse():
    doc = fixture()
    doc["ir_axes"] = ["record_class"]
    assert any("independent axes" in e for e in validate_ir(doc))


def test_semantics_must_remain_unresolved():
    doc = fixture()
    doc["semantic_claims"]["geometry"] = "mesh"
    assert any("semantic_claims.geometry" in e for e in validate_ir(doc))


def test_raw_fields_rejected():
    doc = fixture()
    doc["boundaries"][0]["qword_value"] = "deadbeef"
    assert any("forbidden raw/private field" in e for e in validate_ir(doc))


def test_record_family_axes_independent():
    doc = fixture()
    pairs = {(r["length_blocks"], r["preserve_signature"]) for r in doc["record_families"]}
    assert (48, "0000111") in pairs and (49, "0000111") in pairs
    assert len({r["preserve_signature"] for r in doc["record_families"] if r["length_blocks"] == 48}) > 1


if __name__ == "__main__":
    test_valid()
    test_axes_cannot_collapse()
    test_semantics_must_remain_unresolved()
    test_raw_fields_rejected()
    test_record_family_axes_independent()
    print("CSMC structural IR synthetic tests PASS")
