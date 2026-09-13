#!/usr/bin/env python3
"""C-040: fail-closed validators for Companion C static unlock classes I1-I4."""
from __future__ import annotations
import json, re
from typing import Any

SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$")
FORBIDDEN_ACQUISITION = {
    "MODELER_ACTION", "RUNTIME_JOB", "WINDOWS_WORKER", "CONTROL_GATE",
    "MAINLINE_CANONICAL_MUTATION", "SERIALIZATION_TRIGGER",
}
FORBIDDEN_KEYS = {
    "raw_bytes", "payload_bytes", "hex", "absolute_offset",
    "file_bytes", "binary_blob", "private_payload",
}
UNLOCK_CLASSES = {
    "I1_ISOLATED_PLUS965_STATIC_REF",
    "I2_PUBLIC_SAFE_POSITIONAL_AGGREGATE",
    "I3_INTERPRETABLE_CONTROLLED_PAIR_OR_LABELED_DIFFERENTIAL",
    "I4_CURRENT_MODEL_NODE_MAPPING_ARTIFACT",
}

def _keys(v: Any):
    if isinstance(v, dict):
        for k, x in v.items():
            yield str(k)
            yield from _keys(x)
    elif isinstance(v, list):
        for x in v:
            yield from _keys(x)

def _valid_hash(v: Any) -> bool:
    return isinstance(v, str) and bool(SHA256_RE.fullmatch(v))

def _common(m: dict) -> list[str]:
    r: list[str] = []
    if str(m.get("acquisition_mode", "")) in FORBIDDEN_ACQUISITION:
        r.append("forbidden_acquisition_mode")
    if m.get("side_lane_isolated") is not True:
        r.append("not_side_lane_isolated")
    if not _valid_hash(m.get("provenance_hash")):
        r.append("invalid_provenance_hash")
    leaked = sorted(set(_keys(m)) & FORBIDDEN_KEYS)
    if leaked:
        r.append("forbidden_raw_fields:" + ",".join(leaked))
    if m.get("auto_semantic_promotion") is not False:
        r.append("auto_semantic_promotion_must_be_false")
    if m.get("auto_blender_emit") is not False:
        r.append("auto_blender_emit_must_be_false")
    return r

def _i1(m: dict) -> list[str]:
    r = _common(m)
    for k in ("source_id", "storage_ref", "container_route", "regime_id"):
        if not m.get(k):
            r.append("missing_" + k)
    if m.get("container_route") != "character":
        r.append("wrong_container_route")
    if m.get("regime_id") != "plus965":
        r.append("wrong_regime_id")
    return r

def _i2(m: dict) -> list[str]:
    r = _common(m)
    if not m.get("corpus_id"):
        r.append("missing_corpus_id")
    if m.get("container_route") != "character":
        r.append("wrong_container_route")
    if m.get("regime_id") != "plus965":
        r.append("wrong_regime_id")
    rows = m.get("rows")
    if not isinstance(rows, list) or len(rows) != 22:
        r.append("i2_requires_22_rows")
        return r
    seen: set[int] = set()
    required = {"record_index", "supergroup_index", "slot_index",
                "length_blocks", "preserve_signature"}
    for n, row in enumerate(rows):
        if not isinstance(row, dict):
            r.append(f"row_{n}_not_object")
            continue
        missing = sorted(required - set(row))
        if missing:
            r.append(f"row_{n}_missing:" + ",".join(missing))
        idx = row.get("record_index")
        if not isinstance(idx, int) or idx in seen:
            r.append(f"row_{n}_bad_record_index")
        else:
            seen.add(idx)
        if row.get("length_blocks") not in (48, 49):
            r.append(f"row_{n}_bad_length")
        sig = row.get("preserve_signature")
        if not (isinstance(sig, str) and re.fullmatch(r"[01]{7}", sig)):
            r.append(f"row_{n}_bad_signature")
        if isinstance(idx, int) and 0 <= idx <= 19:
            if row.get("supergroup_index") != idx // 5:
                r.append(f"row_{n}_bad_supergroup")
            if row.get("slot_index") != idx % 5:
                r.append(f"row_{n}_bad_slot")
        elif idx in (20, 21):
            if row.get("supergroup_index") is not None or row.get("slot_index") is not None:
                r.append(f"row_{n}_tail_must_be_unassigned")
    if seen != set(range(22)):
        r.append("record_index_set_mismatch")
    return r

def _i3(m: dict) -> list[str]:
    r = _common(m)
    for k in ("pair_id", "artifact_a_hash", "artifact_b_hash",
              "controlled_variable", "expected_relation",
              "observed_difference_summary"):
        if not m.get(k):
            r.append("missing_" + k)
    for k in ("artifact_a_hash", "artifact_b_hash"):
        if m.get(k) and not _valid_hash(m[k]):
            r.append("invalid_" + k)
    if m.get("interpretable") is not True:
        r.append("pair_not_interpretable")
    if m.get("same_serializer_route") is not True:
        r.append("serializer_route_not_controlled")
    return r

def _i4(m: dict) -> list[str]:
    r = _common(m)
    for k in ("current_model_id", "mapping_id", "container_route"):
        if not m.get(k):
            r.append("missing_" + k)
    if m.get("container_route") != "character":
        r.append("wrong_container_route")
    rows = m.get("nodes")
    if not isinstance(rows, list) or not rows:
        r.append("missing_node_rows")
        return r
    ids: set[str] = set()
    for n, row in enumerate(rows):
        if not isinstance(row, dict):
            r.append(f"node_{n}_not_object")
            continue
        node_id = row.get("node_id")
        if not node_id:
            r.append(f"node_{n}_missing_node_id")
        elif node_id in ids:
            r.append(f"node_{n}_duplicate_node_id")
        else:
            ids.add(str(node_id))
        if "parent_id" not in row:
            r.append(f"node_{n}_missing_parent_id")
        if not row.get("source_ref"):
            r.append(f"node_{n}_missing_source_ref")
    for n, row in enumerate(rows):
        if isinstance(row, dict):
            p = row.get("parent_id")
            if p is not None and str(p) not in ids:
                r.append(f"node_{n}_unresolved_parent")
    return r

VALIDATORS = {
    "I1_ISOLATED_PLUS965_STATIC_REF": _i1,
    "I2_PUBLIC_SAFE_POSITIONAL_AGGREGATE": _i2,
    "I3_INTERPRETABLE_CONTROLLED_PAIR_OR_LABELED_DIFFERENTIAL": _i3,
    "I4_CURRENT_MODEL_NODE_MAPPING_ARTIFACT": _i4,
}

def validate_unlock(m: dict) -> dict:
    cls = m.get("unlock_class")
    reasons = ["unknown_unlock_class"] if cls not in VALIDATORS else VALIDATORS[cls](m)
    return {
        "schema_version": "csmc_analysis_c_unlock_validator_v1",
        "unlock_class": cls,
        "accepted": not reasons,
        "intake_state": "ACCEPTED_STATIC_UNLOCK" if not reasons else "REJECTED",
        "reasons": reasons,
        "semantic_promotion_allowed_by_intake": False,
        "blender_emit_allowed_by_intake": False,
        "runtime_dispatch_requested": False,
    }

def self_test() -> None:
    h = "a" * 64
    base = dict(
        provenance_hash=h, side_lane_isolated=True,
        acquisition_mode="PREEXISTING_STATIC_REFERENCE",
        auto_semantic_promotion=False, auto_blender_emit=False,
    )
    i1 = dict(base, unlock_class="I1_ISOLATED_PLUS965_STATIC_REF",
              source_id="S", storage_ref="private-ref",
              container_route="character", regime_id="plus965")
    rows = [
        dict(record_index=i,
             supergroup_index=(i // 5 if i < 20 else None),
             slot_index=(i % 5 if i < 20 else None),
             length_blocks=(48 if i % 2 == 0 else 49),
             preserve_signature="0000110")
        for i in range(22)
    ]
    i2 = dict(base, unlock_class="I2_PUBLIC_SAFE_POSITIONAL_AGGREGATE",
              corpus_id="C", container_route="character",
              regime_id="plus965", rows=rows)
    i3 = dict(base,
              unlock_class="I3_INTERPRETABLE_CONTROLLED_PAIR_OR_LABELED_DIFFERENTIAL",
              pair_id="P", artifact_a_hash=h, artifact_b_hash="b" * 64,
              controlled_variable="known_edit",
              expected_relation="single controlled change",
              observed_difference_summary="bounded static diff",
              interpretable=True, same_serializer_route=True)
    i4 = dict(base, unlock_class="I4_CURRENT_MODEL_NODE_MAPPING_ARTIFACT",
              current_model_id="M", mapping_id="MAP", container_route="character",
              nodes=[{"node_id":"root","parent_id":None,"source_ref":"r0"},
                     {"node_id":"child","parent_id":"root","source_ref":"r1"}])
    checks = [
        validate_unlock(i1)["accepted"],
        validate_unlock(i2)["accepted"],
        validate_unlock(i3)["accepted"],
        validate_unlock(i4)["accepted"],
        not validate_unlock(dict(i1, acquisition_mode="RUNTIME_JOB"))["accepted"],
        not validate_unlock(dict(i1, payload_bytes="xx"))["accepted"],
        not validate_unlock(dict(i1, provenance_hash="bad"))["accepted"],
        not validate_unlock(dict(i2, rows=rows[:-1]))["accepted"],
        not validate_unlock(dict(i3, interpretable=False))["accepted"],
        not validate_unlock(dict(i4, nodes=[
            {"node_id":"child","parent_id":"missing","source_ref":"r"}]))["accepted"],
    ]
    assert all(checks), checks
    print("SELF_TEST_PASS 10/10")

if __name__ == "__main__":
    self_test()
