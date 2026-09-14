#!/usr/bin/env python3
"""Fail-closed non-semantic intake for Importer Lab candidates.

This module deliberately does not decide semantics. It only admits public-safe,
provenance-bound STRUCTURAL_CANDIDATE / CODEC_CANDIDATE handoffs into the
mainline's oracle-independent development path.
"""
from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION = "csmc_lab_candidate_handoff_v1"
ALLOWED_CANDIDATE_KINDS = {"STRUCTURAL_CANDIDATE", "CODEC_CANDIDATE"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

FORBIDDEN_KEYS = {
    "raw_bytes",
    "payload_bytes",
    "private_payload",
    "binary_blob",
    "base64",
    "semantic_claim",
    "confirmed_semantics",
    "geometry_semantic",
    "index_semantic",
    "uv_semantic",
    "material_semantic",
    "bone_semantic",
    "weight_semantic",
}

REQUIRED_SAFETY = {
    "semantic_promotion": False,
    "blender_emit": False,
    "runtime_dispatch": False,
    "diagnostic_only": True,
}


def _walk_keys(value: Any, path: str = "$"):
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_s = str(key)
            child_path = f"{path}.{key_s}"
            yield key_s, child_path
            yield from _walk_keys(child, child_path)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            yield from _walk_keys(child, f"{path}[{idx}]")


def _require_nonempty_string(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def validate_and_admit(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one Lab handoff and return a semantics-free admission receipt.

    The receipt authorizes only structural/codec diagnostic intake. It cannot be
    used as semantic proof and never authorizes runtime or Blender output.
    """
    if not isinstance(record, Mapping):
        raise ValueError("candidate record must be a mapping")

    if record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported candidate schema_version")

    candidate_id = _require_nonempty_string(record, "candidate_id")
    candidate_kind = _require_nonempty_string(record, "candidate_kind")
    if candidate_kind not in ALLOWED_CANDIDATE_KINDS:
        raise ValueError(f"candidate_kind not allowed: {candidate_kind}")

    producer_lane = _require_nonempty_string(record, "producer_lane")
    if producer_lane != "IMPORTER_LAB":
        raise ValueError("producer_lane must be IMPORTER_LAB")

    source_run_key = _require_nonempty_string(record, "source_run_key")
    source_sha256 = _require_nonempty_string(record, "source_sha256")
    if not SHA256_RE.fullmatch(source_sha256):
        raise ValueError("source_sha256 must be lowercase 64-hex")

    generation = record.get("generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise ValueError("generation must be a non-negative integer")

    family = _require_nonempty_string(record, "family")
    payload = record.get("candidate_payload")
    if not isinstance(payload, Mapping) or not payload:
        raise ValueError("candidate_payload must be a non-empty mapping")

    safety = record.get("safety")
    if not isinstance(safety, Mapping):
        raise ValueError("safety must be a mapping")
    for key, expected in REQUIRED_SAFETY.items():
        if safety.get(key) is not expected:
            raise ValueError(f"safety.{key} must be {expected}")

    for key, path in _walk_keys(record):
        if key.lower() in FORBIDDEN_KEYS:
            raise ValueError(f"forbidden field at {path}")

    evidence_refs = record.get("evidence_refs", [])
    if not isinstance(evidence_refs, list):
        raise ValueError("evidence_refs must be a list")
    for index, ref in enumerate(evidence_refs):
        if not isinstance(ref, Mapping):
            raise ValueError(f"evidence_refs[{index}] must be a mapping")
        if not isinstance(ref.get("type"), str) or not isinstance(ref.get("id"), str):
            raise ValueError(f"evidence_refs[{index}] requires string type and id")

    downstream_scope = (
        "STRUCTURAL_IR_CANDIDATE_ONLY"
        if candidate_kind == "STRUCTURAL_CANDIDATE"
        else "CODEC_DIAGNOSTIC_CANDIDATE_ONLY"
    )

    return {
        "schema_version": "csmc_mainline_candidate_intake_receipt_v1",
        "intake_status": "ADMITTED_NON_SEMANTIC_REFERENCE_ONLY",
        "candidate_id": candidate_id,
        "candidate_kind": candidate_kind,
        "producer_lane": producer_lane,
        "source_run_key": source_run_key,
        "source_sha256": source_sha256,
        "generation": generation,
        "family": family,
        "candidate_payload": deepcopy(dict(payload)),
        "evidence_refs": deepcopy(evidence_refs),
        "downstream_scope": downstream_scope,
        "semantic_projection": False,
        "semantic_promotion": False,
        "proof_grade": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "physical_oracle_required_for_intake": False,
        "independent_evidence_required_for_semantic_promotion": True,
        "mainline_state": "ACTIVE",
        "pipeline_stage": "STRUCTURAL_ONLY",
    }


if __name__ == "__main__":
    sample = {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": "SYNTHETIC-STRUCT-001",
        "candidate_kind": "STRUCTURAL_CANDIDATE",
        "producer_lane": "IMPORTER_LAB",
        "source_run_key": "SYNTHETIC",
        "source_sha256": "a" * 64,
        "generation": 0,
        "family": "RELATIONSHIP_ONLY",
        "candidate_payload": {"region": "synthetic", "relation": "bounded"},
        "evidence_refs": [{"type": "synthetic", "id": "fixture-1"}],
        "safety": dict(REQUIRED_SAFETY),
    }
    receipt = validate_and_admit(sample)
    assert receipt["semantic_promotion"] is False
    assert receipt["mainline_state"] == "ACTIVE"
    print("SELF_TEST_PASS")
