#!/usr/bin/env python3
"""Public-safe contract for the read-only F02 30-mutation MODELER oracle.

This module records/validates human or separately acquired observations. It does
not run MODELER, open files, save files, mutate files, hook processes, or promote
semantics.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "csmc_f02_mutation_oracle_v1"
EXPECTED_VARIANTS = 30

LOAD_RESULTS = {
    "PENDING_MANUAL_ORACLE",
    "LOAD_ACCEPTED",
    "LOAD_REJECTED",
    "PARTIAL_LOAD",
    "ERROR_DIALOG",
    "CRASH",
    "UNKNOWN",
}
VISUAL_RESULTS = {
    "PENDING_MANUAL_ORACLE",
    "VISIBLE_MODEL_CHANGED",
    "VISIBLE_MODEL_UNCHANGED",
    "NOT_OBSERVED",
    "UNKNOWN",
}
PROCESS_SURVIVAL = {"ALIVE", "EXITED", "UNKNOWN", "NOT_OBSERVED"}
EVIDENCE_STRENGTH = {"PENDING", "WEAK", "MODERATE", "STRONG"}
REGIONS = {
    "PREFIX_INTERIOR",
    "INVARIANT_BOUNDARY",
    "INVARIANT_INTERIOR",
    "ALIGNMENT_EXTENSION",
    "FRAMING_REMAINDER",
}
SAVE_POLICY_VALUE = "NOT_RUN_POLICY"


class OracleContractError(ValueError):
    pass


def _hex_byte(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 2:
        raise OracleContractError(f"{name} must be a 2-digit hex byte")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleContractError(f"{name} must be a 2-digit hex byte") from exc
    return value.lower()


def normalize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "variant_id",
        "filename",
        "source_offset",
        "structural_region",
        "byte_before",
        "byte_after",
        "oracle_result",
        "visible_effect",
        "error_class",
        "evidence_strength",
    }
    missing = required - set(row)
    if missing:
        raise OracleContractError(f"missing keys: {sorted(missing)}")

    variant_id = str(row["variant_id"])
    if not variant_id.startswith("M"):
        raise OracleContractError("variant_id must start with M")
    filename = str(row["filename"])
    if not filename.endswith(".csmc"):
        raise OracleContractError("filename must end with .csmc")
    offset = int(row["source_offset"])
    if offset < 0:
        raise OracleContractError("source_offset must be >=0")
    region = str(row["structural_region"])
    if region not in REGIONS:
        raise OracleContractError(f"unknown structural_region: {region}")
    before = _hex_byte(row["byte_before"], "byte_before")
    after = _hex_byte(row["byte_after"], "byte_after")
    if before == after:
        raise OracleContractError("mutation must change exactly one byte value")

    oracle_result = str(row["oracle_result"])
    if oracle_result not in LOAD_RESULTS:
        raise OracleContractError(f"invalid oracle_result: {oracle_result}")
    visible_effect = str(row["visible_effect"])
    if visible_effect not in VISUAL_RESULTS:
        raise OracleContractError(f"invalid visible_effect: {visible_effect}")
    process_survival = str(row.get("process_survival", "NOT_OBSERVED"))
    if process_survival not in PROCESS_SURVIVAL:
        raise OracleContractError(f"invalid process_survival: {process_survival}")
    strength = str(row["evidence_strength"])
    if strength not in EVIDENCE_STRENGTH:
        raise OracleContractError(f"invalid evidence_strength: {strength}")

    # BREAKTHROUGH policy explicitly forbids Save / Save As / Ctrl+S.
    save_result = str(row.get("save_normalization_result", SAVE_POLICY_VALUE))
    if save_result != SAVE_POLICY_VALUE:
        raise OracleContractError("save_normalization_result must remain NOT_RUN_POLICY")
    if bool(row.get("serialization_triggered", False)):
        raise OracleContractError("serialization_triggered must remain false")

    pending = oracle_result == "PENDING_MANUAL_ORACLE"
    if pending and strength != "PENDING":
        raise OracleContractError("pending observations require evidence_strength=PENDING")

    return {
        "variant_id": variant_id,
        "filename": filename,
        "source_offset": offset,
        "structural_region": region,
        "byte_before": before,
        "byte_after": after,
        "oracle_result": oracle_result,
        "visible_effect": visible_effect,
        "error_class": str(row["error_class"]),
        "error_text": str(row.get("error_text", "")),
        "load_timing_ms": row.get("load_timing_ms"),
        "affected_visible_component": str(row.get("affected_visible_component", "")),
        "viewport_result_sha256": row.get("viewport_result_sha256"),
        "process_survival": process_survival,
        "evidence_strength": strength,
        "save_normalization_result": SAVE_POLICY_VALUE,
        "serialization_triggered": False,
    }


def build_oracle_report(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_batch_id: str = "CSMC_F02_SINGLE_BYTE_XOR01_30_20260914",
    require_exact_30: bool = True,
) -> dict[str, Any]:
    normalized = [normalize_row(row) for row in rows]
    ids = [row["variant_id"] for row in normalized]
    if len(ids) != len(set(ids)):
        raise OracleContractError("duplicate variant_id")
    if require_exact_30 and len(normalized) != EXPECTED_VARIANTS:
        raise OracleContractError(f"expected exactly {EXPECTED_VARIANTS} variants")

    normalized.sort(key=lambda row: row["variant_id"])
    pending = sum(row["oracle_result"] == "PENDING_MANUAL_ORACLE" for row in normalized)
    by_region: dict[str, Counter[str]] = defaultdict(Counter)
    for row in normalized:
        by_region[row["structural_region"]][row["oracle_result"]] += 1

    canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": SCHEMA_VERSION,
        "source_batch_id": source_batch_id,
        "observation_count": len(normalized),
        "pending_count": pending,
        "oracle_complete": len(normalized) == EXPECTED_VARIANTS and pending == 0,
        "mode": "READ_ONLY_LOAD_OBSERVATION",
        "save_allowed": False,
        "serialization_trigger_allowed": False,
        "semantic_promotion": False,
        "blender_emit": False,
        "result_counts": dict(Counter(row["oracle_result"] for row in normalized)),
        "region_result_counts": {key: dict(value) for key, value in sorted(by_region.items())},
        "rows_sha256": sha256(canonical).hexdigest(),
        "rows": normalized,
    }
