#!/usr/bin/env python3
"""Public-safe pair evidence for phase-normalized exact invariant regions.

This sidecar does not change Structural IR v0.1 meanings. It records only
aggregate offsets/lengths derived from authorized controlled fixtures and
forbids semantic promotion from invariant-region evidence alone.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SCHEMA_VERSION = "csmc_pair_invariant_evidence_v0_1"


@dataclass(frozen=True)
class PairInvariantEvidence:
    evidence_id: str
    corpus_sha256: str
    fixture_a: str
    fixture_b: str
    fixture_a_sha256: str
    fixture_b_sha256: str
    logical_mod8_a: int
    logical_mod8_b: int
    qword_count_a: int
    qword_count_b: int
    invariant_start_a: int
    invariant_start_b: int
    invariant_length_qwords: int
    trailing_qwords_a: int
    trailing_qwords_b: int
    relationship_type: str = "EXACT_INVARIANT_REGION"
    candidate_semantic: str = "STRUCTURAL_PHASE_CLASS"
    semantic_promotion: bool = False
    raw_values_embedded: bool = False
    blender_emit_ready: bool = False

    def to_dict(self) -> dict:
        return {"schema_version": SCHEMA_VERSION, **asdict(self)}


def validate_pair_invariant(e: PairInvariantEvidence) -> list[str]:
    errors: list[str] = []
    if not e.evidence_id:
        errors.append("evidence_id required")
    if not e.fixture_a or not e.fixture_b or e.fixture_a == e.fixture_b:
        errors.append("two distinct fixture ids required")
    for name, value in (
        ("corpus_sha256", e.corpus_sha256),
        ("fixture_a_sha256", e.fixture_a_sha256),
        ("fixture_b_sha256", e.fixture_b_sha256),
    ):
        if not SHA256_RE.fullmatch(value):
            errors.append(f"{name}: lowercase SHA-256 required")
    for name, value in (
        ("logical_mod8_a", e.logical_mod8_a),
        ("logical_mod8_b", e.logical_mod8_b),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 7:
            errors.append(f"{name}: integer 0..7 required")
    if e.logical_mod8_a != e.logical_mod8_b:
        errors.append("phase-normalized invariant evidence requires equal logical_mod8")
    for name, value in (
        ("qword_count_a", e.qword_count_a),
        ("qword_count_b", e.qword_count_b),
        ("invariant_start_a", e.invariant_start_a),
        ("invariant_start_b", e.invariant_start_b),
        ("invariant_length_qwords", e.invariant_length_qwords),
        ("trailing_qwords_a", e.trailing_qwords_a),
        ("trailing_qwords_b", e.trailing_qwords_b),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{name}: non-negative integer required")
    if e.invariant_length_qwords <= 0:
        errors.append("invariant_length_qwords must be positive")
    if e.invariant_start_a + e.invariant_length_qwords + e.trailing_qwords_a != e.qword_count_a:
        errors.append("fixture A invariant bounds do not close at payload end")
    if e.invariant_start_b + e.invariant_length_qwords + e.trailing_qwords_b != e.qword_count_b:
        errors.append("fixture B invariant bounds do not close at payload end")
    if e.relationship_type != "EXACT_INVARIANT_REGION":
        errors.append("unsupported relationship_type")
    if e.candidate_semantic != "STRUCTURAL_PHASE_CLASS":
        errors.append("candidate_semantic must remain STRUCTURAL_PHASE_CLASS")
    if e.semantic_promotion:
        errors.append("pair invariant evidence cannot directly promote semantics")
    if e.raw_values_embedded:
        errors.append("raw_values_embedded must be false")
    if e.blender_emit_ready:
        errors.append("blender_emit_ready must be false")
    return errors
