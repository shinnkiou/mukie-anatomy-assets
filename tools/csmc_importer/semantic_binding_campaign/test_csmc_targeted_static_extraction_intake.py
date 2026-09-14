#!/usr/bin/env python3
from copy import deepcopy

from csmc_targeted_static_extraction_intake import (
    BASELINE_SNAPSHOT_SHA256,
    EXPECTED_EXE_SHA256,
    validate_targeted_static_manifest,
)


def _fn(va: str) -> dict:
    return {
        "va": va,
        "decompile_present": True,
        "instruction_listing_present": True,
        "xrefs_exported": True,
        "decompile_sha256": "a" * 64,
        "instruction_listing_sha256": "b" * 64,
        "private_output": True,
    }


def _slots() -> list[dict]:
    return [
        {"offset": offset, "raw_value": f"0x{0x140000000 + offset:016x}"}
        for offset in range(0, 72, 8)
    ]


def valid_manifest() -> dict:
    return {
        "schema_version": "csmc_targeted_static_extraction_manifest_v1",
        "request_id": "CSMC_TARGETED_STATIC_EXTRACTION_REQUEST_V1_20260914",
        "source_binary_sha256": EXPECTED_EXE_SHA256,
        "baseline_snapshot_sha256": BASELINE_SNAPSHOT_SHA256,
        "extraction_tool": "synthetic-test",
        "extraction_tool_version": "1",
        "generated_at": "2026-09-15T00:00:00+09:00",
        "private_analysis_archive": True,
        "publication_allowed": False,
        "functions": [
            _fn("0x140f62d20"),
            _fn("0x140f64600"),
            _fn("0x140f650c0"),
            _fn("0x140f622f0"),
            _fn("0x140f63200"),
            _fn("0x140f635d0"),
        ],
        "vtable_interval_exports": [
            {
                "label": "PW3DModelDataLoader",
                "start_va": "0x14195fad0",
                "end_va_exclusive": "0x14195fb18",
                "pointer_width_bytes": 8,
                "slots": _slots(),
            },
            {
                "label": "PWCanvas3DModelLoader",
                "start_va": "0x1417f6d30",
                "end_va_exclusive": "0x1417f6d78",
                "pointer_width_bytes": 8,
                "slots": _slots(),
            },
        ],
        "factory_trace": {
            "root_va": "0x141656a80",
            "resolution_status": "NO_PROVENANCE_BOUND_RESOLUTION",
            "edges": [],
            "negative_control": "synthetic complete search with no admitted edge",
        },
        "conditional_resolution": {
            "0x141658300": {"triggered": False, "function_export_present": False},
            "0x1416586f0": {"triggered": False, "function_export_present": False},
        },
        "guards": {
            "semantic_promotion": False,
            "blender_emit": False,
            "runtime_dispatch": False,
            "modeler_runtime_started": False,
            "save_triggered": False,
            "hook_or_patch": False,
            "f02_runtime_observation": False,
            "proprietary_executable_embedded": False,
        },
    }


def run() -> None:
    # A complete package can be accepted for review even when the bridge is not found.
    result = validate_targeted_static_manifest(valid_manifest())
    assert result["status"] == "INTAKE_COMPLETE_STATIC_REVIEW_REQUIRED"
    assert result["intake_complete"] is True
    assert result["static_review_required"] is True
    assert result["bridge_admitted"] is False
    assert result["proof_grade"] is False

    # Wrong binary identity fails closed.
    wrong = valid_manifest()
    wrong["source_binary_sha256"] = "c" * 64
    assert validate_targeted_static_manifest(wrong)["status"] == "INTAKE_REJECTED"

    # Missing required body/listing fails closed.
    missing_body = valid_manifest()
    missing_body["functions"][0]["decompile_present"] = False
    assert validate_targeted_static_manifest(missing_body)["intake_complete"] is False

    # Incomplete vtable interval dump fails closed.
    bad_slots = valid_manifest()
    bad_slots["vtable_interval_exports"][0]["slots"] = bad_slots["vtable_interval_exports"][0]["slots"][:-1]
    assert validate_targeted_static_manifest(bad_slots)["intake_complete"] is False

    # If a conditional target is triggered, its concrete function export becomes mandatory.
    conditional_missing = valid_manifest()
    conditional_missing["conditional_resolution"]["0x141658300"] = {
        "triggered": True,
        "function_export_present": False,
    }
    assert validate_targeted_static_manifest(conditional_missing)["intake_complete"] is False

    conditional_present = valid_manifest()
    conditional_present["conditional_resolution"]["0x141658300"] = {
        "triggered": True,
        "function_export_present": True,
    }
    conditional_present["functions"].append(_fn("0x141658300"))
    assert validate_targeted_static_manifest(conditional_present)["intake_complete"] is True

    # A resolved trace may pass intake completeness but still cannot auto-admit the bridge.
    resolved = valid_manifest()
    resolved["factory_trace"] = {
        "root_va": "0x141656a80",
        "resolution_status": "RESOLVED",
        "edges": [
            {
                "source_va": "0x141656a80",
                "target_va": "0x140f62d20",
                "edge_kind": "PROVENANCE_BOUND_INDIRECT",
                "evidence_instruction": "synthetic instruction evidence",
            }
        ],
        "negative_control": "synthetic sibling lookup does not reach target",
    }
    resolved_result = validate_targeted_static_manifest(resolved)
    assert resolved_result["intake_complete"] is True
    assert resolved_result["bridge_admitted"] is False
    assert resolved_result["proof_grade"] is False

    # Any safety-guard violation rejects the package.
    unsafe = valid_manifest()
    unsafe["guards"]["semantic_promotion"] = True
    assert validate_targeted_static_manifest(unsafe)["intake_complete"] is False

    print("TARGETED_STATIC_EXTRACTION_INTAKE_PASS cases=8 proof_grade=false bridge_admitted=false")


if __name__ == "__main__":
    run()
