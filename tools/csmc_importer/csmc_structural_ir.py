#!/usr/bin/env python3
"""Public-safe semantics-free structural IR for CSMC interoperability research.

This module deliberately represents only structural evidence that has been
independently observed. It does not assign geometry/material/rig semantics and
forbids embedding raw payload bytes or literal qword values.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "csmc_structural_ir_v0_1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SIG_RE = re.compile(r"^[01]+$")
BOUNDARY_CLASSES = {
    "local_extinction",
    "mixed_reuse_repack",
    "sparse_delta_excursion",
    "unknown",
}
SEMANTIC_KEYS = (
    "geometry",
    "index_buffer",
    "uv",
    "material",
    "texture",
    "bone_hierarchy",
    "bind_pose",
    "bone_indices",
    "skin_weights",
)
FORBIDDEN_KEYS = {
    "raw_bytes",
    "payload_bytes",
    "payload_base64",
    "qword_value",
    "literal_qword",
    "source_path",
    "private_capture_path",
}


def _walk_keys(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                errors.append(f"{path}.{key}: forbidden raw/private field")
            errors.extend(_walk_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            errors.extend(_walk_keys(child, f"{path}[{i}]"))
    return errors


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_ir(doc: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["$: document must be an object"]

    errors.extend(_walk_keys(doc))

    if doc.get("schema_version") != SCHEMA_VERSION:
        errors.append("$.schema_version: unsupported schema version")

    source = doc.get("source")
    if not isinstance(source, dict):
        errors.append("$.source: object required")
    else:
        for name in ("clip_sha256", "csmc_sha256"):
            value = source.get(name)
            if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                errors.append(f"$.source.{name}: lowercase SHA-256 required")
        if source.get("raw_bytes_embedded") is not False:
            errors.append("$.source.raw_bytes_embedded: must be false")

    axes = doc.get("ir_axes")
    if not isinstance(axes, list) or not all(isinstance(x, str) for x in axes):
        errors.append("$.ir_axes: string list required")
    else:
        required_axes = {"length_blocks", "preserve_signature"}
        if not required_axes.issubset(set(axes)):
            errors.append("$.ir_axes: length_blocks and preserve_signature must remain independent axes")

    boundaries = doc.get("boundaries")
    if not isinstance(boundaries, list):
        errors.append("$.boundaries: list required")
    else:
        seen_ids: set[str] = set()
        for i, row in enumerate(boundaries):
            p = f"$.boundaries[{i}]"
            if not isinstance(row, dict):
                errors.append(f"{p}: object required")
                continue
            ident = row.get("id")
            if not isinstance(ident, str) or not ident:
                errors.append(f"{p}.id: non-empty string required")
            elif ident in seen_ids:
                errors.append(f"{p}.id: duplicate boundary id")
            else:
                seen_ids.add(ident)
            if row.get("class") not in BOUNDARY_CLASSES:
                errors.append(f"{p}.class: unsupported boundary class")
            for key in ("from_delta_blocks", "to_delta_blocks", "net_relative_size_bytes", "barrier_matches_old_delta", "barrier_matches_new_delta"):
                if not _is_int(row.get(key)):
                    errors.append(f"{p}.{key}: integer required")
            if row.get("complete_cross_serialization_extinction") not in (True, False):
                errors.append(f"{p}.complete_cross_serialization_extinction: boolean required")
            if row.get("semantic_owner") != "unresolved":
                errors.append(f"{p}.semantic_owner: must remain 'unresolved'")

    families = doc.get("record_families")
    if not isinstance(families, list):
        errors.append("$.record_families: list required")
    else:
        for i, row in enumerate(families):
            p = f"$.record_families[{i}]"
            if not isinstance(row, dict):
                errors.append(f"{p}: object required")
                continue
            if not _is_int(row.get("length_blocks")) or row.get("length_blocks", 0) <= 0:
                errors.append(f"{p}.length_blocks: positive integer required")
            sig = row.get("preserve_signature")
            if not isinstance(sig, str) or not SIG_RE.fullmatch(sig):
                errors.append(f"{p}.preserve_signature: binary string required")
            if not _is_int(row.get("count")) or row.get("count", 0) <= 0:
                errors.append(f"{p}.count: positive integer required")
            if row.get("semantic_record_type") != "unresolved":
                errors.append(f"{p}.semantic_record_type: must remain 'unresolved'")

    semantics = doc.get("semantic_claims")
    if not isinstance(semantics, dict):
        errors.append("$.semantic_claims: object required")
    else:
        for key in SEMANTIC_KEYS:
            if semantics.get(key) != "unresolved":
                errors.append(f"$.semantic_claims.{key}: must be 'unresolved'")

    guardrails = doc.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append("$.guardrails: object required")
    else:
        for key in ("public_safe", "aggregate_only"):
            if guardrails.get(key) is not True:
                errors.append(f"$.guardrails.{key}: must be true")
        for key in ("contains_raw_payload", "contains_literal_qwords", "blender_import_proven"):
            if guardrails.get(key) is not False:
                errors.append(f"$.guardrails.{key}: must be false")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("json_file", type=Path)
    ns = ap.parse_args()
    doc = json.loads(ns.json_file.read_text(encoding="utf-8"))
    errors = validate_ir(doc)
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        return 2
    print(json.dumps({"status": "PASS", "schema_version": SCHEMA_VERSION}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
