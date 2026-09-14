#!/usr/bin/env python3
"""Public-safe sidecar evidence schema for controlled CSMC differentials.

This does not replace csmc_structural_ir_v0_1 and does not change the meaning of
its existing axes. It attaches controlled-evidence provenance and confidence to
candidate semantics while keeping confirmed semantic claims fail-closed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VALID_I3 = {"I3_VALID", "I3_PARTIAL", "I3_INVALID"}
VALID_CONFIDENCE = set(range(6))


@dataclass(frozen=True)
class ControlledEvidence:
    evidence_id: str
    evidence_source: str
    controlled_fixture_ids: tuple[str, ...]
    relationship_type: str
    negative_control_ids: tuple[str, ...]
    independent_validation_ids: tuple[str, ...]
    supporting_relationship_ids: tuple[str, ...]
    candidate_semantic: str
    confidence_level: int
    validation_status: str
    source_sha256: tuple[str, ...]
    counterexample_count: int = 0
    semantic_promotion: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def validate_evidence(e: ControlledEvidence) -> list[str]:
    errors=[]
    if not e.evidence_id: errors.append("evidence_id required")
    if not e.evidence_source: errors.append("evidence_source required")
    if len(e.controlled_fixture_ids) < 2: errors.append("at least two controlled fixture ids required")
    if e.confidence_level not in VALID_CONFIDENCE: errors.append("confidence level must be 0..5")
    if e.validation_status not in VALID_I3: errors.append("validation_status must be I3_VALID/PARTIAL/INVALID")
    if e.counterexample_count < 0: errors.append("counterexample_count cannot be negative")
    if not e.source_sha256 or any(not SHA256_RE.fullmatch(x) for x in e.source_sha256): errors.append("lowercase SHA-256 provenance required")

    if e.semantic_promotion:
        if e.confidence_level != 5:
            errors.append("semantic promotion requires confidence level 5")
        if e.validation_status != "I3_VALID":
            errors.append("semantic promotion requires I3_VALID")
        if not e.negative_control_ids:
            errors.append("semantic promotion requires a negative control")
        if not e.independent_validation_ids:
            errors.append("semantic promotion requires independent validation")
        if len(e.supporting_relationship_ids) < 2:
            errors.append("semantic promotion requires at least two supporting relationships")
        if e.counterexample_count != 0:
            errors.append("semantic promotion requires zero counterexamples")
    return errors
