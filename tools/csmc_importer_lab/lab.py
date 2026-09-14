#!/usr/bin/env python3
"""Public-safe synthetic Factory core for CSMC Importer Hypothesis Lab v0.1.

This module cannot open target payload files.  It implements only the M1
Factory contracts: bounded manifests, canonical dedupe, negative controls,
deterministic results, failure isolation, frozen execution context, artifact
integrity, and hard-disabled promotion/render output.
"""
from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

MANIFEST_SCHEMA_VERSION = "csmc_hypothesis_manifest_v0_1"
LAB_QUEUE = "csmc_importer_lab_jobs_v0_1"
LAB_CAPABILITY = "csmc_hypothesis_runner_v1"
PRODUCTION_QUEUE_DENYLIST = {"ai3d_worker_jobs", "never_tear_ai3d_engine"}

ALLOWED_FIELDS = {
    "schema_version", "experiment_id", "generation_id", "candidate_id",
    "parent_candidate_ids", "mutation_descriptor", "candidate_family",
    "region_id", "anchor_id", "relative_offset", "count_source",
    "count_type", "count_endianness", "element_type", "element_endianness",
    "components", "stride_class", "alignment", "grouping", "relationship",
    "phase_scope", "candidate_semantic_hint",
}
FORBIDDEN_KEYS = {
    "command", "shell", "python_code", "script", "executable",
    "filesystem_path", "network_url", "package_install", "environment_variable",
    "credential", "fixture_override", "evaluator_override", "score_override",
    "timeout_override", "retry_override", "worker_capability_override",
    "holdout_override", "semantic_promotion", "blender_emit",
}
FAMILIES = {
    "LOCAL_STRUCTURAL_BOUNDARY", "COUNTED_NUMERIC_CODEC",
    "GEOMETRY_INDEX_RELATIONSHIP", "FALSIFICATION_CONTROLS", "EXPLORATION",
}
REGIONS = {"VARIABLE_PREFIX", "LOCAL_SUBBLOCK_A", "LOCAL_SUBBLOCK_B", "CONTROL_ZONE", "PRESERVED_ISLAND", "INVARIANT_CORE_DECOY"}
ANCHORS = {"IR_START", "VARIABLE_PREFIX_START", "CONTROL_ZONE_START", "PRESERVED_ISLAND_START", "LOCAL_BOUNDARY_A", "LOCAL_BOUNDARY_B"}
COUNT_SOURCES = {"NONE", "LOCAL_U16", "LOCAL_U32", "PARENT_COUNT", "LOCAL_LENGTH_DERIVED"}
COUNT_TYPES = {"NONE", "U16", "U32"}
ENDIANS = {"NONE", "LE", "BE"}
ELEMENT_TYPES = {"NONE", "U16", "U32", "F32", "F64"}
STRIDES = {"PACKED", "PAD8", "PAD16", "PAD32", "LOCAL_VARLEN"}
GROUPINGS = {"SCALAR", "VECTOR", "COUNTED_ARRAY", "LOCAL_RECORD", "RELATION_PAIR"}
PHASES = {"TRAIN", "ADVERSARIAL", "VALIDATION", "SEALED_SIDE_DOMAIN", "AUDIT_ONLY"}
RELATIONSHIPS = {
    "NONE", "COUNT_TO_EXTENT", "COUNT_TO_INDEX_RANGE", "LENGTH_TO_BLOCK",
    "CROSS_REGION_CARDINALITY", "WRONG_ENDIAN_SENTINEL", "WRONG_COUNT_SENTINEL",
    "WRONG_PHASE_SENTINEL", "WRONG_RELATIONSHIP_SENTINEL",
    "LABEL_ALIAS_SENTINEL", "NOISE_SENTINEL",
}
NEGATIVE_RELATIONSHIPS = {
    "WRONG_ENDIAN_SENTINEL", "WRONG_COUNT_SENTINEL", "WRONG_PHASE_SENTINEL",
    "WRONG_RELATIONSHIP_SENTINEL", "LABEL_ALIAS_SENTINEL", "NOISE_SENTINEL",
}
GENOTYPE_FIELDS = (
    "region_id", "anchor_id", "relative_offset", "count_source", "count_type",
    "count_endianness", "element_type", "element_endianness", "components",
    "stride_class", "alignment", "grouping", "relationship", "phase_scope",
)

class LabError(RuntimeError):
    pass

class FrozenContextDrift(LabError):
    pass

class ArtifactIntegrityError(LabError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _walk_forbidden(value: Any, path: str = "$") -> list[str]:
    out: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                out.append(f"{path}.{key}: forbidden field")
            out.extend(_walk_forbidden(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            out.extend(_walk_forbidden(child, f"{path}[{i}]"))
    return out


def validate_manifest(m: Any) -> list[str]:
    if not isinstance(m, Mapping):
        return ["$: object required"]
    errors = _walk_forbidden(m)
    unknown = set(m) - ALLOWED_FIELDS
    missing = ALLOWED_FIELDS - set(m)
    if unknown:
        errors.append("unknown fields: " + ",".join(sorted(unknown)))
    if missing:
        errors.append("missing fields: " + ",".join(sorted(missing)))
        return errors
    checks = [
        (m["schema_version"] == MANIFEST_SCHEMA_VERSION, "schema_version unsupported"),
        (m["candidate_family"] in FAMILIES, "candidate_family invalid"),
        (m["region_id"] in REGIONS, "region_id invalid"),
        (m["anchor_id"] in ANCHORS, "anchor_id invalid"),
        (isinstance(m["relative_offset"], int) and not isinstance(m["relative_offset"], bool) and -8 <= m["relative_offset"] <= 8, "relative_offset must be bounded -8..8"),
        (m["count_source"] in COUNT_SOURCES, "count_source invalid"),
        (m["count_type"] in COUNT_TYPES, "count_type invalid"),
        (m["count_endianness"] in ENDIANS, "count_endianness invalid"),
        (m["element_type"] in ELEMENT_TYPES, "element_type invalid"),
        (m["element_endianness"] in ENDIANS, "element_endianness invalid"),
        (m["components"] in {1, 2, 3, 4}, "components invalid"),
        (m["stride_class"] in STRIDES, "stride_class invalid"),
        (m["alignment"] in {1, 2, 4, 8, 16}, "alignment invalid"),
        (m["grouping"] in GROUPINGS, "grouping invalid"),
        (m["relationship"] in RELATIONSHIPS, "relationship invalid"),
        (m["phase_scope"] in PHASES, "phase_scope invalid"),
        (isinstance(m["candidate_semantic_hint"], str) and len(m["candidate_semantic_hint"]) <= 64, "candidate_semantic_hint invalid"),
    ]
    errors.extend(msg for ok, msg in checks if not ok)
    md = m.get("mutation_descriptor")
    if not isinstance(md, Mapping) or set(md) != {"kind", "axes"} or not isinstance(md.get("axes"), list) or len(md["axes"]) > 2:
        errors.append("mutation_descriptor invalid")
    if m["phase_scope"] in {"SEALED_SIDE_DOMAIN", "AUDIT_ONLY"}:
        errors.append("holdout/audit phase access forbidden to candidate")
    return errors


def genotype_hash(m: Mapping[str, Any]) -> str:
    return sha256_json({key: m[key] for key in GENOTYPE_FIELDS})


@dataclass(frozen=True)
class FrozenEnvelope:
    engine_sha256: str = "a" * 64
    runner_sha256: str = "b" * 64
    fixture_set_sha256: str = "c" * 64
    negative_control_set_sha256: str = "d" * 64
    constraint_pack_sha256: str = "e" * 64
    evaluator_sha256: str = "f" * 64
    scoring_profile_sha256: str = "1" * 64
    environment_digest: str = "2" * 64
    dependency_lock_sha256: str = "3" * 64
    seed: int = 20260914
    worker_capability: str = LAB_CAPABILITY
    artifact_namespace: str = "csmc_importer_lab/v0_1"

    @property
    def digest(self) -> str:
        return sha256_json(asdict(self))


@dataclass
class CandidateResult:
    candidate_id: str
    status: str
    genotype_sha256: str | None
    metric_vector: dict[str, int]
    reject_reasons: list[str]
    semantic_promotion: bool = False
    blender_emit: bool = False
    diagnostic_only: bool = True
    raw_private_bytes_present: bool = False
    queue: str = LAB_QUEUE
    worker_capability: str = LAB_CAPABILITY
    public_safe_result_fingerprint: str | None = None

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


def _result(candidate_id: str, status: str, gh: str | None, *, reasons: list[str] | None = None, metrics: dict[str, int] | None = None) -> CandidateResult:
    row = CandidateResult(candidate_id=candidate_id, status=status, genotype_sha256=gh, metric_vector=metrics or {}, reject_reasons=reasons or [])
    row.public_safe_result_fingerprint = sha256_json({
        "candidate_id": candidate_id, "status": status, "genotype_sha256": gh,
        "metric_vector": row.metric_vector, "semantic_promotion": False,
        "blender_emit": False, "queue": LAB_QUEUE,
    })
    return row


def _synthetic_evaluate(m: Mapping[str, Any], behavior: str = "NORMAL") -> CandidateResult:
    gh = genotype_hash(m)
    if behavior == "HANG":
        time.sleep(0.05)
        return _result(m["candidate_id"], "TIMEOUT", gh, reasons=["synthetic candidate exceeded fixed timeout"])
    if behavior == "CRASH":
        raise RuntimeError("synthetic isolated crash")
    if m["candidate_family"] == "FALSIFICATION_CONTROLS" or m["relationship"] in NEGATIVE_RELATIONSHIPS:
        return _result(m["candidate_id"], "NEGATIVE_CONTROL_REJECT", gh, reasons=["negative-control sentinel rejected"])
    nibble = int(gh[:8], 16)
    metrics = {
        "controlled_differential_consistency": nibble % 7,
        "cross_fixture_structural_consistency": (nibble >> 3) % 7,
        "negative_control_specificity": 6,
        "validation_generalization": (nibble >> 6) % 7,
        "consumer_compatibility": (nibble >> 9) % 7,
        "parsimony": 6 - (abs(int(m["relative_offset"])) % 6),
    }
    return _result(m["candidate_id"], "EXECUTION_PASS", gh, metrics=metrics)


class GenerationRunner:
    def __init__(self, envelope: FrozenEnvelope, physical_concurrency: int = 1):
        if physical_concurrency not in {1, 2, 5}:
            raise ValueError("physical_concurrency must be 1, 2, or 5")
        self.envelope = envelope
        self.frozen_digest = envelope.digest
        self.physical_concurrency = physical_concurrency
        self.production_queue_jobs = 0
        self.production_artifact_mutations = 0

    def assert_frozen(self, envelope: FrozenEnvelope) -> None:
        if envelope.digest != self.frozen_digest:
            raise FrozenContextDrift("frozen execution context changed")

    def run(self, manifests: list[dict[str, Any]], *, test_behaviors: Mapping[str, str] | None = None) -> list[CandidateResult]:
        self.assert_frozen(self.envelope)
        test_behaviors = dict(test_behaviors or {})
        seen: set[str] = set()
        results: list[CandidateResult] = []
        runnable: list[dict[str, Any]] = []
        for m in manifests:
            errors = validate_manifest(m)
            if errors:
                results.append(_result(str(m.get("candidate_id", "UNKNOWN")), "INVALID_MANIFEST", None, reasons=errors))
                continue
            gh = genotype_hash(m)
            if gh in seen:
                results.append(_result(m["candidate_id"], "CONSTRAINT_REJECT", gh, reasons=["canonical genotype duplicate"]))
                continue
            seen.add(gh)
            runnable.append(m)
        with ThreadPoolExecutor(max_workers=self.physical_concurrency) as pool:
            future_map = {pool.submit(_synthetic_evaluate, m, test_behaviors.get(m["candidate_id"], "NORMAL")): m for m in runnable}
            for future in as_completed(future_map):
                m = future_map[future]
                try:
                    results.append(future.result())
                except Exception as exc:
                    results.append(_result(m["candidate_id"], "CRASH", genotype_hash(m), reasons=[f"isolated candidate crash: {type(exc).__name__}"]))
        results.sort(key=lambda row: row.candidate_id)
        return results


def write_artifact(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    expected = hashlib.sha256(raw).hexdigest()
    path.write_bytes(raw)
    verify_artifact(path, expected)
    return expected


def verify_artifact(path: Path, expected_sha256: str) -> None:
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ArtifactIntegrityError("artifact provider readback SHA mismatch")


def generate_synthetic_candidates(count: int = 50, *, experiment_id: str = "M1_SYNTHETIC_20260914") -> list[dict[str, Any]]:
    if not 0 <= count <= 50:
        raise ValueError("count must be 0..50")
    allocation = (["LOCAL_STRUCTURAL_BOUNDARY"] * 20 + ["COUNTED_NUMERIC_CODEC"] * 10 + ["GEOMETRY_INDEX_RELATIONSHIP"] * 5 + ["FALSIFICATION_CONTROLS"] * 5 + ["EXPLORATION"] * 10)
    normal_rel = ["LENGTH_TO_BLOCK", "COUNT_TO_EXTENT", "COUNT_TO_INDEX_RANGE", "CROSS_REGION_CARDINALITY", "NONE"]
    negative_rel = ["WRONG_ENDIAN_SENTINEL", "WRONG_COUNT_SENTINEL", "WRONG_PHASE_SENTINEL", "WRONG_RELATIONSHIP_SENTINEL", "NOISE_SENTINEL"]
    regions = ["VARIABLE_PREFIX", "LOCAL_SUBBLOCK_A", "LOCAL_SUBBLOCK_B", "CONTROL_ZONE", "PRESERVED_ISLAND"]
    anchors = ["VARIABLE_PREFIX_START", "LOCAL_BOUNDARY_A", "LOCAL_BOUNDARY_B", "CONTROL_ZONE_START", "PRESERVED_ISLAND_START"]
    rows: list[dict[str, Any]] = []
    for i in range(count):
        family = allocation[i]
        negative = family == "FALSIFICATION_CONTROLS"
        count_type = ["NONE", "U16", "U32"][i % 3]
        row = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "experiment_id": experiment_id,
            "generation_id": "GEN0",
            "candidate_id": f"HYP_{i:04d}",
            "parent_candidate_ids": [],
            "mutation_descriptor": {"kind": "FALSIFICATION_SENTINEL" if negative else "SEED", "axes": []},
            "candidate_family": family,
            "region_id": regions[i % 5],
            "anchor_id": anchors[i % 5],
            "relative_offset": (i % 17) - 8,
            "count_source": "NONE" if count_type == "NONE" else ("LOCAL_U16" if count_type == "U16" else "LOCAL_U32"),
            "count_type": count_type,
            "count_endianness": "NONE" if count_type == "NONE" else ["LE", "BE"][i % 2],
            "element_type": ["F32", "F64", "U16", "U32"][i % 4],
            "element_endianness": ["LE", "BE"][i % 2],
            "components": 1 + (i % 4),
            "stride_class": ["PACKED", "PAD8", "PAD16", "PAD32", "LOCAL_VARLEN"][i % 5],
            "alignment": [1, 2, 4, 8, 16][i % 5],
            "grouping": ["SCALAR", "VECTOR", "COUNTED_ARRAY", "LOCAL_RECORD", "RELATION_PAIR"][i % 5],
            "relationship": negative_rel[i - 35] if negative else normal_rel[i % 5],
            "phase_scope": "TRAIN",
            "candidate_semantic_hint": ["structural", "codec", "relation", "sentinel", "explore"][i % 5],
        }
        rows.append(row)
    if len({genotype_hash(r) for r in rows}) != len(rows):
        raise RuntimeError("synthetic generator produced a canonical collision")
    return rows


def public_result_contains_private_material(result: Mapping[str, Any]) -> bool:
    text = canonical_json(result)
    markers = ("raw_bytes", "payload_bytes", "payload_base64", "private_capture_path", "filesystem_path")
    return any(marker in text for marker in markers) or bool(result.get("raw_private_bytes_present"))
