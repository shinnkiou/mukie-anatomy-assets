#!/usr/bin/env python3
from __future__ import annotations
from hashlib import sha256
import json
from typing import Any, Mapping, Iterable

SCHEMA_VERSION = "csmc_importer_lab_consumer_compatibility_v1"
RESULTS = {"CONSUMER_COMPATIBLE", "CONSUMER_CONTRADICTED", "CONSUMER_UNRESOLVED"}
KNOWN_LOADER = "Canvas3DModelLoader"
KNOWN_EXTERNAL_LOOKUP = "EXTERNAL_ID_TO_OFFSET"

# Behavioral keys intentionally exclude hypothesis_id, semantic_label, visualization output,
# score, and prose labels. Semantic relabeling cannot manufacture a new candidate.
BEHAVIOR_KEYS = (
    "family", "consumer_scope", "externalchunk_corridor", "read_width",
    "endianness", "count_source", "grouping", "relationship",
    "destination_kind", "external_lookup_mode", "modeldata_loader_binding",
)

def canonical_behavior_key(candidate: Mapping[str, Any]) -> str:
    payload = {k: candidate.get(k) for k in BEHAVIOR_KEYS}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw).hexdigest()

def _c01(candidate: Mapping[str, Any]) -> tuple[bool, bool, bool, str]:
    applicable = candidate.get("externalchunk_corridor") is True
    if not applicable:
        return False, False, False, "C01 not applicable"
    mode = candidate.get("external_lookup_mode")
    if mode is None:
        return True, False, True, "C01 applicable but lookup mode unresolved"
    if mode != KNOWN_EXTERNAL_LOOKUP:
        return True, True, False, "Contradicts confirmed ExternalID -> Offset lookup"
    return True, False, False, "Compatible with confirmed ExternalID -> Offset lookup"

def _c02(candidate: Mapping[str, Any]) -> tuple[bool, bool, bool, str]:
    applicable = candidate.get("consumer_scope") == "MODELDATA_CONSUMER_PATH"
    if not applicable:
        return False, False, False, "C02 not applicable"
    binding = candidate.get("modeldata_loader_binding")
    if binding is None:
        return True, False, True, "C02 applicable but loader binding unresolved"
    if binding != KNOWN_LOADER:
        return True, True, False, "Contradicts confirmed ModelData -> Canvas3DModelLoader binding"
    return True, False, False, "Compatible with confirmed ModelData -> Canvas3DModelLoader binding"

def classify_consumer_compatibility(candidate: Mapping[str, Any]) -> dict[str, Any]:
    applicable, contradicted, unresolved, notes = [], [], [], []
    for cid, fn in (("C01", _c01), ("C02", _c02)):
        app, bad, unknown, note = fn(candidate)
        if app:
            applicable.append(cid)
        if bad:
            contradicted.append(cid)
        if unknown:
            unresolved.append(cid)
        notes.append(f"{cid}: {note}")
    if contradicted:
        result = "CONSUMER_CONTRADICTED"
    elif applicable and not unresolved:
        result = "CONSUMER_COMPATIBLE"
    else:
        result = "CONSUMER_UNRESOLVED"
    hard_reject = bool(contradicted)
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": str(candidate.get("candidate_id", "UNNAMED")),
        "result_class": result,
        "hard_reject": hard_reject,
        "survives": not hard_reject,
        "applicable_constraints": applicable,
        "contradicted_constraints": contradicted,
        "unresolved_constraints": unresolved,
        "consumer_bonus": 0,
        "visual_score_delta": 0,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "notes": notes,
    }

def dedupe_survivors(candidates: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    if not isinstance(candidates, list):
        candidates = list(candidates)
    survivors, rejected, duplicates, seen = [], [], [], {}
    for candidate in candidates:
        result = classify_consumer_compatibility(candidate)
        if result["hard_reject"]:
            rejected.append({"candidate_id": candidate["candidate_id"], "result": result})
            continue
        key = canonical_behavior_key(candidate)
        if key in seen:
            duplicates.append({
                "candidate_id": candidate["candidate_id"],
                "duplicate_of": seen[key],
                "behavior_key": key,
            })
            continue
        seen[key] = candidate["candidate_id"]
        survivors.append({"candidate": dict(candidate), "consumer_result": result, "behavior_key": key})
    return {
        "input_count": len(candidates),
        "survivor_count": len(survivors),
        "hard_reject_count": len(rejected),
        "duplicate_count": len(duplicates),
        "survivors": survivors,
        "hard_rejects": rejected,
        "duplicates": duplicates,
        "semantic_promotion": False,
    }

def generate_consumer_constrained_synthetic_50() -> list[dict[str, Any]]:
    """Public-safe synthetic proposal generation only; no private bytes and no semantic truth."""
    families = [
        ("READER_WIDTH_ENDIAN", 15),
        ("COUNT_LENGTH_RELATION", 10),
        ("LOCAL_BLOCK_LAYOUT", 10),
        ("DESTINATION_CONTAINER_RELATION", 10),
        ("NEGATIVE_DECOY", 5),
    ]
    widths = [2, 4, 8, 4, 2]
    endians = ["LE", "BE"]
    count_sources = ["parent_length", "local_count", "derived_count", "sentinel_terminated"]
    groupings = ["scalar", "vec2", "vec3", "vec4", "interleaved_tuple"]
    destinations = ["array", "vector_container", "node_structure", "mesh_like_structure", "generic_model_data"]
    rows: list[dict[str, Any]] = []
    n = 0
    for family, count in families:
        for i in range(count):
            scope = "MODELDATA_CONSUMER_PATH" if i % 3 != 2 else "UNRELATED_RECORD_FAMILY"
            external = (i % 4 == 0)
            row = {
                "candidate_id": f"CCG1_{n:02d}",
                "family": family,
                "consumer_scope": scope,
                "externalchunk_corridor": external,
                "read_width": widths[i % len(widths)],
                "endianness": endians[i % 2],
                "count_source": count_sources[i % len(count_sources)],
                "grouping": groupings[i % len(groupings)],
                "relationship": ["count_to_block_length","count_to_repeated_elements","reference_domain_bound","local_stride"][i % 4],
                "destination_kind": destinations[i % len(destinations)],
                "external_lookup_mode": KNOWN_EXTERNAL_LOOKUP if external else None,
                "modeldata_loader_binding": KNOWN_LOADER if scope == "MODELDATA_CONSUMER_PATH" else None,
                "semantic_label": "STRUCTURAL_ONLY",
                "visual_similarity": 0.0,
            }
            if (family == "NEGATIVE_DECOY" and i in {0, 1}) or (family == "DESTINATION_CONTAINER_RELATION" and i == 7):
                row["consumer_scope"] = "MODELDATA_CONSUMER_PATH"
                row["modeldata_loader_binding"] = "OtherLoader"
            if family == "LOCAL_BLOCK_LAYOUT" and i == 9:
                row["externalchunk_corridor"] = True
                row["external_lookup_mode"] = "DIRECT_PAYLOAD_OFFSET_WITHOUT_EXTERNAL_ID"
            if family in {"COUNT_LENGTH_RELATION","LOCAL_BLOCK_LAYOUT"} and i in {8, 9}:
                base = rows[-2]
                row.update({k: base.get(k) for k in BEHAVIOR_KEYS})
                row["semantic_label"] = "GEOMETRY_OR_TOPOLOGY_TARGET"
            rows.append(row)
            n += 1
    assert len(rows) == 50
    return rows

def synthetic_generation_summary() -> dict[str, Any]:
    rows = generate_consumer_constrained_synthetic_50()
    out = dedupe_survivors(rows)
    out["family_budget"] = {
        "READER_WIDTH_ENDIAN": 15,
        "COUNT_LENGTH_RELATION": 10,
        "LOCAL_BLOCK_LAYOUT": 10,
        "DESTINATION_CONTAINER_RELATION": 10,
        "NEGATIVE_DECOY": 5,
    }
    out["execution_class"] = "SYNTHETIC_PUBLIC_SAFE_CONSTRAINT_TEST_ONLY"
    out["fill_to_50_after_prune"] = False
    out["classic_ga"] = False
    out["search_method"] = "CONSTRAINT_GUIDED_BEAM_SEARCH_PLUS_FALSIFICATION"
    return out
