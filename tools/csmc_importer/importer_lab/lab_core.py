from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

SCHEMA_VERSION = "csmc_importer_lab_hypothesis_v0_1"
PIPELINE_STAGE = "STRUCTURAL_ONLY"

ALLOWED_FAMILIES = {
    "LOCAL_BOUNDARY_LENGTH",
    "COUNT_SCALAR_CODEC",
    "LOCAL_RECORD_LAYOUT",
    "CROSS_BLOCK_RELATIONSHIP",
    "REFERENCE_DOMAIN",
    "NEGATIVE_CONTROL",
}

REJECTED_FAMILIES = {
    "WHOLE_PAYLOAD_SIMPLE_FIXED_STRIDE",
    "WHOLE_PHASE_PREFIX_SIMPLE_FIXED_STRIDE",
    "PLAINTEXT_NAME_CARVING",
    "EXACT_QWORD_BRUTE_FORCE_REPETITION",
    "OLD_OWNER_EDGE_RESCAN",
}

ALLOWED_COUNT_SOURCES = {
    "NONE",
    "LOCAL_SCALAR",
    "LOCAL_LENGTH_DIV_STRIDE",
    "PEER_BLOCK_COUNT",
    "PEER_BLOCK_LENGTH",
}
ALLOWED_COUNT_TYPES = {"NONE", "u16", "u32", "u64"}
ALLOWED_ENDIANNESS = {"NONE", "LE", "BE"}
ALLOWED_ELEMENT_TYPES = {"NONE", "u8", "u16", "u32", "f32", "f64"}
ALLOWED_STRIDES = {0, 2, 4, 8, 12, 16, 24, 32}
ALLOWED_COMPONENTS = {0, 1, 2, 3, 4}
ALLOWED_RELATIONSHIPS = {
    "NONE",
    "LENGTH_EQ_COUNT_X_STRIDE",
    "REFERENCE_LT_PEER_COUNT",
    "PAIR_DELTA_TRACKS_COUNT",
    "COUNT_SHARED_ACROSS_BLOCKS",
}
ALLOWED_SOURCE_SCOPES = {"BOUNDED_STRUCTURAL_REGION"}
ALLOWED_COUPLED_MUTATIONS = {
    frozenset({"element_type", "endianness"}),
    frozenset({"components", "stride_bytes"}),
}
FORBIDDEN_TUNING_FIELDS = {
    "absolute_offset",
    "arbitrary_coefficient",
    "score_weights",
    "holdout_release",
    "semantic_truth",
    "semantic_confidence",
    "visual_similarity_score",
    "numeric_plausibility_score",
    "blender_ready",
    "mainline_adopt",
}

SCORING_WEIGHTS = {
    "controlled_differential": 30,
    "withheld_validation": 25,
    "negative_controls": 20,
    "structural_consistency": 10,
    "consumer_evidence": 10,
    "simplicity": 5,
}


class ManifestRejected(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "candidate_id",
        "candidate_family",
        "source_scope",
        "segment_id",
        "anchor_id",
        "relative_offset_bytes",
        "count_source_template",
        "count_type",
        "endianness",
        "element_type",
        "stride_bytes",
        "components",
        "relationship",
        "candidate_semantic",
        "diagnostic_only",
        "semantic_promotion",
        "blender_emit",
        "evidence_snapshot",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ManifestRejected(f"missing required fields: {missing}")

    forbidden_present = sorted(FORBIDDEN_TUNING_FIELDS & set(manifest))
    if forbidden_present:
        raise ManifestRejected(f"forbidden tuning fields: {forbidden_present}")

    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ManifestRejected("wrong schema_version")
    if not isinstance(manifest["candidate_id"], str) or not manifest["candidate_id"].strip():
        raise ManifestRejected("candidate_id must be non-empty")
    if manifest["candidate_family"] in REJECTED_FAMILIES:
        raise ManifestRejected("rejected family cannot re-enter without a new external evidence revision")
    if manifest["candidate_family"] not in ALLOWED_FAMILIES:
        raise ManifestRejected("candidate_family is outside GEN0 grammar")
    if manifest["source_scope"] not in ALLOWED_SOURCE_SCOPES:
        raise ManifestRejected("only bounded structural regions are allowed")
    if not isinstance(manifest["segment_id"], str) or not manifest["segment_id"]:
        raise ManifestRejected("segment_id required")
    if not isinstance(manifest["anchor_id"], str) or not manifest["anchor_id"]:
        raise ManifestRejected("anchor_id required")

    rel = manifest["relative_offset_bytes"]
    if not isinstance(rel, int) or not -64 <= rel <= 64:
        raise ManifestRejected("relative_offset_bytes must be an integer in [-64,64]")
    if manifest["count_source_template"] not in ALLOWED_COUNT_SOURCES:
        raise ManifestRejected("unsupported count source")
    if manifest["count_type"] not in ALLOWED_COUNT_TYPES:
        raise ManifestRejected("unsupported count type")
    if manifest["endianness"] not in ALLOWED_ENDIANNESS:
        raise ManifestRejected("unsupported endianness")
    if manifest["element_type"] not in ALLOWED_ELEMENT_TYPES:
        raise ManifestRejected("unsupported element type")
    if manifest["stride_bytes"] not in ALLOWED_STRIDES:
        raise ManifestRejected("unsupported bounded local stride")
    if manifest["components"] not in ALLOWED_COMPONENTS:
        raise ManifestRejected("unsupported components")
    if manifest["relationship"] not in ALLOWED_RELATIONSHIPS:
        raise ManifestRejected("unsupported relationship")

    if manifest["candidate_semantic"] != "UNRESOLVED":
        raise ManifestRejected("GEN0 cannot assert geometry/index/material/UV/weight semantics")
    if manifest["diagnostic_only"] is not True:
        raise ManifestRejected("candidate must be diagnostic_only")
    if manifest["semantic_promotion"] is not False:
        raise ManifestRejected("semantic_promotion must stay false")
    if manifest["blender_emit"] is not False:
        raise ManifestRejected("blender_emit must stay false")

    snapshot = manifest["evidence_snapshot"]
    if not isinstance(snapshot, Mapping):
        raise ManifestRejected("evidence_snapshot must be an object")
    if snapshot.get("pipeline_stage") != PIPELINE_STAGE:
        raise ManifestRejected("evidence snapshot must be STRUCTURAL_ONLY")
    if snapshot.get("semantic_promotion_count") != 0:
        raise ManifestRejected("evidence snapshot semantic_promotion_count must be zero")
    if snapshot.get("blender_emit_ready") is not False:
        raise ManifestRejected("evidence snapshot blender_emit_ready must be false")
    if not snapshot.get("structural_ir_schema"):
        raise ManifestRejected("structural_ir_schema provenance is required")

    mutation_fields = manifest.get("mutation_fields", [])
    if not isinstance(mutation_fields, list):
        raise ManifestRejected("mutation_fields must be a list")
    if len(mutation_fields) > 2:
        raise ManifestRejected("at most one mutation or one preregistered coupled mutation is allowed")
    if len(mutation_fields) == 2 and frozenset(mutation_fields) not in ALLOWED_COUPLED_MUTATIONS:
        raise ManifestRejected("two-field mutation is not a preregistered coupled mutation")


def canonical_genotype(manifest: Mapping[str, Any]) -> Dict[str, Any]:
    validate_manifest(manifest)
    keys = (
        "schema_version",
        "candidate_family",
        "source_scope",
        "segment_id",
        "anchor_id",
        "relative_offset_bytes",
        "count_source_template",
        "count_type",
        "endianness",
        "element_type",
        "stride_bytes",
        "components",
        "relationship",
    )
    return {key: manifest[key] for key in keys}


def genotype_hash(manifest: Mapping[str, Any]) -> str:
    return _sha256_json(canonical_genotype(manifest))


def phenotype_hash(observation: Mapping[str, Any]) -> str:
    public_shape = {
        "parsed_ranges": observation.get("parsed_ranges", []),
        "element_counts": observation.get("element_counts", {}),
        "relationship_outcomes": observation.get("relationship_outcomes", {}),
    }
    return _sha256_json(public_shape)


def dedupe_manifests(manifests: Sequence[Mapping[str, Any]]) -> Tuple[List[Mapping[str, Any]], List[str]]:
    if len(manifests) > 50:
        raise ManifestRejected("logical candidate batch may not exceed 50")
    unique: List[Mapping[str, Any]] = []
    duplicate_ids: List[str] = []
    seen: set[str] = set()
    for manifest in manifests:
        validate_manifest(manifest)
        digest = genotype_hash(manifest)
        if digest in seen:
            duplicate_ids.append(str(manifest["candidate_id"]))
            continue
        seen.add(digest)
        unique.append(manifest)
    return unique, duplicate_ids


def score_candidate(metrics: Mapping[str, Any]) -> Dict[str, Any]:
    """Score means NEXT-TEST PRIORITY only. It is never semantic truth."""
    if metrics.get("parse_valid") is not True:
        return {"admitted": False, "score": 0.0, "reason": "PARSE_GATE_REJECT"}
    if metrics.get("hard_constraints_pass") is not True:
        return {"admitted": False, "score": 0.0, "reason": "HARD_CONSTRAINT_REJECT"}

    total = 0.0
    components: Dict[str, float] = {}
    for name, weight in SCORING_WEIGHTS.items():
        value = float(metrics.get(name, 0.0))
        if value < 0.0 or value > 1.0:
            raise ManifestRejected(f"score component {name} must be in [0,1]")
        weighted = value * weight
        components[name] = weighted
        total += weighted

    # Deliberately excluded from fitness: visual similarity, generic numeric plausibility,
    # candidate semantic labels, and parse success itself.
    return {
        "admitted": True,
        "score": round(total, 6),
        "reason": "NEXT_TEST_PRIORITY_ONLY",
        "components": components,
        "ignored_direct_score_fields": [
            "visual_similarity",
            "generic_numeric_plausibility",
            "candidate_semantic",
            "parse_valid",
        ],
    }


def validate_holdout_ledger(ledger: Mapping[str, Any]) -> None:
    if ledger.get("V01", {}).get("role") != "LOCKED_AUDIT_SET":
        raise ManifestRejected("V01 must remain LOCKED_AUDIT_SET in M0/M1")
    if ledger.get("V01", {}).get("pristine_holdout") is not False:
        raise ManifestRejected("V01 is not a pristine holdout after prior structural use")
    if ledger.get("semantic_promotion") is not False:
        raise ManifestRejected("holdout ledger cannot authorize semantic promotion")


def validate_gen0_plan(plan: Mapping[str, Any]) -> None:
    expected = {
        "LOCAL_BOUNDARY_LENGTH": 14,
        "COUNT_SCALAR_CODEC": 10,
        "LOCAL_RECORD_LAYOUT": 10,
        "CROSS_BLOCK_RELATIONSHIP": 6,
        "REFERENCE_DOMAIN": 5,
        "NEGATIVE_CONTROL": 5,
    }
    if plan.get("candidate_family_counts") != expected:
        raise ManifestRejected("GEN0 family allocation differs from frozen design review")
    if sum(expected.values()) != 50:
        raise AssertionError("internal GEN0 allocation error")
    if plan.get("semantic_scope") != "UNRESOLVED_LOCAL_SUBBLOCK_GRAMMAR_ONLY":
        raise ManifestRejected("GEN0 semantic scope widened")
    if plan.get("private_csmc_execution") is not False:
        raise ManifestRejected("M0/M1 must not execute private CSMC GEN0")


def make_synthetic_manifest(candidate_id: str = "SYN-001", **overrides: Any) -> Dict[str, Any]:
    manifest: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "candidate_family": "LOCAL_BOUNDARY_LENGTH",
        "source_scope": "BOUNDED_STRUCTURAL_REGION",
        "segment_id": "SYNTHETIC_VARIABLE_PREFIX",
        "anchor_id": "SYNTHETIC_ANCHOR_A",
        "relative_offset_bytes": 0,
        "count_source_template": "LOCAL_SCALAR",
        "count_type": "u32",
        "endianness": "LE",
        "element_type": "u32",
        "stride_bytes": 4,
        "components": 1,
        "relationship": "LENGTH_EQ_COUNT_X_STRIDE",
        "candidate_semantic": "UNRESOLVED",
        "diagnostic_only": True,
        "semantic_promotion": False,
        "blender_emit": False,
        "mutation_fields": [],
        "evidence_snapshot": {
            "pipeline_stage": PIPELINE_STAGE,
            "semantic_promotion_count": 0,
            "blender_emit_ready": False,
            "structural_ir_schema": "csmc_controlled_segment_ir_v0_1",
        },
    }
    manifest.update(overrides)
    return manifest
