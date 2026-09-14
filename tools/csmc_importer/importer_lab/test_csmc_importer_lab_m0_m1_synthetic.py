#!/usr/bin/env python3
from __future__ import annotations
import copy
from csmc_importer_lab_manifest import HypothesisManifest, ManifestError, validate_child_mutation
from csmc_importer_lab_runner import run_batch, RunnerError


def base(hid="H1", offset=0, stride=2, relationship="COUNT_EQUALS_LABEL", semantic="GEOMETRY_OR_TOPOLOGY_TARGET"):
    return {
        "hypothesis_id": hid,
        "generation": 0,
        "engine_mode": "SYNTHETIC_ONLY",
        "region_class": "SYNTHETIC_REGION",
        "region_id": "A",
        "anchor_id": "SYNTH_START",
        "relative_offset": offset,
        "count_source": "REGION_LENGTH",
        "count_type": "u32",
        "endianness": "be",
        "element_type": "u16",
        "stride": stride,
        "components": 1,
        "grouping": "SCALAR",
        "relationship": relationship,
        "candidate_semantic": semantic,
        "preprocess": "NONE",
        "parent_hypothesis_id": None,
        "preregistered_prediction": "count equals target",
        "negative_control_set": ["N1"],
        "semantic_promotion": False,
        "diagnostic_only": True,
        "blender_emit": False,
        "synthetic_fault": None,
    }


def fixtures():
    return [
        {"fixture_id": "T1", "split": "TRAIN", "regions": {"A": "000100020003"}, "labels": {"target": 3}},
        {"fixture_id": "T2", "split": "TRAIN", "regions": {"A": "0001000200030004"}, "labels": {"target": 4}},
        {"fixture_id": "V1", "split": "VALIDATION", "regions": {"A": "00010002"}, "labels": {"target": 2}},
        {"fixture_id": "N1", "split": "NEGATIVE", "regions": {"A": "000100020003"}, "labels": {"target": 7}},
        {"fixture_id": "HOLD", "split": "HOLDOUT", "regions": {"A": "00010002000300040005"}, "labels": {"target": 5}},
    ]


def main():
    manifest = HypothesisManifest.from_mapping(base())
    assert manifest.semantic_promotion is False and manifest.blender_emit is False

    bad = base()
    bad["semantic_promotion"] = True
    try:
        HypothesisManifest.from_mapping(bad)
        raise AssertionError("promotion accepted")
    except ManifestError:
        pass

    bad = base()
    bad["best_offset_per_fixture"] = {"T1": 1}
    try:
        HypothesisManifest.from_mapping(bad)
        raise AssertionError("forbidden key accepted")
    except ManifestError:
        pass

    child = base("H2")
    child["generation"] = 1
    child["parent_hypothesis_id"] = "H1"
    child["stride"] = 4
    child_manifest = HypothesisManifest.from_mapping(child)
    assert validate_child_mutation(manifest, child_manifest) == ["stride"]

    child2 = copy.deepcopy(child)
    child2["hypothesis_id"] = "H3"
    child2["endianness"] = "le"
    try:
        validate_child_mutation(manifest, HypothesisManifest.from_mapping(child2))
        raise AssertionError("multi-locus accepted")
    except ManifestError:
        pass

    rows = [base("GOOD"), base("GOOD_DUP")]
    rows.append(base("DECOY", relationship="NULL_DECOY", semantic="NULL_DECOY"))
    out = run_batch(rows, fixtures(), concurrency=2, timeout_seconds=10.0)
    assert out["candidate_count_input"] == 3 and out["candidate_count_unique"] == 2
    assert len(out["duplicates"]) == 1
    good = next(row for row in out["results"] if row["hypothesis_id"] == "GOOD")
    assert good["status"] == "EVALUATED" and good["score"] > 90
    assert all(row["fixture_id"] != "HOLD" for row in good["fixture_results"])
    assert out["holdout_used_for_selection"] is False

    out2 = run_batch(list(reversed(rows)), fixtures(), concurrency=1, timeout_seconds=10.0)
    assert [
        (row["canonical_key"], row["score"], row["status"]) for row in out["results"]
    ] == [
        (row["canonical_key"], row["score"], row["status"]) for row in out2["results"]
    ]

    crash = base("CRASH")
    crash["synthetic_fault"] = "CRASH"
    ok = base("OK2")
    ok["relative_offset"] = 2
    isolated = run_batch([crash, ok], fixtures(), concurrency=2, timeout_seconds=10.0)
    assert any(row["status"] == "CRASH_ISOLATED" for row in isolated["results"])
    assert any(row["status"] == "EVALUATED" for row in isolated["results"])

    slow = base("SLOW")
    slow["synthetic_fault"] = "SLEEP:2.0"
    timed = run_batch([slow], fixtures(), concurrency=1, timeout_seconds=1.0)
    assert timed["results"][0]["status"] == "TIMEOUT_ISOLATED"

    too_many = []
    for i in range(51):
        row = base(f"X{i}")
        row["relative_offset"] = i % 2
        too_many.append(row)
    try:
        run_batch(too_many, fixtures())
        raise AssertionError("batch > 50 accepted")
    except RunnerError:
        pass

    print("PASS csmc importer lab M0/M1 synthetic acceptance")


if __name__ == "__main__":
    main()
