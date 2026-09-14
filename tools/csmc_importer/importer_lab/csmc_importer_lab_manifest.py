#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Any, Mapping

SCHEMA_VERSION = "csmc_importer_lab_manifest_v0_1"
ALLOWED_ENGINE_MODES = {"SYNTHETIC_ONLY", "PRIVATE_EVALUATOR"}
ALLOWED_REGION_CLASSES = {
    "SYNTHETIC_REGION",
    "VARIABLE_PREFIX_CANDIDATE_REGION",
    "TERMINAL_REMAINDER_CANDIDATE_REGION",
}
ALLOWED_ENDIANNESS = {"be", "le", "na"}
ALLOWED_ELEMENT_TYPES = {"bytes", "u16", "u32", "f32", "f64", "opaque"}
ALLOWED_STRIDES = {1, 2, 4, 8, 12, 16, 24, 32}
ALLOWED_COMPONENTS = {1, 2, 3, 4}
ALLOWED_RELATIONSHIPS = {
    "COUNT_EQUALS_LABEL",
    "COUNT_LINEAR_LABEL",
    "MAX_LT_LABEL",
    "MONOTONIC_WITH_LABEL",
    "FIXED_RECORD_REPEAT",
    "REFERENCE_DOMAIN",
    "NULL_DECOY",
}
ALLOWED_CANDIDATE_SEMANTICS = {
    "STRUCTURAL_ONLY",
    "GEOMETRY_OR_TOPOLOGY_TARGET",
    "NULL_DECOY",
}
FORBIDDEN_KEYS = {
    "best_offset_per_fixture",
    "custom_score_formula",
    "holdout_override",
    "special_case_for_fixture",
    "threshold_for_this_candidate",
    "semantic_truth",
    "promotion",
    "blender_ready",
}
CANONICAL_PARAMETER_KEYS = (
    "engine_mode", "region_class", "region_id", "anchor_id", "relative_offset",
    "count_source", "count_type", "endianness", "element_type", "stride", "components",
    "grouping", "relationship", "candidate_semantic", "preprocess",
)


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class HypothesisManifest:
    hypothesis_id: str
    generation: int
    engine_mode: str
    region_class: str
    region_id: str
    anchor_id: str
    relative_offset: int
    count_source: str
    count_type: str
    endianness: str
    element_type: str
    stride: int
    components: int
    grouping: str
    relationship: str
    candidate_semantic: str
    preprocess: str = "NONE"
    parent_hypothesis_id: str | None = None
    preregistered_prediction: str = ""
    negative_control_set: tuple[str, ...] = ()
    semantic_promotion: bool = False
    diagnostic_only: bool = True
    blender_emit: bool = False
    synthetic_fault: str | None = None

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "HypothesisManifest":
        extra = set(row) - set(cls.__dataclass_fields__)
        forbidden = extra & FORBIDDEN_KEYS
        if forbidden:
            raise ManifestError(f"forbidden keys: {sorted(forbidden)}")
        if extra:
            raise ManifestError(f"unknown keys: {sorted(extra)}")
        data = dict(row)
        if "negative_control_set" in data:
            data["negative_control_set"] = tuple(data["negative_control_set"])
        obj = cls(**data)
        obj.validate()
        return obj

    def validate(self) -> None:
        if not self.hypothesis_id or len(self.hypothesis_id) > 128:
            raise ManifestError("invalid hypothesis_id")
        if self.generation < 0:
            raise ManifestError("generation must be >=0")
        if self.engine_mode not in ALLOWED_ENGINE_MODES:
            raise ManifestError("invalid engine_mode")
        if self.region_class not in ALLOWED_REGION_CLASSES:
            raise ManifestError("invalid region_class")
        if self.endianness not in ALLOWED_ENDIANNESS:
            raise ManifestError("invalid endianness")
        if self.element_type not in ALLOWED_ELEMENT_TYPES:
            raise ManifestError("invalid element_type")
        if self.stride not in ALLOWED_STRIDES:
            raise ManifestError("stride outside frozen candidate set")
        if self.components not in ALLOWED_COMPONENTS:
            raise ManifestError("components outside frozen candidate set")
        if self.relationship not in ALLOWED_RELATIONSHIPS:
            raise ManifestError("relationship outside frozen candidate set")
        if self.candidate_semantic not in ALLOWED_CANDIDATE_SEMANTICS:
            raise ManifestError("candidate_semantic is too specific or unknown")
        if self.relative_offset < 0:
            raise ManifestError("relative_offset must be >=0")
        if self.semantic_promotion is not False:
            raise ManifestError("semantic_promotion must remain false")
        if self.diagnostic_only is not True:
            raise ManifestError("diagnostic_only must remain true")
        if self.blender_emit is not False:
            raise ManifestError("blender_emit must remain false")
        if self.synthetic_fault is not None and self.engine_mode != "SYNTHETIC_ONLY":
            raise ManifestError("synthetic_fault forbidden outside SYNTHETIC_ONLY")
        if self.candidate_semantic == "NULL_DECOY" and self.relationship != "NULL_DECOY":
            raise ManifestError("NULL_DECOY semantic requires NULL_DECOY relationship")
        if self.element_type == "bytes" and self.endianness != "na":
            raise ManifestError("byte candidates must use endianness=na")
        if self.element_type in {"u16", "u32", "f32", "f64"} and self.endianness == "na":
            raise ManifestError("numeric candidates require explicit endianness")
        item_size = {"u16": 2, "u32": 4, "f32": 4, "f64": 8}.get(self.element_type, 1)
        if self.components * item_size > self.stride:
            raise ManifestError("components do not fit in stride")

    def canonical_parameters(self) -> dict[str, Any]:
        row = asdict(self)
        return {k: row[k] for k in CANONICAL_PARAMETER_KEYS}

    def canonical_key(self) -> str:
        raw = json.dumps(self.canonical_parameters(), sort_keys=True, separators=(",", ":")).encode()
        return sha256(raw).hexdigest()

    def manifest_hash(self) -> str:
        row = asdict(self)
        row["negative_control_set"] = list(self.negative_control_set)
        raw = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
        return sha256(raw).hexdigest()


def changed_loci(parent: HypothesisManifest, child: HypothesisManifest) -> list[str]:
    a = parent.canonical_parameters()
    b = child.canonical_parameters()
    return [k for k in CANONICAL_PARAMETER_KEYS if a[k] != b[k]]


def validate_child_mutation(
    parent: HypothesisManifest,
    child: HypothesisManifest,
    max_loci: int = 1,
) -> list[str]:
    if child.parent_hypothesis_id != parent.hypothesis_id:
        raise ManifestError("parent_hypothesis_id mismatch")
    if child.generation != parent.generation + 1:
        raise ManifestError("generation must increment exactly once")
    loci = changed_loci(parent, child)
    if len(loci) > max_loci:
        raise ManifestError(f"too many changed loci: {loci}")
    return loci
