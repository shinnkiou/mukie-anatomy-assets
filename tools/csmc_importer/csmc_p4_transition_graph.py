#!/usr/bin/env python3
"""Build a semantics-free graph over already-public CSMC correspondence transitions.

The graph distinguishes reversible sparse excursions, local length-changing child
candidates, and section-scale repack/reorder candidates without naming payload
semantics or serializer functions.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA = "csmc_p4_transition_graph_v1"
ALLOWED_CLASSES = {
    "LOCAL_LENGTH_CHANGING_CHILD_CANDIDATE",
    "SPARSE_EXCURSION_BOUNDARY",
    "SECTION_REPACK_OR_REORDER_CANDIDATE",
    "UNRESOLVED_TRANSITION",
}


def _require_bool(row: dict, key: str, errors: list[str], prefix: str) -> None:
    if not isinstance(row.get(key), bool):
        errors.append(f"{prefix}_malformed_{key}")


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    if doc.get("schema_version") != SCHEMA:
        errors.append("invalid_schema_version")
    if doc.get("container_route") != "character":
        errors.append("unexpected_container_route")
    support = doc.get("anchor_support")
    if not isinstance(support, dict) or not support:
        errors.append("missing_anchor_support")
    else:
        for k, v in support.items():
            try:
                if int(k) < 0 or int(v) < 0:
                    errors.append("invalid_anchor_support")
            except Exception:
                errors.append("invalid_anchor_support")
    transitions = doc.get("transitions")
    if not isinstance(transitions, list) or not transitions:
        errors.append("missing_transitions")
    else:
        ids: set[str] = set()
        for i, row in enumerate(transitions):
            p = f"transition_{i}"
            if not isinstance(row, dict):
                errors.append(f"{p}_malformed")
                continue
            tid = str(row.get("boundary_id", ""))
            if not tid or tid in ids:
                errors.append(f"{p}_missing_or_duplicate_id")
            ids.add(tid)
            for key in ("from_delta_qwords", "to_delta_qwords", "clip_gap_qwords", "csmc_gap_qwords"):
                try:
                    if int(row[key]) < 0:
                        errors.append(f"{p}_negative_{key}")
                except Exception:
                    errors.append(f"{p}_malformed_{key}")
            try:
                int(row["net_relative_size_change_bytes"])
            except Exception:
                errors.append(f"{p}_malformed_net_relative_size_change_bytes")
            _require_bool(row, "complete_cross_serialization_extinction", errors, p)
            if row.get("structural_class") not in ALLOWED_CLASSES:
                errors.append(f"{p}_invalid_structural_class")
    guardrails = doc.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append("missing_guardrails")
    else:
        for key in (
            "semantic_owner_confirmed",
            "geometry_confirmed",
            "index_confirmed",
            "codec_confirmed",
            "runtime_executed",
            "blender_import_confirmed",
        ):
            if guardrails.get(key) is not False:
                errors.append(f"guardrail_{key}_must_be_false")
    return sorted(set(errors))


def analyze(doc: dict) -> dict:
    errors = validate(doc)
    if errors:
        return {"schema_version": "csmc_p4_transition_graph_result_v1", "valid": False, "errors": errors}

    support = {int(k): int(v) for k, v in doc["anchor_support"].items()}
    transitions = doc["transitions"]
    edge_by_pair: dict[tuple[int, int], list[dict]] = defaultdict(list)
    nodes: set[int] = set()
    for row in transitions:
        a = int(row["from_delta_qwords"])
        b = int(row["to_delta_qwords"])
        nodes.update((a, b))
        edge_by_pair[(a, b)].append(row)

    reversible_pairs = []
    seen_pairs: set[frozenset[int]] = set()
    for (a, b), forward in sorted(edge_by_pair.items()):
        if a == b or (b, a) not in edge_by_pair:
            continue
        key = frozenset((a, b))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        reverse = edge_by_pair[(b, a)]
        sa, sb = support.get(a), support.get(b)
        support_known = sa is not None and sb is not None and max(sa, sb) > 0
        if support_known:
            dominant = a if sa >= sb else b
            sparse = b if dominant == a else a
            ratio = support[sparse] / support[dominant]
        else:
            dominant = None
            sparse = None
            ratio = None
        net_bytes = int(forward[0]["net_relative_size_change_bytes"]) + int(reverse[0]["net_relative_size_change_bytes"])
        sparse_excursion = (
            support_known
            and ratio is not None
            and ratio <= 0.10
            and net_bytes == 0
            and not forward[0]["complete_cross_serialization_extinction"]
            and not reverse[0]["complete_cross_serialization_extinction"]
        )
        reversible_pairs.append({
            "deltas_qwords": sorted((a, b)),
            "dominant_delta_qwords": dominant,
            "sparse_delta_qwords": sparse,
            "sparse_to_dominant_anchor_support_ratio": ratio,
            "round_trip_net_relative_size_change_bytes": net_bytes,
            "classification": "SPARSE_REVERSIBLE_EXCURSION_INSIDE_BASE_REGIME" if sparse_excursion else "REVERSIBLE_PAIR_UNRESOLVED",
            "owner_implication": "DELTA_CHANGE_NOT_SUFFICIENT_FOR_OWNER_CHANGE" if sparse_excursion else "OWNER_SCOPE_UNRESOLVED",
        })

    class_counts = Counter(str(x["structural_class"]) for x in transitions)
    local_edges = [x for x in transitions if x["structural_class"] == "LOCAL_LENGTH_CHANGING_CHILD_CANDIDATE"]
    section_edges = [x for x in transitions if x["structural_class"] == "SECTION_REPACK_OR_REORDER_CANDIDATE"]
    sparse_roundtrips = [x for x in reversible_pairs if x["classification"] == "SPARSE_REVERSIBLE_EXCURSION_INSIDE_BASE_REGIME"]

    owner_rules = [
        "A displacement/delta change alone must not be interpreted as an owner change.",
        "A reversible sparse excursion with zero round-trip displacement change is compatible with continuity inside a broader regime.",
        "Complete extinction + tight local gap conservation + reused endpoints strengthens a local-child interpretation, but does not name the owner.",
        "Large asymmetric gaps with retained reuse remain section-repack/reorder candidates and do not prove owner continuity.",
    ]

    preferred = None
    if local_edges:
        preferred = sorted(
            local_edges,
            key=lambda x: (
                not bool(x.get("complete_cross_serialization_extinction")),
                abs(int(x["net_relative_size_change_bytes"])),
                str(x["boundary_id"]),
            ),
        )[0]["boundary_id"]

    return {
        "schema_version": "csmc_p4_transition_graph_result_v1",
        "valid": True,
        "container_route": doc["container_route"],
        "node_deltas_qwords": sorted(nodes),
        "anchor_support": {str(k): support[k] for k in sorted(support)},
        "transition_count": len(transitions),
        "class_counts": dict(sorted(class_counts.items())),
        "reversible_pairs": reversible_pairs,
        "sparse_roundtrip_count": len(sparse_roundtrips),
        "local_child_candidate_count": len(local_edges),
        "section_repack_candidate_count": len(section_edges),
        "preferred_consumer_landmark": preferred,
        "owner_scope_rules": owner_rules,
        "new_information": {
            "delta_change_alone_can_signal_owner_change": False if sparse_roundtrips else None,
            "base_regime_continuity_example": sparse_roundtrips[0] if sparse_roundtrips else None,
        },
        "semantic_owner": "UNRESOLVED",
        "semantic_promotions": 0,
        "runtime_executed": False,
    }


def fixture() -> dict:
    return {
        "schema_version": SCHEMA,
        "container_route": "character",
        "anchor_support": {"194": 6, "195": 187, "197": 685},
        "transitions": [
            {"boundary_id": "BND_197_TO_195", "from_delta_qwords": 197, "to_delta_qwords": 195, "clip_gap_qwords": 380, "csmc_gap_qwords": 378, "net_relative_size_change_bytes": -16, "complete_cross_serialization_extinction": True, "structural_class": "LOCAL_LENGTH_CHANGING_CHILD_CANDIDATE"},
            {"boundary_id": "BND_195_TO_194", "from_delta_qwords": 195, "to_delta_qwords": 194, "clip_gap_qwords": 5090, "csmc_gap_qwords": 5089, "net_relative_size_change_bytes": -8, "complete_cross_serialization_extinction": False, "structural_class": "SPARSE_EXCURSION_BOUNDARY"},
            {"boundary_id": "BND_194_TO_195", "from_delta_qwords": 194, "to_delta_qwords": 195, "clip_gap_qwords": 1582, "csmc_gap_qwords": 1583, "net_relative_size_change_bytes": 8, "complete_cross_serialization_extinction": False, "structural_class": "SPARSE_EXCURSION_BOUNDARY"},
            {"boundary_id": "BND_4693615_TO_4692559", "from_delta_qwords": 4693615, "to_delta_qwords": 4692559, "clip_gap_qwords": 1325, "csmc_gap_qwords": 269, "net_relative_size_change_bytes": -8448, "complete_cross_serialization_extinction": False, "structural_class": "SECTION_REPACK_OR_REORDER_CANDIDATE"},
            {"boundary_id": "BND_4692559_TO_4697174", "from_delta_qwords": 4692559, "to_delta_qwords": 4697174, "clip_gap_qwords": 3573, "csmc_gap_qwords": 8188, "net_relative_size_change_bytes": 36920, "complete_cross_serialization_extinction": False, "structural_class": "SECTION_REPACK_OR_REORDER_CANDIDATE"},
        ],
        "guardrails": {
            "semantic_owner_confirmed": False,
            "geometry_confirmed": False,
            "index_confirmed": False,
            "codec_confirmed": False,
            "runtime_executed": False,
            "blender_import_confirmed": False,
        },
    }


def self_test() -> None:
    out = analyze(fixture())
    assert out["valid"] is True
    assert out["preferred_consumer_landmark"] == "BND_197_TO_195"
    assert out["sparse_roundtrip_count"] == 1
    pair = out["reversible_pairs"][0]
    assert pair["classification"] == "SPARSE_REVERSIBLE_EXCURSION_INSIDE_BASE_REGIME"
    assert pair["dominant_delta_qwords"] == 195
    assert pair["sparse_delta_qwords"] == 194
    assert pair["round_trip_net_relative_size_change_bytes"] == 0
    assert out["new_information"]["delta_change_alone_can_signal_owner_change"] is False

    bad = fixture()
    bad["guardrails"]["geometry_confirmed"] = True
    out2 = analyze(bad)
    assert out2["valid"] is False
    assert "guardrail_geometry_confirmed_must_be_false" in out2["errors"]

    broken = fixture()
    broken["transitions"][2]["net_relative_size_change_bytes"] = 16
    out3 = analyze(broken)
    assert out3["valid"] is True
    assert out3["sparse_roundtrip_count"] == 0
    print("SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ns = ap.parse_args()
    if ns.self_test:
        self_test(); return 0
    if ns.input is None:
        ap.error("input required unless --self-test")
    print(json.dumps(analyze(json.loads(ns.input.read_text(encoding="utf-8"))), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
