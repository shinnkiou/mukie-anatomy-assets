from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, Mapping, Sequence

SOURCE_BATCH_ID = "CSMC_F02_SINGLE_BYTE_XOR01_30_20260914"
SOURCE_MANIFEST_SHA256 = "751f05dfff9d5308dfd96421d5bce43e6785de2cb385fb28a8c97c565c6cc891"
SOURCE_FIXTURE = "CSMC_F02_QUAD"
EXPECTED_VARIANT_COUNT = 30

LOAD_RESULTS = {
    "LOAD_ACCEPTED",
    "LOAD_REJECTED",
    "PARTIAL_LOAD",
    "ERROR_DIALOG",
    "CRASH",
    "UNKNOWN",
}
VISIBLE_EFFECTS = {
    "VISIBLE_MODEL_CHANGED",
    "VISIBLE_MODEL_UNCHANGED",
    "NOT_VISIBLE",
    "UNKNOWN",
}
PROCESS_SURVIVAL = {"SURVIVED", "TERMINATED", "UNKNOWN"}
EVIDENCE_STRENGTH = {"DIRECT_PHYSICAL_OBSERVATION", "UNKNOWN"}

FORBIDDEN_OBSERVATION_FIELDS = {
    "semantic",
    "candidate_semantic",
    "semantic_promotion",
    "geometry_claim",
    "index_claim",
    "vertex_claim",
    "weight_claim",
    "material_claim",
    "uv_claim",
    "blender_ready",
    "save_normalization_result",
}

PUBLIC_ROW_FIELDS = (
    "variant_id",
    "source_offset",
    "structural_region",
    "variant_file_sha256",
    "variant_character_blob_sha256",
    "oracle_result",
    "visible_effect",
    "error_class",
    "error_text_sha256",
    "load_time_ms",
    "affected_visible_component",
    "viewport_result_sha256",
    "screenshot_sha256",
    "process_survival",
    "evidence_strength",
    "observer_session_id",
    "observed_at",
)


class OracleIntakeRejected(ValueError):
    pass


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_source_manifest(manifest: Mapping[str, Any], manifest_sha256: str) -> Dict[str, Mapping[str, Any]]:
    if manifest_sha256 != SOURCE_MANIFEST_SHA256:
        raise OracleIntakeRejected("source manifest SHA256 mismatch")
    if manifest.get("batch_id") != SOURCE_BATCH_ID:
        raise OracleIntakeRejected("wrong mutation batch")
    if manifest.get("base_fixture") != SOURCE_FIXTURE:
        raise OracleIntakeRejected("wrong base fixture")
    if manifest.get("variant_count") != EXPECTED_VARIANT_COUNT:
        raise OracleIntakeRejected("source manifest must contain exactly 30 variants")
    if manifest.get("mutation_rule") != "exactly one character-BLOB byte XOR 0x01 per variant":
        raise OracleIntakeRejected("unexpected mutation rule")
    if manifest.get("raw_bytes_embedded") is not False:
        raise OracleIntakeRejected("public source manifest must not embed raw bytes")
    if manifest.get("semantic_promotion") is not False:
        raise OracleIntakeRejected("source manifest must not promote semantics")
    if manifest.get("runtime_dispatch") is not False:
        raise OracleIntakeRejected("source manifest runtime_dispatch must be false")

    variants = manifest.get("variants")
    if not isinstance(variants, list) or len(variants) != EXPECTED_VARIANT_COUNT:
        raise OracleIntakeRejected("variants list must contain exactly 30 entries")

    by_id: Dict[str, Mapping[str, Any]] = {}
    for row in variants:
        if not isinstance(row, Mapping):
            raise OracleIntakeRejected("variant rows must be objects")
        variant_id = row.get("variant_id")
        if not isinstance(variant_id, str) or variant_id in by_id:
            raise OracleIntakeRejected("variant ids must be unique strings")
        expected_num = len(by_id) + 1
        if variant_id != f"M{expected_num:02d}":
            raise OracleIntakeRejected("variant ids must be M01..M30 in source order")
        if row.get("character_blob_diff_byte_count") != 1:
            raise OracleIntakeRejected("each source variant must differ at exactly one BLOB byte")
        if row.get("xor_mask_hex") != "01":
            raise OracleIntakeRejected("each source variant must use XOR 0x01")
        if row.get("sqlite_readback_ok") is not True or row.get("frame_rule_still_holds") is not True:
            raise OracleIntakeRejected("source variant integrity gate failed")
        if row.get("modeler_load_result") != "PENDING_MANUAL_ORACLE":
            raise OracleIntakeRejected("source manifest must remain pre-oracle")
        if not isinstance(row.get("payload_relative_offset"), int):
            raise OracleIntakeRejected("payload_relative_offset missing")
        if not row.get("region") or not row.get("file_sha256") or not row.get("character_blob_sha256"):
            raise OracleIntakeRejected("source variant provenance incomplete")
        by_id[variant_id] = row
    return by_id


def _validate_hash_or_none(name: str, value: Any) -> None:
    if value in (None, ""):
        return
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise OracleIntakeRejected(f"{name} must be lowercase SHA256 or null")


def _validate_observation_row(row: Mapping[str, Any], source: Mapping[str, Any]) -> None:
    forbidden = FORBIDDEN_OBSERVATION_FIELDS & set(row)
    if forbidden:
        raise OracleIntakeRejected(f"semantic/save fields forbidden in oracle observation: {sorted(forbidden)}")

    required = {
        "variant_id",
        "source_offset",
        "structural_region",
        "variant_file_sha256",
        "variant_character_blob_sha256",
        "oracle_result",
        "visible_effect",
        "error_class",
        "process_survival",
        "evidence_strength",
        "save_action_performed",
        "observer_session_id",
        "observed_at",
    }
    missing = sorted(required - set(row))
    if missing:
        raise OracleIntakeRejected(f"observation missing fields: {missing}")

    if row["source_offset"] != source["payload_relative_offset"]:
        raise OracleIntakeRejected("source_offset does not match preregistered manifest")
    if row["structural_region"] != source["region"]:
        raise OracleIntakeRejected("structural_region does not match preregistered manifest")
    if row["variant_file_sha256"] != source["file_sha256"]:
        raise OracleIntakeRejected("variant file hash mismatch")
    if row["variant_character_blob_sha256"] != source["character_blob_sha256"]:
        raise OracleIntakeRejected("variant BLOB hash mismatch")
    if row["oracle_result"] not in LOAD_RESULTS:
        raise OracleIntakeRejected("invalid oracle_result")
    if row["visible_effect"] not in VISIBLE_EFFECTS:
        raise OracleIntakeRejected("invalid visible_effect")
    if row["process_survival"] not in PROCESS_SURVIVAL:
        raise OracleIntakeRejected("invalid process_survival")
    if row["evidence_strength"] not in EVIDENCE_STRENGTH:
        raise OracleIntakeRejected("invalid evidence_strength")
    if row["save_action_performed"] is not False:
        raise OracleIntakeRejected("Save/Save As/Ctrl+S is forbidden in this oracle")
    if not isinstance(row["observer_session_id"], str) or not row["observer_session_id"].strip():
        raise OracleIntakeRejected("observer_session_id required")
    if not isinstance(row["observed_at"], str) or not row["observed_at"].strip():
        raise OracleIntakeRejected("observed_at required")

    if row["oracle_result"] == "CRASH" and row["process_survival"] == "SURVIVED":
        raise OracleIntakeRejected("CRASH cannot claim process survived")
    if row["oracle_result"] == "LOAD_REJECTED" and row["visible_effect"] in {
        "VISIBLE_MODEL_CHANGED",
        "VISIBLE_MODEL_UNCHANGED",
    }:
        raise OracleIntakeRejected("rejected load cannot claim visible-model comparison")

    for name in ("error_text_sha256", "viewport_result_sha256", "screenshot_sha256"):
        _validate_hash_or_none(name, row.get(name))
    if row.get("load_time_ms") is not None:
        if not isinstance(row["load_time_ms"], (int, float)) or row["load_time_ms"] < 0:
            raise OracleIntakeRejected("load_time_ms must be nonnegative or null")


def validate_oracle_observation(
    source_manifest: Mapping[str, Any],
    source_manifest_sha256: str,
    observation: Mapping[str, Any],
    *,
    require_complete: bool = True,
) -> Dict[str, Any]:
    source_by_id = validate_source_manifest(source_manifest, source_manifest_sha256)

    if observation.get("schema_version") != "csmc_f02_mutation_oracle_30_v1":
        raise OracleIntakeRejected("wrong observation schema")
    if observation.get("source_batch_id") != SOURCE_BATCH_ID:
        raise OracleIntakeRejected("observation references wrong batch")
    if observation.get("source_manifest_sha256") != SOURCE_MANIFEST_SHA256:
        raise OracleIntakeRejected("observation source manifest hash mismatch")
    if observation.get("save_actions_performed") not in (False, 0):
        raise OracleIntakeRejected("oracle session must have zero save actions")
    if observation.get("semantic_promotion") is not False:
        raise OracleIntakeRejected("semantic_promotion must remain false")
    if observation.get("blender_emit") is not False:
        raise OracleIntakeRejected("blender_emit must remain false")
    if observation.get("runtime_mutation") is not False:
        raise OracleIntakeRejected("runtime_mutation must remain false")

    rows = observation.get("observations")
    if not isinstance(rows, list):
        raise OracleIntakeRejected("observations must be a list")
    if len(rows) > EXPECTED_VARIANT_COUNT:
        raise OracleIntakeRejected("more than 30 observations supplied")
    if require_complete and len(rows) != EXPECTED_VARIANT_COUNT:
        raise OracleIntakeRejected("complete oracle requires exactly 30 observations")

    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise OracleIntakeRejected("observation rows must be objects")
        variant_id = row.get("variant_id")
        if variant_id not in source_by_id:
            raise OracleIntakeRejected("unknown variant id")
        if variant_id in seen:
            raise OracleIntakeRejected("duplicate variant observation")
        seen.add(variant_id)
        _validate_observation_row(row, source_by_id[variant_id])

    if require_complete and seen != set(source_by_id):
        raise OracleIntakeRejected("complete oracle must cover M01..M30 exactly once")

    unresolved = sum(1 for row in rows if row["oracle_result"] == "UNKNOWN")
    direct = sum(1 for row in rows if row["evidence_strength"] == "DIRECT_PHYSICAL_OBSERVATION")
    return {
        "accepted": True,
        "complete": len(rows) == EXPECTED_VARIANT_COUNT and seen == set(source_by_id),
        "observed_count": len(rows),
        "direct_observation_count": direct,
        "unknown_count": unresolved,
        "semantic_promotion": False,
        "blender_emit": False,
        "classification": "PHYSICAL_ORACLE_COMPLETE" if len(rows) == EXPECTED_VARIANT_COUNT else "PHYSICAL_ORACLE_PARTIAL_CHECKPOINT",
    }


def public_safe_projection(observation: Mapping[str, Any]) -> Dict[str, Any]:
    rows = []
    for row in observation.get("observations", []):
        public_row = {key: row.get(key) for key in PUBLIC_ROW_FIELDS if key in row}
        public_row["xor01_verified_from_source_manifest"] = True
        rows.append(public_row)
    return {
        "schema_version": "csmc_f02_mutation_oracle_30_public_v1",
        "source_batch_id": observation.get("source_batch_id"),
        "source_manifest_sha256": observation.get("source_manifest_sha256"),
        "observations": rows,
        "semantic_promotion": False,
        "blender_emit": False,
        "diagnostic_only": True,
        "not_semantic_proof": True,
    }
