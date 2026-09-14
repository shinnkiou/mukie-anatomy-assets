from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Mapping

SCHEMA_VERSION = "csmc_modeler_static_evidence_slice_v2"
LANE = "MODELER_CONSUMER_SIDE_STATIC_ANALYSIS"
EXPECTED_EXE_SHA256 = "2EBE2D90F8609496CB2E81A7C9DEFAE4E851479B8E5DB76EB9DD8EC05D943150"

EVIDENCE_CLASSES = {
    "EXPLICIT_CSMC_HANDLER_ENTRY",
    "EXPLICIT_EXTERNALCHUNK_OFFSET_LOOKUP",
    "EXPLICIT_MODELDATA_LOOKUP",
    "EXPLICIT_CANVAS3D_LOAD_ENTRY",
    "EXPLICIT_SERIALIZER_FIELD_READ",
    "EXPLICIT_INTERNAL_MODEL_CONSTRUCTION",
    "CONTROLLED_FIXTURE_TO_CONSUMER_MATCH",
}
CONFIDENCE = {"CONFIRMED", "STRONG", "CANDIDATE", "REJECTED"}
DIRECT_EDGE_KINDS = {
    "DIRECT_CALL",
    "DIRECT_READ",
    "DIRECT_WRITE",
    "EXPLICIT_REGISTRY_LOOKUP",
    "EXPLICIT_FACTORY_SELECTION",
    "EXPLICIT_FIELD_ACCESS",
    "READER_WRITER_SYMMETRY",
    "DIRECT_DATA_FLOW",
}
ENDIANNESS = {"LE", "BE", "MIXED", "NA"}

PUBLIC_SAFE_FIELDS = {
    "schema_version",
    "lane",
    "evidence_id",
    "evidence_class",
    "confidence",
    "evidence_source_kind",
    "exe_sha256",
    "direct_edge_kind",
    "caller_va",
    "callee_va",
    "function_va",
    "class_or_template",
    "field_label",
    "read_or_write_primitive_va",
    "width_bytes",
    "endianness",
    "count_or_length_source",
    "destination_summary",
    "upstream_edge_summary",
    "downstream_edge_summary",
    "controlled_fixture_ref",
    "negative_control",
    "public_safe_pseudocode",
    "provenance_hash",
    "semantic_promotion",
    "blender_emit",
    "runtime_dispatch",
    "raw_private_bytes_embedded",
}

FORBIDDEN_FIELDS = {
    "raw_exe_bytes",
    "raw_dll_bytes",
    "raw_decompiler_dump",
    "raw_disassembly_dump",
    "private_csmc_payload",
    "purchased_model_bytes",
    "credentials",
    "license_or_activation_data",
}

BASE_REQUIRED = {
    "schema_version",
    "lane",
    "evidence_id",
    "evidence_class",
    "confidence",
    "evidence_source_kind",
    "exe_sha256",
    "provenance_hash",
    "semantic_promotion",
    "blender_emit",
    "runtime_dispatch",
    "raw_private_bytes_embedded",
}

SERIALIZER_CONFIRMED_REQUIRED = {
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
}

FIXTURE_MATCH_CONFIRMED_REQUIRED = {
    "controlled_fixture_ref",
    "direct_edge_kind",
    "upstream_edge_summary",
    "downstream_edge_summary",
    "negative_control",
    "provenance_hash",
}

VA_RE = re.compile(r"^0x[0-9A-Fa-f]+$")
SHA_RE = re.compile(r"^[0-9A-Fa-f]{64}$")


class StaticEvidenceRejected(ValueError):
    pass


def _walk_keys(value: Any):
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_fields(record: Mapping[str, Any], fields: set[str], context: str) -> None:
    missing = sorted(name for name in fields if name not in record or record[name] in (None, ""))
    if missing:
        raise StaticEvidenceRejected(f"{context} missing required fields: {missing}")


def _validate_sha(name: str, value: Any) -> None:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise StaticEvidenceRejected(f"{name} must be a 64-hex SHA-256")


def _validate_va(name: str, value: Any) -> None:
    if value in (None, ""):
        return
    if not isinstance(value, str) or not VA_RE.fullmatch(value):
        raise StaticEvidenceRejected(f"{name} must be a 0x-prefixed virtual address")


def validate_slice(record: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, Mapping):
        raise StaticEvidenceRejected("evidence slice must be an object")

    forbidden = sorted(FORBIDDEN_FIELDS & set(_walk_keys(record)))
    if forbidden:
        raise StaticEvidenceRejected(f"forbidden private/raw fields present: {forbidden}")

    unknown = sorted(set(record) - PUBLIC_SAFE_FIELDS)
    if unknown:
        raise StaticEvidenceRejected(f"unknown public fields rejected: {unknown}")

    _require_fields(record, BASE_REQUIRED, "evidence slice")

    if record["schema_version"] != SCHEMA_VERSION:
        raise StaticEvidenceRejected("wrong schema_version")
    if record["lane"] != LANE:
        raise StaticEvidenceRejected("wrong lane")
    if not _nonempty(record["evidence_id"]):
        raise StaticEvidenceRejected("evidence_id must be non-empty")
    if not _nonempty(record["evidence_source_kind"]):
        raise StaticEvidenceRejected("evidence_source_kind must be non-empty")
    if record["evidence_class"] not in EVIDENCE_CLASSES:
        raise StaticEvidenceRejected("unsupported evidence_class")
    if record["confidence"] not in CONFIDENCE:
        raise StaticEvidenceRejected("unsupported confidence")

    _validate_sha("exe_sha256", record["exe_sha256"])
    if record["exe_sha256"].upper() != EXPECTED_EXE_SHA256:
        raise StaticEvidenceRejected("MODELER executable SHA-256 mismatch")
    _validate_sha("provenance_hash", record["provenance_hash"])

    for guard in (
        "semantic_promotion",
        "blender_emit",
        "runtime_dispatch",
        "raw_private_bytes_embedded",
    ):
        if record[guard] is not False:
            raise StaticEvidenceRejected(f"{guard} must remain false")

    for name in ("caller_va", "callee_va", "function_va", "read_or_write_primitive_va"):
        _validate_va(name, record.get(name))

    direct_kind = record.get("direct_edge_kind")
    if direct_kind not in (None, "") and direct_kind not in DIRECT_EDGE_KINDS:
        raise StaticEvidenceRejected("invalid direct_edge_kind")

    width = record.get("width_bytes")
    if width is not None:
        if not isinstance(width, int) or isinstance(width, bool) or width <= 0 or width > 64:
            raise StaticEvidenceRejected("width_bytes must be an integer in 1..64 or null")

    endian = record.get("endianness")
    if endian is not None and endian not in ENDIANNESS:
        raise StaticEvidenceRejected("endianness must be LE/BE/MIXED/NA or null")

    if record["confidence"] in {"CONFIRMED", "STRONG"}:
        if direct_kind not in DIRECT_EDGE_KINDS:
            raise StaticEvidenceRejected("CONFIRMED/STRONG evidence requires a direct_edge_kind")
        if not any(record.get(name) for name in ("caller_va", "callee_va", "function_va")):
            raise StaticEvidenceRejected("CONFIRMED/STRONG evidence requires a provenance-bound function address")
        if not _nonempty(record.get("negative_control")):
            raise StaticEvidenceRejected("CONFIRMED/STRONG evidence requires a negative_control")

    if record["evidence_class"] == "EXPLICIT_SERIALIZER_FIELD_READ" and record["confidence"] == "CONFIRMED":
        _require_fields(record, SERIALIZER_CONFIRMED_REQUIRED, "confirmed serializer field read")
        if direct_kind not in {"DIRECT_READ", "EXPLICIT_FIELD_ACCESS", "DIRECT_DATA_FLOW", "READER_WRITER_SYMMETRY"}:
            raise StaticEvidenceRejected("confirmed serializer field read needs a read/field/data-flow edge")
        if record.get("endianness") == "NA":
            raise StaticEvidenceRejected("confirmed serializer field read cannot use endianness=NA")

    if record["evidence_class"] == "CONTROLLED_FIXTURE_TO_CONSUMER_MATCH" and record["confidence"] in {"CONFIRMED", "STRONG"}:
        _require_fields(record, FIXTURE_MATCH_CONFIRMED_REQUIRED, "controlled fixture consumer match")

    proof_grade = record["confidence"] in {"CONFIRMED", "STRONG"}
    closes_requested_edge = proof_grade and record["evidence_class"] == "EXPLICIT_SERIALIZER_FIELD_READ"
    return {
        "accepted": True,
        "schema_version": SCHEMA_VERSION,
        "evidence_id": record["evidence_id"],
        "evidence_class": record["evidence_class"],
        "confidence": record["confidence"],
        "proof_grade": proof_grade,
        "closes_requested_edge": closes_requested_edge,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "public_safe_only": True,
    }


def validate_file(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return validate_slice(data)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Validate a public-safe MODELER static evidence slice.")
    ap.add_argument("evidence_json", type=Path)
    args = ap.parse_args()
    print(json.dumps(validate_file(args.evidence_json), indent=2, sort_keys=True))
