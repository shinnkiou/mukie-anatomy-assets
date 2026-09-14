#!/usr/bin/env python3
from __future__ import annotations
import re
from typing import Any, Iterable, Mapping

from csmc_serializer_field_read_gate import (
    apply_serializer_width_constraint,
    assess_serializer_field_read,
)

BRIDGE_SCHEMA_VERSION = "csmc_modeldata_serializer_bridge_evidence_v1"
EXPECTED_EXE_SHA256 = "2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150"
EXPECTED_SNAPSHOT_SHA256 = "afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342"
EXPECTED_SOURCE_ANCHOR = "C02"
EXPECTED_SOURCE_FUNCTION_VA = "0x140d45d30"
EXPECTED_CONSUMER_SCOPE = "MODELDATA_CONSUMER_PATH"
BRIDGE_EDGE_KINDS = {"DIRECT_CALL", "FACTORY_LOOKUP", "VTABLE_DISPATCH", "PROVENANCE_BOUND_INDIRECT"}
SHA_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
VA_RE = re.compile(r"^0x[0-9A-Fa-f]+$")
FORBIDDEN_KEYS = {
    "raw_bytes", "payload_bytes", "private_payload", "binary_blob", "base64",
    "raw_csmc", "raw_decompiler_dump", "raw_disassembly", "exe_bytes", "dll_bytes",
    "semantic_truth", "geometry_confirmed", "index_confirmed", "blender_ready",
}


def _nonempty(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _walk_keys(obj: Any):
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            yield str(k).lower()
            yield from _walk_keys(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _walk_keys(v)


def assess_modeldata_serializer_bridge(evidence: Mapping[str, Any] | None) -> dict[str, Any]:
    evidence = evidence or {}
    reasons: list[str] = []
    if evidence.get("schema_version") != BRIDGE_SCHEMA_VERSION:
        reasons.append("wrong bridge schema_version")
    if evidence.get("source_anchor_ref") != EXPECTED_SOURCE_ANCHOR:
        reasons.append("source_anchor_ref must be C02")
    if evidence.get("source_function_va") != EXPECTED_SOURCE_FUNCTION_VA:
        reasons.append("bridge must originate from the confirmed ModelData lookup function")
    target = evidence.get("target_reader_va")
    if not isinstance(target, str) or not VA_RE.fullmatch(target):
        reasons.append("target_reader_va must be a 0x-prefixed VA")
    if evidence.get("edge_kind") not in BRIDGE_EDGE_KINDS:
        reasons.append("edge_kind is not an admissible provenance bridge")
    if evidence.get("consumer_scope") != EXPECTED_CONSUMER_SCOPE:
        reasons.append("consumer_scope must be MODELDATA_CONSUMER_PATH")
    if evidence.get("exe_sha256") != EXPECTED_EXE_SHA256:
        reasons.append("MODELER executable SHA-256 mismatch")
    if evidence.get("snapshot_sha256") != EXPECTED_SNAPSHOT_SHA256:
        reasons.append("full snapshot SHA-256 mismatch")
    for name in ("evidence_id", "consumer_object_provenance", "negative_control"):
        if not _nonempty(evidence.get(name)):
            reasons.append(f"{name} must be non-empty")
    prov = evidence.get("provenance_hash")
    if not isinstance(prov, str) or not SHA_RE.fullmatch(prov):
        reasons.append("provenance_hash must be a 64-hex SHA-256")
    for guard in ("semantic_promotion", "blender_emit", "runtime_dispatch", "raw_private_bytes_embedded"):
        if evidence.get(guard) is not False:
            reasons.append(f"{guard} must remain false")
    bad = sorted(set(_walk_keys(evidence)) & FORBIDDEN_KEYS)
    if bad:
        reasons.append(f"forbidden private/promotion keys present: {bad}")
    admitted = not reasons
    return {
        "question_id": "DQ-BRIDGE-LOADER-SER-01",
        "status": "BRIDGE_ADMISSIBLE_NONSEMANTIC" if admitted else "WAIT_FOR_BRIDGE_PROOF",
        "bridge_admissible": admitted,
        "evidence_id": evidence.get("evidence_id") if admitted else None,
        "target_reader_va": target if admitted else None,
        "reasons": reasons,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
    }


def assess_provenance_bound_width(width_evidence: Mapping[str, Any] | None, bridge_evidence: Mapping[str, Any] | None) -> dict[str, Any]:
    bridge = assess_modeldata_serializer_bridge(bridge_evidence)
    if not bridge["bridge_admissible"]:
        return {
            "status": "WAIT_FOR_BRIDGE_PROOF",
            "bridge": bridge,
            "width_assessment": None,
            "candidate_pruning_allowed": False,
            "semantic_promotion": False,
            "blender_emit": False,
            "runtime_dispatch": False,
        }
    width_evidence = dict(width_evidence or {})
    reasons: list[str] = []
    if width_evidence.get("consumer_scope") != EXPECTED_CONSUMER_SCOPE:
        reasons.append("width evidence is outside MODELDATA_CONSUMER_PATH")
    if width_evidence.get("bridge_evidence_ref") != bridge["evidence_id"]:
        reasons.append("width evidence does not reference the admitted bridge")
    if width_evidence.get("function_va") != bridge["target_reader_va"]:
        reasons.append("width reader VA does not match the bridge target")
    if reasons:
        return {
            "status": "WIDTH_EVIDENCE_SCOPE_MISMATCH",
            "bridge": bridge,
            "width_assessment": None,
            "candidate_pruning_allowed": False,
            "reasons": reasons,
            "semantic_promotion": False,
            "blender_emit": False,
            "runtime_dispatch": False,
        }
    width = assess_serializer_field_read(width_evidence)
    return {
        "status": width["status"],
        "bridge": bridge,
        "width_assessment": width,
        "candidate_pruning_allowed": bool(width["candidate_pruning_allowed"]),
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
    }


def apply_provenance_bound_width_constraint(candidates: Iterable[Mapping[str, Any]], width_evidence: Mapping[str, Any] | None, bridge_evidence: Mapping[str, Any] | None) -> dict[str, Any]:
    rows = [dict(row) for row in candidates]
    admission = assess_provenance_bound_width(width_evidence, bridge_evidence)
    if not admission["candidate_pruning_allowed"]:
        return {
            "gate_status": admission["status"],
            "input_count": len(rows),
            "survivor_count": len(rows),
            "hard_reject_count": 0,
            "survivors": rows,
            "hard_rejects": [],
            "constraint_applied": False,
            "admission": admission,
            "semantic_promotion": False,
            "blender_emit": False,
            "runtime_dispatch": False,
        }
    result = apply_serializer_width_constraint(rows, width_evidence)
    result["admission"] = admission
    return result
