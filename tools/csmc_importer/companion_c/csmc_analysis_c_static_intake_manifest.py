#!/usr/bin/env python3
"""Validate static-only evidence intake for CSMC Analysis Companion C."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ALLOWED_CLASSES = {
    "PUBLIC_SAFE_AGGREGATE",
    "PUBLIC_SAFE_METADATA",
    "PRIVATE_AUTHORIZED_ISOLATED_REF",
    "LATENT_SCHEMA_SNAPSHOT",
}
FORBIDDEN_ACQUISITION = {
    "MODELER_ACTION",
    "RUNTIME_JOB",
    "WINDOWS_WORKER",
    "CONTROL_GATE",
    "MAINLINE_CANONICAL_MUTATION",
}


def validate(m: dict) -> dict:
    reasons: list[str] = []
    artifact_class = str(m.get("artifact_class", ""))
    acquisition_mode = str(m.get("acquisition_mode", ""))
    if artifact_class not in ALLOWED_CLASSES:
        reasons.append("artifact_class_not_allowed")
    if acquisition_mode in FORBIDDEN_ACQUISITION:
        reasons.append("forbidden_acquisition_mode")
    if not m.get("source_id"):
        reasons.append("missing_source_id")
    if not m.get("provenance_hash"):
        reasons.append("missing_provenance_hash")
    if not m.get("storage_ref"):
        reasons.append("missing_storage_ref")
    if not bool(m.get("side_lane_isolated")):
        reasons.append("not_side_lane_isolated")
    if bool(m.get("auto_semantic_promotion")):
        reasons.append("auto_semantic_promotion_forbidden")
    if bool(m.get("auto_blender_emit")):
        reasons.append("auto_blender_emit_forbidden")
    if bool(m.get("public_repo_contains_private_bytes")):
        reasons.append("private_bytes_in_public_repo_forbidden")
    accepted = not reasons
    return {
        "schema_version": "csmc_analysis_c_static_intake_manifest_v1",
        "source_id": m.get("source_id"),
        "accepted": accepted,
        "intake_state": "ACCEPTED_STATIC_INPUT" if accepted else "REJECTED",
        "reasons": reasons,
        "semantic_promotion_allowed_by_intake": False,
        "blender_emit_allowed_by_intake": False,
        "runtime_dispatch_requested": False,
    }


def self_test() -> None:
    good = {
        "source_id": "S1",
        "artifact_class": "PRIVATE_AUTHORIZED_ISOLATED_REF",
        "acquisition_mode": "PREEXISTING_STATIC_REFERENCE",
        "provenance_hash": "sha256:example",
        "storage_ref": "private-ref",
        "side_lane_isolated": True,
        "auto_semantic_promotion": False,
        "auto_blender_emit": False,
        "public_repo_contains_private_bytes": False,
    }
    assert validate(good)["accepted"] is True
    bad = dict(good, acquisition_mode="RUNTIME_JOB")
    assert validate(bad)["accepted"] is False
    bad2 = dict(good, auto_semantic_promotion=True)
    assert validate(bad2)["accepted"] is False
    bad3 = dict(good, public_repo_contains_private_bytes=True)
    assert validate(bad3)["accepted"] is False
    print("SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ns = ap.parse_args()
    if ns.self_test:
        self_test()
        return 0
    if ns.input is None:
        ap.error("input is required unless --self-test is used")
    print(json.dumps(validate(json.loads(ns.input.read_text(encoding="utf-8"))), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
