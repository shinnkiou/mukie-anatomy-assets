from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from typing import Any, Dict, Mapping

SOURCE_BATCH_ID = "CSMC_F02_SINGLE_BYTE_XOR01_30_20260914"
SOURCE_MANIFEST_SHA256 = "751f05dfff9d5308dfd96421d5bce43e6785de2cb385fb28a8c97c565c6cc891"
PROJECTION_SCHEMA = "csmc_f02_mutation_oracle_30_public_v1"
RECEIPT_SCHEMA = "csmc_f02_mutation_oracle_intake_receipt_v2"
DIRECT = "DIRECT_PHYSICAL_OBSERVATION"
LOAD_RESULTS = {"LOAD_ACCEPTED", "LOAD_REJECTED", "PARTIAL_LOAD", "ERROR_DIALOG", "CRASH"}
VISIBLE_EFFECTS = {"VISIBLE_MODEL_CHANGED", "VISIBLE_MODEL_UNCHANGED", "NOT_VISIBLE"}
PROCESS_SURVIVAL = {"SURVIVED", "TERMINATED"}

EXPECTED = {
    **{f"M{i:02d}": (off, "PREFIX_INTERIOR") for i, off in enumerate((8, 64, 128, 256, 512, 1024, 1536, 2048, 2560, 3072), 1)},
    **{f"M{i:02d}": (off, "INVARIANT_BOUNDARY") for i, off in zip(range(11, 18), (3200, 3208, 3215, 3216, 3217, 3224, 3232))},
    **{f"M{i:02d}": (off, "INVARIANT_INTERIOR") for i, off in zip(range(18, 22), (3728, 7312, 11408, 15216))},
    "M22": (17687, "ALIGNMENT_EXTENSION"),
    **{f"M{i:02d}": (off, "FRAMING_REMAINDER") for i, off in zip(range(23, 31), range(17688, 17696))},
}
REGIONS = sorted({region for _, region in EXPECTED.values()})
SENTINEL9 = ("M01", "M10", "M13", "M14", "M15", "M18", "M22", "M23", "M30")
FORBIDDEN_ROW_FIELDS = {
    "semantic", "candidate_semantic", "semantic_promotion", "geometry_claim", "index_claim",
    "vertex_claim", "weight_claim", "material_claim", "uv_claim", "blender_ready",
    "save_normalization_result", "raw_bytes", "raw_payload", "private_payload", "base64_payload",
}


class StructuralContrastRejected(ValueError):
    pass


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _hash64(name: str, value: Any) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise StructuralContrastRejected(f"{name} must be lowercase SHA256")


def _offset_aware_iso(value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise StructuralContrastRejected("observed_at required")
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise StructuralContrastRejected("observed_at must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise StructuralContrastRejected("observed_at must be offset-aware")


def _validate_receipt(projection: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema_version") != RECEIPT_SCHEMA:
        raise StructuralContrastRejected("wrong receipt schema")
    if receipt.get("source_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256:
        raise StructuralContrastRejected("receipt source manifest hash mismatch")
    if receipt.get("public_projection_canonical_sha256") != canonical_sha256(projection):
        raise StructuralContrastRejected("projection canonical SHA mismatch")
    if receipt.get("semantic_promotion") is not False or receipt.get("blender_emit") is not False:
        raise StructuralContrastRejected("receipt semantic/blender guard failed")
    if receipt.get("diagnostic_only") is not True:
        raise StructuralContrastRejected("receipt must remain diagnostic_only")
    validation = receipt.get("validation")
    completion = receipt.get("physical_completion_gate")
    if not isinstance(validation, Mapping) or validation.get("accepted") is not True:
        raise StructuralContrastRejected("upstream validation receipt not accepted")
    if not isinstance(completion, Mapping):
        raise StructuralContrastRejected("missing physical completion gate")


def _response_class(row: Mapping[str, Any]) -> str:
    load = row["oracle_result"]
    if load == "CRASH" or row["process_survival"] == "TERMINATED":
        return "PROCESS_TERMINATION"
    if load in {"ERROR_DIALOG", "LOAD_REJECTED", "PARTIAL_LOAD"}:
        return load
    return {
        "VISIBLE_MODEL_CHANGED": "LOAD_ACCEPTED_VISIBLE_CHANGED",
        "VISIBLE_MODEL_UNCHANGED": "LOAD_ACCEPTED_VISIBLE_UNCHANGED",
        "NOT_VISIBLE": "LOAD_ACCEPTED_NOT_VISIBLE",
    }[row["visible_effect"]]


def _disruptive(row: Mapping[str, Any]) -> bool:
    return row["oracle_result"] in {"LOAD_REJECTED", "PARTIAL_LOAD", "ERROR_DIALOG", "CRASH"} or row["process_survival"] == "TERMINATED"


def analyze_public_projection(projection: Mapping[str, Any], receipt: Mapping[str, Any], *, require_complete: bool = False) -> Dict[str, Any]:
    _validate_receipt(projection, receipt)
    if projection.get("schema_version") != PROJECTION_SCHEMA:
        raise StructuralContrastRejected("wrong projection schema")
    if projection.get("source_batch_id") != SOURCE_BATCH_ID or projection.get("source_manifest_sha256") != SOURCE_MANIFEST_SHA256:
        raise StructuralContrastRejected("wrong batch or manifest")
    if projection.get("semantic_promotion") is not False or projection.get("blender_emit") is not False:
        raise StructuralContrastRejected("projection semantic/blender guard failed")
    if projection.get("diagnostic_only") is not True or projection.get("not_semantic_proof") is not True:
        raise StructuralContrastRejected("projection must remain diagnostic and non-semantic")

    rows = projection.get("observations")
    if not isinstance(rows, list) or not rows or len(rows) > 30:
        raise StructuralContrastRejected("observation count out of range")

    by_id: Dict[str, Mapping[str, Any]] = {}
    region_classes: Dict[str, Counter[str]] = defaultdict(Counter)
    region_loads: Dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        if not isinstance(row, Mapping):
            raise StructuralContrastRejected("row must be object")
        forbidden = FORBIDDEN_ROW_FIELDS & set(row)
        if forbidden:
            raise StructuralContrastRejected(f"forbidden semantic/raw fields: {sorted(forbidden)}")
        variant = row.get("variant_id")
        if variant not in EXPECTED or variant in by_id:
            raise StructuralContrastRejected("unknown or duplicate variant")
        offset, region = EXPECTED[variant]
        if row.get("source_offset") != offset or row.get("structural_region") != region:
            raise StructuralContrastRejected("variant offset/region mismatch")
        if row.get("xor01_verified_from_source_manifest") is not True:
            raise StructuralContrastRejected("missing XOR01 source binding")
        _hash64("variant_file_sha256", row.get("variant_file_sha256"))
        _hash64("variant_character_blob_sha256", row.get("variant_character_blob_sha256"))
        if row.get("oracle_result") not in LOAD_RESULTS or row.get("visible_effect") not in VISIBLE_EFFECTS or row.get("process_survival") not in PROCESS_SURVIVAL:
            raise StructuralContrastRejected("row must contain resolved physical classifications")
        if row.get("evidence_strength") != DIRECT:
            raise StructuralContrastRejected("only direct physical observations are analyzable")
        if not isinstance(row.get("observer_session_id"), str) or not row["observer_session_id"].strip():
            raise StructuralContrastRejected("observer_session_id required")
        _offset_aware_iso(row.get("observed_at"))
        by_id[variant] = row
        region_classes[region][_response_class(row)] += 1
        region_loads[region][row["oracle_result"]] += 1

    n = len(rows)
    validation = receipt["validation"]
    completion = receipt["physical_completion_gate"]
    if validation.get("observed_count") != n or validation.get("direct_observation_count") != n:
        raise StructuralContrastRejected("validation counts disagree")
    if completion.get("observed_count") != n or completion.get("direct_observation_count") != n or completion.get("unresolved_row_count") != 0:
        raise StructuralContrastRejected("completion counts/unresolved state disagree")

    complete = set(by_id) == set(EXPECTED)
    if require_complete and not complete:
        raise StructuralContrastRejected("complete contrast requires M01..M30")
    if complete and completion.get("physical_complete") is not True:
        raise StructuralContrastRejected("complete projection requires physical_complete")
    if not complete and completion.get("physical_complete") is True:
        raise StructuralContrastRejected("partial projection cannot claim physical_complete")

    flags = []
    if all(v in by_id for v in ("M10", "M13", "M14", "M15", "M18")):
        boundary = [by_id[v] for v in ("M13", "M14", "M15")]
        if by_id["M10"]["oracle_result"] == "LOAD_ACCEPTED" and by_id["M18"]["oracle_result"] == "LOAD_ACCEPTED":
            if sum(_disruptive(r) for r in boundary) >= 2:
                flags.append("BOUNDARY_TRIPLET_LOAD_DISRUPTION_CANDIDATE")
            if by_id["M10"]["visible_effect"] == "VISIBLE_MODEL_UNCHANGED" and by_id["M18"]["visible_effect"] == "VISIBLE_MODEL_UNCHANGED" and any(r["oracle_result"] == "LOAD_ACCEPTED" and r["visible_effect"] == "VISIBLE_MODEL_CHANGED" for r in boundary):
                flags.append("BOUNDARY_TRIPLET_VISIBLE_DIVERGENCE_CANDIDATE")
    if all(v in by_id for v in ("M22", "M23", "M30")):
        if by_id["M22"]["oracle_result"] == "LOAD_ACCEPTED" and (_disruptive(by_id["M23"]) or _disruptive(by_id["M30"])):
            flags.append("FRAMING_EDGE_LOAD_DISRUPTION_CANDIDATE")
        if by_id["M23"]["oracle_result"] != by_id["M30"]["oracle_result"]:
            flags.append("FRAMING_SENTINEL_DISAGREEMENT")
    if all(v in by_id for v in ("M01", "M10")) and by_id["M01"]["oracle_result"] != by_id["M10"]["oracle_result"]:
        flags.append("PREFIX_SENTINEL_DISAGREEMENT")

    region_summary = {}
    for region in REGIONS:
        ids = [v for v, (_, r) in EXPECTED.items() if r == region]
        observed = [v for v in ids if v in by_id]
        region_summary[region] = {
            "expected_count": len(ids), "observed_count": len(observed), "variant_ids": observed,
            "response_classes": dict(sorted(region_classes[region].items())),
            "load_results": dict(sorted(region_loads[region].items())),
        }

    sentinel_observed = [v for v in SENTINEL9 if v in by_id]
    return {
        "schema_version": "csmc_analysis_c_f02_structural_contrast_prereg_v1",
        "classification": "STRUCTURAL_CONTRAST_COMPLETE_DIRECT" if complete else "STRUCTURAL_CONTRAST_PARTIAL_DIRECT",
        "observed_count": n,
        "complete_30": complete,
        "sentinel9_observed_count": len(sentinel_observed),
        "sentinel9_complete": len(sentinel_observed) == len(SENTINEL9),
        "sentinel9_observed": sentinel_observed,
        "region_summary": region_summary,
        "preregistered_structural_flags": flags,
        "interpretation_scope": "STRUCTURAL_LOAD_VISIBILITY_ONLY",
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "numbered_run_auto_authorized": False,
        "diagnostic_only": True,
        "not_semantic_proof": True,
    }
