#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

QUESTION_ID = "DQ-SER-WIDTH-01"
STATIC_SCHEMA_VERSION = "csmc_modeler_static_evidence_slice_v2"
STATIC_LANE = "MODELER_CONSUMER_SIDE_STATIC_ANALYSIS"
EXPECTED_EXE_SHA256 = "2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150"
EVIDENCE_CLASS = "EXPLICIT_SERIALIZER_FIELD_READ"
TARGET_FIXTURE = "F02"
TARGET_FIELD_LABEL = "F02_DATA2_VARIABLE_PREFIX"
TARGET_CONSUMER_SCOPE = "MODELDATA_CONSUMER_PATH"
DECISIVE_WIDTHS = {2, 4}
DIRECT_READ_EDGE_KINDS = {
    "DIRECT_READ",
    "EXPLICIT_FIELD_ACCESS",
    "DIRECT_DATA_FLOW",
    "READER_WRITER_SYMMETRY",
}
ENDIANNESS = {"LE", "BE", "MIXED"}
VA_RE = re.compile(r"^0x[0-9A-Fa-f]+$")
SHA_RE = re.compile(r"^[0-9A-Fa-f]{64}$")

SERIALIZER_REQUIRED = {
    "schema_version",
    "lane",
    "evidence_id",
    "evidence_class",
    "confidence",
    "evidence_source_kind",
    "exe_sha256",
    "direct_edge_kind",
    "function_va",
    "read_or_write_primitive_va",
    "width_bytes",
    "endianness",
    "count_or_length_source",
    "destination_summary",
    "upstream_edge_summary",
    "downstream_edge_summary",
    "negative_control",
    "provenance_hash",
    "semantic_promotion",
    "blender_emit",
    "runtime_dispatch",
    "raw_private_bytes_embedded",
}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def assess_serializer_field_read(evidence: Mapping[str, Any] | None) -> dict[str, Any]:
    """Assess whether static evidence can answer DQ-SER-WIDTH-01.

    This gate deliberately distinguishes two questions:
    1) Is the direct reader width itself proof-grade and decisive (16 vs 32 bit)?
    2) Is that proof explicitly bound to the F02 DATA2 variable-prefix region so it may
       structurally prune F02 Importer Lab candidates?

    A positive answer to (1) never implies (2).
    """
    reasons: list[str] = []
    evidence = evidence or {}

    missing = sorted(
        key for key in SERIALIZER_REQUIRED
        if key not in evidence or evidence.get(key) in (None, "")
    )
    if missing:
        reasons.append(f"missing required serializer fields: {missing}")

    if evidence.get("schema_version") != STATIC_SCHEMA_VERSION:
        reasons.append("wrong static evidence schema_version")
    if evidence.get("lane") != STATIC_LANE:
        reasons.append("wrong static evidence lane")
    if evidence.get("evidence_class") != EVIDENCE_CLASS:
        reasons.append("wrong evidence_class")
    if evidence.get("confidence") != "CONFIRMED":
        reasons.append("hard width discriminator requires confidence=CONFIRMED")
    if evidence.get("direct_edge_kind") not in DIRECT_READ_EDGE_KINDS:
        reasons.append("direct_edge_kind is not a direct read/field/data-flow edge")

    exe_sha = evidence.get("exe_sha256")
    if not isinstance(exe_sha, str) or not SHA_RE.fullmatch(exe_sha):
        reasons.append("exe_sha256 must be a 64-hex SHA-256")
    elif exe_sha.lower() != EXPECTED_EXE_SHA256:
        reasons.append("MODELER executable SHA-256 mismatch")

    provenance = evidence.get("provenance_hash")
    if not isinstance(provenance, str) or not SHA_RE.fullmatch(provenance):
        reasons.append("provenance_hash must be a 64-hex SHA-256")

    for name in ("function_va", "read_or_write_primitive_va"):
        value = evidence.get(name)
        if not isinstance(value, str) or not VA_RE.fullmatch(value):
            reasons.append(f"{name} must be a 0x-prefixed virtual address")

    width = evidence.get("width_bytes")
    if width not in DECISIVE_WIDTHS:
        reasons.append("width_bytes must be exactly 2 or 4 for DQ-SER-WIDTH-01")

    if evidence.get("endianness") not in ENDIANNESS:
        reasons.append("endianness must be LE/BE/MIXED and cannot be NA")

    for name in (
        "evidence_id",
        "evidence_source_kind",
        "count_or_length_source",
        "destination_summary",
        "upstream_edge_summary",
        "downstream_edge_summary",
        "negative_control",
    ):
        if not _nonempty(evidence.get(name)):
            reasons.append(f"{name} must be non-empty")

    for guard in (
        "semantic_promotion",
        "blender_emit",
        "runtime_dispatch",
        "raw_private_bytes_embedded",
    ):
        if evidence.get(guard) is not False:
            reasons.append(f"{guard} must remain false")

    decisive = not reasons
    bound_to_f02 = (
        decisive
        and evidence.get("controlled_fixture_ref") == TARGET_FIXTURE
        and evidence.get("field_label") == TARGET_FIELD_LABEL
    )

    return {
        "question_id": QUESTION_ID,
        "status": (
            "DQ_RESOLVED_AND_F02_BOUND"
            if bound_to_f02
            else "DQ_RESOLVED_UNBOUND_TO_F02"
            if decisive
            else "WAIT_FOR_PROOF"
        ),
        "dq_decisive": decisive,
        "dq_answer_bits": width * 8 if decisive else None,
        "width_bytes": width if decisive else None,
        "f02_binding_confirmed": bound_to_f02,
        "candidate_pruning_allowed": bound_to_f02,
        "reasons": reasons,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "consumer_bonus": 0,
        "visual_score_delta": 0,
    }


def apply_serializer_width_constraint(
    candidates: Iterable[Mapping[str, Any]],
    evidence: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Apply a proof-bound width as a scope-aware falsification constraint only.

    Unresolved, non-CONFIRMED, wrong-binary, incomplete, or F02-unbound evidence is a
    strict no-op. Even when bound, only candidates in MODELDATA_CONSUMER_PATH are
    eligible for rejection. Unrelated scopes are preserved as negative controls.
    """
    rows = [dict(row) for row in candidates]
    assessment = assess_serializer_field_read(evidence)

    if not assessment["candidate_pruning_allowed"]:
        return {
            "question_id": QUESTION_ID,
            "gate_status": assessment["status"],
            "input_count": len(rows),
            "survivor_count": len(rows),
            "hard_reject_count": 0,
            "survivors": rows,
            "hard_rejects": [],
            "assessment": assessment,
            "constraint_applied": False,
            "semantic_promotion": False,
            "blender_emit": False,
            "runtime_dispatch": False,
        }

    width = assessment["width_bytes"]
    survivors: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in rows:
        in_scope = row.get("consumer_scope") == TARGET_CONSUMER_SCOPE
        claimed_width = row.get("read_width")
        if in_scope and claimed_width is not None and claimed_width != width:
            rejected.append({
                "candidate_id": str(row.get("candidate_id", "UNNAMED")),
                "reason": "CONTRADICTS_CONFIRMED_F02_DIRECT_READER_WIDTH",
                "candidate_read_width": claimed_width,
                "confirmed_read_width": width,
            })
        else:
            survivors.append(row)

    return {
        "question_id": QUESTION_ID,
        "gate_status": assessment["status"],
        "input_count": len(rows),
        "survivor_count": len(survivors),
        "hard_reject_count": len(rejected),
        "survivors": survivors,
        "hard_rejects": rejected,
        "assessment": assessment,
        "constraint_applied": True,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
    }
