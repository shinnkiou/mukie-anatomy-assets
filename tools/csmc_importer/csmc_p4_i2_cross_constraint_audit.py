#!/usr/bin/env python3
"""Public-safe cross-constraint audit for the six unresolved +965 I2 signatures.

This probe deliberately consumes only durable aggregate facts. It does not read
private payload bytes and does not infer semantic field names.

Question: do already-verified family quotas, five-record cadence, route
correlation, or counted-BE entropy ceilings force any of the six unresolved
q24/q27 equality bits?

Only constraints that directly restrict preserve_signature assignments are
allowed to reduce the assignment set. Structural facts from a different axis
(length cadence, route provenance, codec-start entropy) are recorded but are
not silently converted into signature constraints.
"""
from __future__ import annotations

import itertools
import json

AMBIGUOUS_INDICES = (2, 3, 8, 14, 15, 21)
SIG_A = "0000111"
SIG_B = "0001110"
REQUIRED_COUNTS = {SIG_A: 3, SIG_B: 3}

# Durable orthogonal facts. These are deliberately informational only because
# none establishes a logical mapping to q24/q27 equality for an individual row.
ORTHOGONAL_FACTS = {
    "five_record_group_sums_blocks": [242, 242, 242, 242],
    "group_rows": list(range(20)),
    "tail_rows": [20, 21],
    "container_route": "character",
    "counted_be_control_max_fit": {"surface_a": 6, "surface_b": 5},
    "counted_be_island_max_fit": {"surface_a": 6, "surface_b": 6},
}


def enumerate_assignments() -> list[dict[int, str]]:
    out: list[dict[int, str]] = []
    for a_indices in itertools.combinations(AMBIGUOUS_INDICES, REQUIRED_COUNTS[SIG_A]):
        a_set = set(a_indices)
        assignment = {
            idx: (SIG_A if idx in a_set else SIG_B)
            for idx in AMBIGUOUS_INDICES
        }
        if sum(v == SIG_A for v in assignment.values()) != 3:
            raise AssertionError("quota violation")
        if sum(v == SIG_B for v in assignment.values()) != 3:
            raise AssertionError("quota violation")
        out.append(assignment)
    return out


def audit() -> dict:
    assignments = enumerate_assignments()
    forced: dict[int, str] = {}
    for idx in AMBIGUOUS_INDICES:
        vals = {a[idx] for a in assignments}
        if len(vals) == 1:
            forced[idx] = next(iter(vals))

    return {
        "schema_version": "csmc_p4_i2_cross_constraint_audit_v1",
        "status": "NO_DETERMINISTIC_REDUCTION" if not forced else "FORCED_ROWS_FOUND",
        "ambiguous_record_indices": list(AMBIGUOUS_INDICES),
        "candidate_signatures": [SIG_A, SIG_B],
        "trusted_signature_quota": REQUIRED_COUNTS,
        "complete_assignments_after_all_direct_signature_constraints": len(assignments),
        "forced_signature_rows": {str(k): v for k, v in forced.items()},
        "minimum_new_observation_contract": {
            "recommended": "six corpus-bound q24 equality bits (or q27 equivalents)",
            "quota_assisted_minimum": "five bits only if 3/3 family quota is trusted",
        },
        "orthogonal_facts_not_used_as_signature_constraints": ORTHOGONAL_FACTS,
        "why_not_used": {
            "five_record_cadence": "constrains ordered lengths/group sums, not q24/q27 equality labels",
            "route_correlation": "binds corpus to character surface, not individual preserve_signature",
            "counted_be_entropy_ceiling": "bounds exact counted-BE fits at fixed role starts; it does not determine q24/q27 cross-surface equality",
        },
        "guardrails": [
            "Do not guess ambiguous signatures from family marginals or slot aesthetics.",
            "Do not promote codec or geometry semantics from this audit.",
            "Do not reacquire raw/private payload bytes merely to satisfy this static audit.",
        ],
    }


def self_test() -> None:
    out = audit()
    assert out["status"] == "NO_DETERMINISTIC_REDUCTION", out
    assert out["complete_assignments_after_all_direct_signature_constraints"] == 20, out
    assert out["forced_signature_rows"] == {}, out
    assignments = enumerate_assignments()
    for idx in AMBIGUOUS_INDICES:
        assert {a[idx] for a in assignments} == {SIG_A, SIG_B}
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    self_test()
    print(json.dumps(audit(), indent=2, sort_keys=True))
