#!/usr/bin/env python3
"""Fail-closed bridge from importer structural intake to validated Structural IR.

The bridge does not infer boundaries, record families, or field semantics from
cadence alone. It accepts a separately validated ``csmc_structural_ir_v0_1``
document only when its CSMC SHA matches the importer-side source SHA. The
result is an importer-facing bundle that preserves all semantic gates as
unresolved and keeps Blender emission disabled.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from csmc_structural_ir import validate_ir

SCHEMA_VERSION = "csmc_importer_ir_bridge_v0_1"
REQUIRED_MODE = "STRUCTURAL_ONLY"
REQUIRED_CANDIDATE = "TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE"


class ImporterIRBridgeError(ValueError):
    pass


def _copy(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _intake_csmc_sha(intake: Mapping[str, Any]) -> str:
    source = intake.get("source")
    if not isinstance(source, Mapping):
        raise ImporterIRBridgeError("intake.source object required")
    sha = source.get("file_sha256")
    if not isinstance(sha, str) or len(sha) != 64:
        raise ImporterIRBridgeError("intake source SHA-256 required")
    return sha.lower()


def build_bridge(*, intake: Mapping[str, Any], structural_ir: Mapping[str, Any]) -> dict[str, Any]:
    """Join two independently validated structural products without semantic promotion."""
    intake_doc = _copy(intake)
    ir_doc = _copy(structural_ir)

    if intake_doc.get("mode") != REQUIRED_MODE:
        raise ImporterIRBridgeError("intake must remain STRUCTURAL_ONLY")
    if intake_doc.get("semantic_promotion_count") != 0:
        raise ImporterIRBridgeError("intake semantic promotion count must be zero")
    if intake_doc.get("semantic_projection") is not False:
        raise ImporterIRBridgeError("intake semantic projection must be disabled")
    if intake_doc.get("runtime_dispatch") is not False:
        raise ImporterIRBridgeError("intake runtime dispatch must be disabled")
    if intake_doc.get("blender_emit_ready") is not False:
        raise ImporterIRBridgeError("intake Blender emit must be disabled")

    errors = validate_ir(ir_doc)
    if errors:
        raise ImporterIRBridgeError("invalid structural IR: " + "; ".join(errors))

    intake_sha = _intake_csmc_sha(intake_doc)
    ir_source = ir_doc.get("source")
    assert isinstance(ir_source, dict)
    ir_sha = ir_source.get("csmc_sha256")
    if ir_sha != intake_sha:
        raise ImporterIRBridgeError("CSMC SHA mismatch between importer intake and structural IR")

    candidates = intake_doc.get("accepted_structural_candidates")
    if not isinstance(candidates, list):
        raise ImporterIRBridgeError("accepted_structural_candidates list required")
    accepted_ids = {
        row.get("evidence_id")
        for row in candidates
        if isinstance(row, Mapping) and isinstance(row.get("evidence_id"), str)
    }
    if accepted_ids and accepted_ids != {REQUIRED_CANDIDATE}:
        raise ImporterIRBridgeError("unexpected structural candidate set")

    semantics = ir_doc["semantic_claims"]
    if any(value != "unresolved" for value in semantics.values()):
        raise ImporterIRBridgeError("Structural IR semantics must remain unresolved")

    return {
        "schema_version": SCHEMA_VERSION,
        "mode": REQUIRED_MODE,
        "source": {
            "csmc_sha256": intake_sha,
            "clip_sha256": ir_source["clip_sha256"],
            "raw_bytes_embedded": False,
        },
        "importer_intake_schema": intake_doc.get("schema_version"),
        "structural_ir_schema": ir_doc.get("schema_version"),
        "accepted_structural_candidates": candidates,
        "consumer_side_evidence": intake_doc.get("consumer_side_evidence", {}),
        "controlled_fixture_to_consumer_match": intake_doc.get(
            "controlled_fixture_to_consumer_match", "UNRESOLVED"
        ),
        "structural_ir": ir_doc,
        "semantic_claims": _copy(semantics),
        "semantic_promotions": [],
        "semantic_promotion_count": 0,
        "automatic_semantic_promotion": False,
        "semantic_projection": False,
        "runtime_dispatch": False,
        "blender_emit_ready": False,
        "guardrails": {
            "structural_ir_validated": True,
            "source_sha_matched": True,
            "boundary_inference_from_cadence": False,
            "record_family_inference_from_cadence": False,
            "consumer_name_defines_field_semantics": False,
            "contains_raw_payload": False,
            "contains_literal_qwords": False,
        },
        "next_gate": (
            "direct independently validated field-semantic evidence is required "
            "before geometry/index/material/rig promotion or Blender emit"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Join structural importer intake with Structural IR")
    ap.add_argument("intake_json", type=Path)
    ap.add_argument("structural_ir_json", type=Path)
    ap.add_argument("--json-out", type=Path)
    ns = ap.parse_args()

    intake = json.loads(ns.intake_json.read_text(encoding="utf-8"))
    structural_ir = json.loads(ns.structural_ir_json.read_text(encoding="utf-8"))
    result = build_bridge(intake=intake, structural_ir=structural_ir)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if ns.json_out:
        ns.json_out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
