#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any, Mapping

SCHEMA_VERSION = "csmc_targeted_static_extraction_manifest_v1"
REQUEST_ID = "CSMC_TARGETED_STATIC_EXTRACTION_REQUEST_V1_20260914"
EXPECTED_EXE_SHA256 = "2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150"
BASELINE_SNAPSHOT_SHA256 = "afefd623f1eecdca1da692078230b41ea9c890b7aaa41985524001405dcc7342"
REQUIRED_FUNCTIONS = {
    "0x140f62d20",
    "0x140f64600",
    "0x140f650c0",
    "0x140f622f0",
    "0x140f63200",
    "0x140f635d0",
}
CONDITIONAL_FUNCTIONS = {"0x141658300", "0x1416586f0"}
FACTORY_TRACE_ROOT = "0x141656a80"
FACTORY_EDGE_KINDS = {
    "DIRECT_CALL",
    "FACTORY_LOOKUP",
    "VTABLE_DISPATCH",
    "PROVENANCE_BOUND_INDIRECT",
}
FACTORY_RESOLUTION_STATUSES = {
    "RESOLVED",
    "NO_PROVENANCE_BOUND_RESOLUTION",
}
VTABLE_INTERVALS = {
    "0x14195fad0": {
        "label": "PW3DModelDataLoader",
        "end": "0x14195fb18",
        "slots": 9,
    },
    "0x1417f6d30": {
        "label": "PWCanvas3DModelLoader",
        "end": "0x1417f6d78",
        "slots": 9,
    },
}
REQUIRED_GUARDS = {
    "semantic_promotion": False,
    "blender_emit": False,
    "runtime_dispatch": False,
    "modeler_runtime_started": False,
    "save_triggered": False,
    "hook_or_patch": False,
    "f02_runtime_observation": False,
    "proprietary_executable_embedded": False,
}
SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")
VA_RE = re.compile(r"^0x[0-9a-fA-F]+$")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA_RE.fullmatch(value))


def _valid_va(value: Any) -> bool:
    return isinstance(value, str) and bool(VA_RE.fullmatch(value))


def validate_targeted_static_manifest(manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate a private targeted static extraction package manifest.

    This is an intake-completeness gate only. Passing it never admits
    DQ-BRIDGE-LOADER-SER-01, EXPLICIT_SERIALIZER_FIELD_READ, or semantics.
    """
    m = dict(manifest or {})
    reasons: list[str] = []

    if m.get("schema_version") != SCHEMA_VERSION:
        reasons.append("wrong schema_version")
    if m.get("request_id") != REQUEST_ID:
        reasons.append("wrong request_id")

    exe_sha = m.get("source_binary_sha256")
    if not _valid_sha(exe_sha):
        reasons.append("source_binary_sha256 must be 64-hex")
    elif exe_sha.lower() != EXPECTED_EXE_SHA256:
        reasons.append("MODELER executable SHA-256 mismatch")

    baseline_sha = m.get("baseline_snapshot_sha256")
    if not _valid_sha(baseline_sha):
        reasons.append("baseline_snapshot_sha256 must be 64-hex")
    elif baseline_sha.lower() != BASELINE_SNAPSHOT_SHA256:
        reasons.append("baseline snapshot SHA-256 mismatch")

    for name in ("extraction_tool", "extraction_tool_version", "generated_at"):
        if not _nonempty(m.get(name)):
            reasons.append(f"{name} must be non-empty")

    if m.get("private_analysis_archive") is not True:
        reasons.append("private_analysis_archive must be true")
    if m.get("publication_allowed") is not False:
        reasons.append("publication_allowed must be false")

    guards = m.get("guards")
    if not isinstance(guards, Mapping):
        reasons.append("guards must be an object")
    else:
        for key, expected in REQUIRED_GUARDS.items():
            if guards.get(key) is not expected:
                reasons.append(f"guard {key} must be {expected}")

    functions_raw = m.get("functions")
    function_map: dict[str, Mapping[str, Any]] = {}
    if not isinstance(functions_raw, list):
        reasons.append("functions must be a list")
    else:
        for row in functions_raw:
            if not isinstance(row, Mapping):
                reasons.append("function record must be an object")
                continue
            va = row.get("va")
            if not _valid_va(va):
                reasons.append("function va must be 0x-prefixed")
                continue
            if va in function_map:
                reasons.append(f"duplicate function record: {va}")
                continue
            function_map[va] = row

        for va in sorted(REQUIRED_FUNCTIONS):
            row = function_map.get(va)
            if row is None:
                reasons.append(f"missing required function export: {va}")
                continue
            if row.get("decompile_present") is not True:
                reasons.append(f"{va} missing decompile")
            if row.get("instruction_listing_present") is not True:
                reasons.append(f"{va} missing instruction listing")
            if row.get("xrefs_exported") is not True:
                reasons.append(f"{va} missing xref export")
            if row.get("private_output") is not True:
                reasons.append(f"{va} must remain private_output=true")
            for field in ("decompile_sha256", "instruction_listing_sha256"):
                if not _valid_sha(row.get(field)):
                    reasons.append(f"{va} {field} must be 64-hex")

    intervals_raw = m.get("vtable_interval_exports")
    interval_map: dict[str, Mapping[str, Any]] = {}
    if not isinstance(intervals_raw, list):
        reasons.append("vtable_interval_exports must be a list")
    else:
        for row in intervals_raw:
            if not isinstance(row, Mapping):
                reasons.append("vtable interval record must be an object")
                continue
            start = row.get("start_va")
            if not _valid_va(start):
                reasons.append("vtable start_va must be 0x-prefixed")
                continue
            if start in interval_map:
                reasons.append(f"duplicate vtable interval: {start}")
                continue
            interval_map[start] = row

        expected_offsets = list(range(0, 72, 8))
        for start, spec in VTABLE_INTERVALS.items():
            row = interval_map.get(start)
            if row is None:
                reasons.append(f"missing vtable interval export: {start}")
                continue
            if row.get("label") != spec["label"]:
                reasons.append(f"{start} wrong vtable label")
            if row.get("end_va_exclusive") != spec["end"]:
                reasons.append(f"{start} wrong end_va_exclusive")
            if row.get("pointer_width_bytes") != 8:
                reasons.append(f"{start} pointer_width_bytes must be 8")
            slots = row.get("slots")
            if not isinstance(slots, list) or len(slots) != spec["slots"]:
                reasons.append(f"{start} must export exactly 9 slot records")
                continue
            offsets = []
            for slot in slots:
                if not isinstance(slot, Mapping):
                    reasons.append(f"{start} slot record must be an object")
                    continue
                offsets.append(slot.get("offset"))
                raw_value = slot.get("raw_value")
                if not isinstance(raw_value, str) or not raw_value:
                    reasons.append(f"{start} slot raw_value must be recorded")
            if offsets != expected_offsets:
                reasons.append(f"{start} slot offsets must be 0..64 step 8")

    trace = m.get("factory_trace")
    if not isinstance(trace, Mapping):
        reasons.append("factory_trace must be an object")
    else:
        if trace.get("root_va") != FACTORY_TRACE_ROOT:
            reasons.append("factory_trace root_va mismatch")
        status = trace.get("resolution_status")
        if status not in FACTORY_RESOLUTION_STATUSES:
            reasons.append("factory_trace resolution_status invalid")
        if not _nonempty(trace.get("negative_control")):
            reasons.append("factory_trace negative_control must be non-empty")
        edges = trace.get("edges")
        if not isinstance(edges, list):
            reasons.append("factory_trace edges must be a list")
        elif status == "RESOLVED":
            if not edges:
                reasons.append("resolved factory trace requires at least one edge")
            for edge in edges:
                if not isinstance(edge, Mapping):
                    reasons.append("factory edge must be an object")
                    continue
                if not _valid_va(edge.get("source_va")) or not _valid_va(edge.get("target_va")):
                    reasons.append("factory edge source/target VA invalid")
                if edge.get("edge_kind") not in FACTORY_EDGE_KINDS:
                    reasons.append("factory edge kind invalid")
                if not _nonempty(edge.get("evidence_instruction")):
                    reasons.append("factory edge evidence_instruction required")

    conditional = m.get("conditional_resolution")
    if not isinstance(conditional, Mapping):
        reasons.append("conditional_resolution must be an object")
    else:
        for va in sorted(CONDITIONAL_FUNCTIONS):
            row = conditional.get(va)
            if not isinstance(row, Mapping):
                reasons.append(f"conditional resolution missing: {va}")
                continue
            triggered = row.get("triggered")
            present = row.get("function_export_present")
            if not isinstance(triggered, bool) or not isinstance(present, bool):
                reasons.append(f"conditional resolution booleans invalid: {va}")
                continue
            if triggered and not present:
                reasons.append(f"conditional function triggered but export absent: {va}")
            if present:
                exported = function_map.get(va)
                if exported is None:
                    reasons.append(f"conditional function flagged present but record missing: {va}")
                else:
                    if exported.get("decompile_present") is not True or exported.get("instruction_listing_present") is not True:
                        reasons.append(f"conditional function export incomplete: {va}")

    complete = not reasons
    return {
        "status": "INTAKE_COMPLETE_STATIC_REVIEW_REQUIRED" if complete else "INTAKE_REJECTED",
        "intake_complete": complete,
        "static_review_required": complete,
        "bridge_admitted": False,
        "proof_grade": False,
        "explicit_serializer_field_read": "UNRESOLVED",
        "controlled_fixture_to_consumer_match": "UNRESOLVED",
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "reasons": reasons,
    }
