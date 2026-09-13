#!/usr/bin/env python3
"""Fail-closed public-safe intake contract for one bounded CSMC transition trace.

This module validates metadata only. It never dispatches MODELER/runtime actions and
never accepts raw memory bytes or broad-scan output as public evidence.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

SCHEMA = "csmc_p4_transition_event_evidence_v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_EVENT_KINDS = {"CALLSITE", "LENGTH_UPDATE", "BUFFER_WRITE", "RETURN", "ALLOCATION"}


def validate(doc: dict) -> list[str]:
    e: list[str] = []
    if doc.get("schema_version") != SCHEMA:
        e.append("invalid_schema_version")
    if doc.get("experiment_id") != "SERIALIZATION_TRIGGER_NO_CHANGE_SAVE_001":
        e.append("unexpected_experiment_id")
    if doc.get("boundary_id") != "BND_197_TO_195":
        e.append("unexpected_boundary_id")
    if doc.get("transition_class") != "LOCAL_LENGTH_CHANGING_CHILD_CANDIDATE":
        e.append("unexpected_transition_class")
    if doc.get("container_route") != "character":
        e.append("unexpected_container_route")
    if doc.get("regime_before") != "+197" or doc.get("regime_after") != "+195":
        e.append("unexpected_regime_pair")
    if doc.get("net_relative_size_change_bytes") != -16:
        e.append("unexpected_net_size_change")

    provenance = doc.get("provenance")
    if not isinstance(provenance, dict):
        e.append("missing_provenance")
    else:
        for key in ("clip_sha256", "csmc_sha256", "transition_object_sha256"):
            if not SHA256_RE.fullmatch(str(provenance.get(key, ""))):
                e.append(f"invalid_{key}")

    trigger = doc.get("trigger")
    if not isinstance(trigger, dict):
        e.append("missing_trigger")
    else:
        required = {
            "kind": "NO_CHANGE_SAVE",
            "trigger_count": 1,
            "model_already_open": True,
            "model_reload_count": 0,
            "modeler_restart_count": 0,
        }
        for key, expected in required.items():
            if trigger.get(key) != expected:
                e.append(f"invalid_trigger_{key}")

    collection = doc.get("collection")
    if not isinstance(collection, dict):
        e.append("missing_collection")
    else:
        if collection.get("scope") != "BOUNDARY_TRANSITION_EVENT":
            e.append("invalid_collection_scope")
        for key in (
            "broad_memory_scan",
            "generic_guid_scan",
            "idle_partial_copy_scan",
            "raw_memory_bytes_in_public_artifact",
            "arbitrary_address_sweep",
        ):
            if collection.get(key) is not False:
                e.append(f"collection_{key}_must_be_false")
        if collection.get("diagnostic_count") != 1:
            e.append("diagnostic_count_must_equal_one")

    events = doc.get("events")
    if not isinstance(events, list):
        e.append("events_must_be_list")
    else:
        seen = set()
        for row in events:
            if not isinstance(row, dict):
                e.append("malformed_event")
                continue
            event_id = str(row.get("event_id", ""))
            if not event_id or event_id in seen:
                e.append("missing_or_duplicate_event_id")
            seen.add(event_id)
            if row.get("kind") not in ALLOWED_EVENT_KINDS:
                e.append("invalid_event_kind")
            if not row.get("module") or not isinstance(row.get("module"), str):
                e.append("missing_event_module")
            try:
                if int(row.get("rva")) < 0:
                    e.append("negative_event_rva")
            except Exception:
                e.append("malformed_event_rva")
            try:
                if float(row.get("after_trigger_ms")) < 0:
                    e.append("negative_after_trigger_ms")
            except Exception:
                e.append("malformed_after_trigger_ms")
            if "absolute_address" in row or "raw_bytes" in row or "memory_dump" in row:
                e.append("forbidden_event_payload_field")

    claims = doc.get("claims")
    if not isinstance(claims, dict):
        e.append("missing_claims")
    else:
        for key in (
            "consumer_confirmed",
            "semantic_owner_confirmed",
            "codec_confirmed",
            "geometry_confirmed",
            "index_confirmed",
            "blender_import_confirmed",
        ):
            if claims.get(key) is not False:
                e.append(f"claim_{key}_must_be_false")

    return sorted(set(e))


def analyze(doc: dict) -> dict:
    errors = validate(doc)
    if errors:
        return {"schema_version": "csmc_p4_transition_event_evidence_result_v1", "valid": False, "errors": errors}
    events = doc["events"]
    threads = sorted({str(x.get("thread_id")) for x in events if x.get("thread_id") is not None})
    return {
        "schema_version": "csmc_p4_transition_event_evidence_result_v1",
        "valid": True,
        "intake_state": "BOUNDARY_TRANSITION_EVENT_EVIDENCE_ACCEPTED",
        "event_count": len(events),
        "thread_count": len(threads),
        "consumer_confirmation_ready": False,
        "semantic_promotions": 0,
        "runtime_dispatched_by_validator": False,
        "next_analysis": (
            "If future accepted events exist, correlate repeated module+RVA/causal order only within the one-shot save interval; "
            "do not widen to broad scans."
        ),
    }


def _fixture() -> dict:
    return {
        "schema_version": SCHEMA,
        "experiment_id": "SERIALIZATION_TRIGGER_NO_CHANGE_SAVE_001",
        "boundary_id": "BND_197_TO_195",
        "transition_class": "LOCAL_LENGTH_CHANGING_CHILD_CANDIDATE",
        "container_route": "character",
        "regime_before": "+197",
        "regime_after": "+195",
        "net_relative_size_change_bytes": -16,
        "provenance": {
            "clip_sha256": "e" * 64,
            "csmc_sha256": "3" * 64,
            "transition_object_sha256": "a" * 64,
        },
        "trigger": {
            "kind": "NO_CHANGE_SAVE",
            "trigger_count": 1,
            "model_already_open": True,
            "model_reload_count": 0,
            "modeler_restart_count": 0,
        },
        "collection": {
            "scope": "BOUNDARY_TRANSITION_EVENT",
            "diagnostic_count": 1,
            "broad_memory_scan": False,
            "generic_guid_scan": False,
            "idle_partial_copy_scan": False,
            "raw_memory_bytes_in_public_artifact": False,
            "arbitrary_address_sweep": False,
        },
        "events": [
            {"event_id": "E1", "kind": "CALLSITE", "module": "synthetic.dll", "rva": 4096, "thread_id": "T1", "after_trigger_ms": 4.5},
            {"event_id": "E2", "kind": "LENGTH_UPDATE", "module": "synthetic.dll", "rva": 4112, "thread_id": "T1", "after_trigger_ms": 5.0},
        ],
        "claims": {
            "consumer_confirmed": False,
            "semantic_owner_confirmed": False,
            "codec_confirmed": False,
            "geometry_confirmed": False,
            "index_confirmed": False,
            "blender_import_confirmed": False,
        },
    }


def self_test() -> None:
    good = _fixture()
    assert analyze(good)["valid"] is True

    broad = json.loads(json.dumps(good))
    broad["collection"]["broad_memory_scan"] = True
    assert "collection_broad_memory_scan_must_be_false" in analyze(broad)["errors"]

    twice = json.loads(json.dumps(good))
    twice["trigger"]["trigger_count"] = 2
    assert "invalid_trigger_trigger_count" in analyze(twice)["errors"]

    leaked = json.loads(json.dumps(good))
    leaked["events"][0]["raw_bytes"] = "00ff"
    assert "forbidden_event_payload_field" in analyze(leaked)["errors"]

    promoted = json.loads(json.dumps(good))
    promoted["claims"]["consumer_confirmed"] = True
    assert "claim_consumer_confirmed_must_be_false" in analyze(promoted)["errors"]
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
