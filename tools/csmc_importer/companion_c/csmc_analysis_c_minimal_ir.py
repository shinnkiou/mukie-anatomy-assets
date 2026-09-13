#!/usr/bin/env python3
"""Build and validate a semantics-free CSMC importer intermediate representation.

Inputs are public-safe aggregate outputs only. The IR intentionally separates
structural facts from semantic claims so later geometry/index/transform/material/
hierarchy evidence can be attached without rewriting structural parsing logic.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

IR_VERSION = "csmc_analysis_c_minimal_ir_v1"
BOUNDARY_CLASSES = {
    "LOCAL_EXTINCTION_CANDIDATE",
    "MIXED_REUSE_REPACK_CANDIDATE",
    "UNRESOLVED_BOUNDARY",
}
SEMANTIC_STATUS = {"UNRESOLVED", "CANDIDATE", "CONFIRMED"}
SEMANTIC_SLOTS = ("geometry", "index", "transform", "material", "hierarchy")
SIG_RE = re.compile(r"^[01]{7}$")


def _semantic_slot() -> dict[str, Any]:
    return {
        "status": "UNRESOLVED",
        "confidence": 0.0,
        "evidence_ids": [],
        "candidate_notes": [],
    }


def build_ir(boundary_report: dict, family_report: dict, control_report: dict | None = None) -> dict:
    boundaries = []
    for boundary_id, b in sorted(boundary_report.get("boundaries", {}).items()):
        boundaries.append(
            {
                "boundary_id": boundary_id,
                "boundary_class": b["class"],
                "net_relative_size_change_bytes": int(b["net_relative_size_change_bytes"]),
                "cross_serialization_survival_distinct": int(b["cross_serialization_survival_distinct"]),
                "old_delta_barrier_match_density": float(b["old_delta_barrier_match_density"]),
                "new_delta_barrier_match_density": float(b["new_delta_barrier_match_density"]),
                "semantic_role": "UNRESOLVED",
            }
        )

    families = []
    for idx, f in enumerate(family_report.get("families", [])):
        families.append(
            {
                "family_id": f"RF_{idx:02d}",
                "length_blocks": int(f["length_blocks"]),
                "preserve_signature": str(f["signature"]),
                "count": int(f["count"]),
                "semantic_role": "UNRESOLVED",
            }
        )

    record_layout = {
        "qword_bytes": 8,
        "observed_record_lengths_blocks": sorted({f["length_blocks"] for f in families}),
        "stable_prefix": {"start_qword": 0, "end_qword_inclusive": 20},
        "control_zone": {"start_qword": 21, "end_qword_inclusive": 27},
        "fixed_rewrite_qwords": [22, 23],
        "fixed_preserve_qwords": [25, 26],
        "conditional_qwords": [21, 24, 27],
        "rewrite_tail_start_qword": 28,
    }
    if control_report:
        record_layout.update(
            {
                "fixed_rewrite_qwords": list(control_report.get("fixed_different_relative_blocks", [22, 23])),
                "fixed_preserve_qwords": list(control_report.get("fixed_equal_relative_blocks", [25, 26])),
                "conditional_qwords": list(control_report.get("conditional_relative_blocks", [21, 24, 27])),
            }
        )

    ir = {
        "schema_version": IR_VERSION,
        "parser_contract": {
            "semantic_free": True,
            "raw_payload_bytes_embedded": False,
            "qword_alignment_bytes": 8,
            "semantic_confirmation_requires_evidence": True,
        },
        "structural_grammar": {
            "boundary_classes_observed": sorted({b["boundary_class"] for b in boundaries}),
            "boundaries": boundaries,
            "record_layout": record_layout,
            "record_families": families,
            "record_family_axes": list(family_report.get("recommended_ir_axes", ["length_blocks", "preserve_signature"])),
        },
        "semantic_slots": {slot: _semantic_slot() for slot in SEMANTIC_SLOTS},
        "evidence_refs": [
            "CSMC_ANALYSIS_C_BOUNDARY_MOTIF_20260913",
            "CSMC_ANALYSIS_C_RECORD_FAMILY_FACTORIZATION_20260913",
        ],
        "guardrails": [
            "Structure is not semantics.",
            "A record family must not be named Mesh/Index/UV/Material/Bone/Weight without independent evidence.",
            "CONFIRMED semantic status requires at least one explicit evidence id.",
        ],
    }
    validate_ir(ir)
    return ir


def validate_ir(ir: dict) -> None:
    if ir.get("schema_version") != IR_VERSION:
        raise ValueError("unexpected schema_version")
    contract = ir.get("parser_contract", {})
    if contract.get("semantic_free") is not True:
        raise ValueError("IR must remain semantic_free")
    if contract.get("raw_payload_bytes_embedded") is not False:
        raise ValueError("raw payload bytes are forbidden in the aggregate IR")

    grammar = ir.get("structural_grammar", {})
    for b in grammar.get("boundaries", []):
        if b.get("boundary_class") not in BOUNDARY_CLASSES:
            raise ValueError(f"unknown boundary class: {b.get('boundary_class')}")
        if b.get("semantic_role") != "UNRESOLVED":
            raise ValueError("boundary semantic_role must remain UNRESOLVED in v1")

    for f in grammar.get("record_families", []):
        if not isinstance(f.get("length_blocks"), int) or f["length_blocks"] <= 0:
            raise ValueError("invalid record length")
        if not SIG_RE.match(str(f.get("preserve_signature", ""))):
            raise ValueError("preserve_signature must be a 7-bit 0/1 string")
        if not isinstance(f.get("count"), int) or f["count"] <= 0:
            raise ValueError("invalid family count")
        if f.get("semantic_role") != "UNRESOLVED":
            raise ValueError("record family semantic_role must remain UNRESOLVED in v1")

    slots = ir.get("semantic_slots", {})
    if set(slots) != set(SEMANTIC_SLOTS):
        raise ValueError("semantic_slots must contain exactly geometry/index/transform/material/hierarchy")
    for name, slot in slots.items():
        status = slot.get("status")
        if status not in SEMANTIC_STATUS:
            raise ValueError(f"invalid semantic status for {name}")
        confidence = float(slot.get("confidence", -1))
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"invalid confidence for {name}")
        evidence = slot.get("evidence_ids")
        if not isinstance(evidence, list):
            raise ValueError(f"evidence_ids must be a list for {name}")
        if status == "CONFIRMED" and not evidence:
            raise ValueError(f"CONFIRMED semantic slot {name} lacks evidence")
        if status == "UNRESOLVED" and confidence != 0.0:
            raise ValueError(f"UNRESOLVED semantic slot {name} must have confidence 0.0 in v1")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundary", type=Path, required=True)
    ap.add_argument("--families", type=Path, required=True)
    ap.add_argument("--control", type=Path)
    ap.add_argument("--out", type=Path)
    ns = ap.parse_args()
    control = json.loads(ns.control.read_text(encoding="utf-8")) if ns.control else None
    ir = build_ir(
        json.loads(ns.boundary.read_text(encoding="utf-8")),
        json.loads(ns.families.read_text(encoding="utf-8")),
        control,
    )
    text = json.dumps(ir, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if ns.out:
        ns.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
