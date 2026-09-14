#!/usr/bin/env python3
from __future__ import annotations
from copy import deepcopy
from typing import Any, Iterable, Mapping

POLICY_VERSION = "csmc_importer_lab_policy_v0_1"

OPEN_CANDIDATE_FAMILIES = {
    "LOCAL_COUNTED_NUMERIC_BLOCK",
    "LOCAL_INDEX_RANGE_BLOCK",
    "LOCAL_INTERLEAVED_TUPLE",
    "BOUNDARY_REPEATED_RECORD",
    "RELATIONSHIP_ONLY",
    "NULL_DECOY",
}

# Scope matters: these rejections do not ban local sub-block hypotheses.
REJECTED_FAMILIES = {
    "WHOLE_PAYLOAD_SIMPLE_FIXED_STRIDE": {
        "status": "REJECTED",
        "scope": "whole stored payload only",
        "reason": "preregistered whole-region fixed-stride size laws failed controlled fixtures",
    },
    "WHOLE_PHASE_PREFIX_SIMPLE_FIXED_STRIDE": {
        "status": "REJECTED",
        "scope": "whole phase-normalized prefix only",
        "reason": "preregistered whole-prefix fixed-stride laws failed controlled fixtures",
    },
    "PLAINTEXT_NAME_CARVING": {
        "status": "REJECTED",
        "scope": "ASCII/UTF-16 literal teacher identifiers on tested surfaces",
        "reason": "controlled negative control found zero tested plaintext identifiers",
    },
    "OLD_OWNER_EDGE_RESCAN": {
        "status": "CLOSED",
        "scope": "former parent boundary/length/crossref gaps",
        "reason": "MODELER 1.10.13 FIRST PASS already confirmed these evidence classes",
    },
    "EXACT_QWORD_BRUTE_FORCE_REPETITION": {
        "status": "REJECTED_AS_PRODUCTIVE_METHOD",
        "scope": "tested bounded variable prefixes",
        "reason": "phase-normalized bounded prefix exact-qword reuse was not productive",
    },
}

FROZEN_SCORE_SPEC = {
    "train_relationship": 35.0,
    "validation_generalization": 25.0,
    "negative_control_resistance": 20.0,
    "cross_fixture_stability": 10.0,
    "parsimony": 10.0,
    "parse_success_points": 0.0,
    "visual_similarity_points": 0.0,
}

HARD_CONSTRAINTS = {
    "max_logical_batch": 50,
    "allowed_concurrency": [1, 2],
    "semantic_promotion": False,
    "diagnostic_only": True,
    "blender_emit": False,
    "holdout_used_for_selection": False,
    "max_exploit_mutation_loci": 1,
}


def assert_candidate_family_open(family: str) -> None:
    if family in REJECTED_FAMILIES:
        item = REJECTED_FAMILIES[family]
        raise ValueError(f"candidate family is closed: {family}: {item['reason']}")
    if family not in OPEN_CANDIDATE_FAMILIES:
        raise ValueError(f"candidate family is not in frozen open set: {family}")


def build_holdout_ledger(fixtures: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    entries: dict[str, Any] = {}
    for fixture in fixtures:
        fixture_id = str(fixture["fixture_id"])
        split = str(fixture["split"])
        if split not in {"TRAIN", "VALIDATION", "NEGATIVE", "HOLDOUT", "EXTERNAL_BENCHMARK"}:
            raise ValueError(f"unknown split for {fixture_id}: {split}")
        entries[fixture_id] = {
            "declared_split": split,
            "current_split": split,
            "exposure_count": 0,
            "first_exposed_generation": None,
            "last_exposed_generation": None,
            "used_for_selection": False,
        }
    return {
        "schema_version": "csmc_importer_lab_holdout_ledger_v0_1",
        "policy_version": POLICY_VERSION,
        "entries": entries,
    }


def record_exposure(
    ledger: Mapping[str, Any],
    *,
    fixture_id: str,
    generation: int,
    used_for_selection: bool,
) -> dict[str, Any]:
    out = deepcopy(dict(ledger))
    entries = out["entries"]
    if fixture_id not in entries:
        raise ValueError(f"unknown fixture_id: {fixture_id}")
    row = entries[fixture_id]
    row["exposure_count"] += 1
    row["first_exposed_generation"] = (
        generation if row["first_exposed_generation"] is None else row["first_exposed_generation"]
    )
    row["last_exposed_generation"] = generation
    if used_for_selection:
        row["used_for_selection"] = True
        if row["current_split"] in {"HOLDOUT", "EXTERNAL_BENCHMARK"}:
            row["current_split"] = "VALIDATION_CONTAMINATED"
    return out
