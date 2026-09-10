"""Deterministic cloud recovery/state reconciliation for UKIE AI BRIDGE.

This reducer converts repeated Drive discovery observations and optional verified
cloud-intake evidence into a stable state. It performs no I/O, no Base44 writes,
no Drive writes, and no release promotion. The control plane can safely upsert the
returned record by recovery_key.

Key safety rules:
- incomplete sync waits rather than fails;
- duplicate/ambiguous triplets block automatic intake;
- repeated identical observations are idempotent;
- once DRIVE_VERIFIED, a changed Drive file-id triplet or content SHA is treated
  as evidence replacement and blocks automatic reuse;
- READY_FOR_AI and release promotion are never asserted here.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


SCHEMA = "ukie_cloud_recovery_v1"
FINAL_VERIFIED = "DRIVE_VERIFIED"
BLOCKED = "BLOCKED"
WAITING = "WAITING_FOR_SYNC"
INCOMPLETE = "INCOMPLETE"
COMPLETE = "COMPLETE"
READBACK_VERIFYING = "READBACK_VERIFYING"
ALLOWED = {WAITING, INCOMPLETE, COMPLETE, READBACK_VERIFYING, FINAL_VERIFIED, BLOCKED}


class CloudRecoveryError(ValueError):
    pass


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def recovery_key(base_name: str) -> str:
    if not isinstance(base_name, str) or not base_name.startswith("UKIE_PHYSICAL_ACCEPTANCE__") or not base_name.endswith(".zip"):
        raise CloudRecoveryError("invalid acceptance base_name")
    return "CLOUD_RECOVERY_" + hashlib.sha256(base_name.encode("utf-8")).hexdigest()[:24].upper()


def _triplet_identity(row: dict[str, Any]) -> dict[str, Any]:
    triplet = row.get("triplet") if isinstance(row.get("triplet"), dict) else {}
    values: dict[str, dict[str, Any]] = {}
    for kind in ("zip", "sha256", "handoff"):
        item = triplet.get(kind) if isinstance(triplet.get(kind), dict) else {}
        file_id = item.get("file_id")
        name = item.get("name")
        if not isinstance(file_id, str) or not file_id or not isinstance(name, str) or not name:
            raise CloudRecoveryError(f"complete discovery row is missing {kind} identity")
        values[kind] = {
            "file_id": file_id,
            "name": name,
            "size": item.get("size") if isinstance(item.get("size"), int) else None,
        }
    return {
        "files": values,
        "fingerprint": _canonical_sha(values),
    }


def _find_row(discovery: dict[str, Any], base_name: str) -> tuple[str, dict[str, Any] | None]:
    if not isinstance(discovery, dict):
        raise CloudRecoveryError("discovery must be an object")
    if discovery.get("schema_version") != "ukie_cloud_discovery_v1":
        raise CloudRecoveryError("unsupported discovery schema")
    for category, status in (("ambiguous", "AMBIGUOUS"), ("complete", "COMPLETE"), ("incomplete", "INCOMPLETE")):
        rows = discovery.get(category)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict) and row.get("base_name") == base_name:
                return status, row
    return "ABSENT", None


def _base_state(base_name: str, previous: dict[str, Any] | None) -> dict[str, Any]:
    key = recovery_key(base_name)
    if previous is None:
        return {
            "schema_version": SCHEMA,
            "recovery_key": key,
            "base_name": base_name,
            "revision": 0,
            "status": WAITING,
            "triplet": None,
            "verified_sha256": None,
            "verified_provider_file_ids": None,
            "acceptance_id": None,
            "release_key": None,
            "bridge_version": None,
            "physical_provenance": False,
            "ready_for_ai": False,
            "promotion_performed": False,
            "blocked_reason": None,
            "next_action": "WAIT_FOR_SYNC",
        }
    if not isinstance(previous, dict) or previous.get("schema_version") != SCHEMA:
        raise CloudRecoveryError("previous recovery state uses an unsupported schema")
    if previous.get("recovery_key") != key or previous.get("base_name") != base_name:
        raise CloudRecoveryError("previous recovery state identity mismatch")
    if previous.get("status") not in ALLOWED:
        raise CloudRecoveryError("previous recovery status is invalid")
    state = dict(previous)
    state["ready_for_ai"] = False
    state["promotion_performed"] = False
    return state


def _state_signature(state: dict[str, Any]) -> str:
    material = {k: v for k, v in state.items() if k not in {"revision", "last_transition", "idempotent_replay"}}
    return _canonical_sha(material)


def _finish(previous_state: dict[str, Any], candidate: dict[str, Any], transition: str) -> dict[str, Any]:
    candidate["schema_version"] = SCHEMA
    candidate["ready_for_ai"] = False
    candidate["promotion_performed"] = False
    same = _state_signature(previous_state) == _state_signature(candidate)
    if same:
        candidate["revision"] = int(previous_state.get("revision") or 0)
        candidate["idempotent_replay"] = True
        candidate["last_transition"] = "NO_CHANGE"
    else:
        candidate["revision"] = int(previous_state.get("revision") or 0) + 1
        candidate["idempotent_replay"] = False
        candidate["last_transition"] = transition
    return candidate


def reconcile_candidate(
    base_name: str,
    discovery: dict[str, Any],
    previous: dict[str, Any] | None = None,
    intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Reconcile one acceptance basename to a deterministic non-promoting state."""
    state = _base_state(base_name, previous)
    observed_status, row = _find_row(discovery, base_name)

    # Verified evidence is sticky. If it disappears temporarily, retain proof and
    # wait for a later scan rather than erasing previously verified provenance.
    if observed_status == "ABSENT":
        if state.get("status") == FINAL_VERIFIED:
            candidate = dict(state)
            candidate["next_action"] = "KEEP_VERIFIED_WAIT_FOR_REAPPEARANCE"
            candidate["blocked_reason"] = None
            return _finish(state, candidate, "VERIFIED_EVIDENCE_TEMPORARILY_ABSENT")
        candidate = dict(state)
        candidate.update({
            "status": WAITING,
            "triplet": None if state.get("status") != FINAL_VERIFIED else state.get("triplet"),
            "blocked_reason": None,
            "next_action": "WAIT_FOR_SYNC",
        })
        return _finish(state, candidate, "WAIT_FOR_SYNC")

    if observed_status == "AMBIGUOUS":
        candidate = dict(state)
        candidate.update({
            "status": BLOCKED,
            "blocked_reason": "AMBIGUOUS_DUPLICATE_FILES",
            "next_action": "REQUIRE_HUMAN_DUPLICATE_RESOLUTION",
            "observed_counts": row.get("counts") if row else None,
        })
        return _finish(state, candidate, "BLOCK_AMBIGUOUS")

    if observed_status == "INCOMPLETE":
        # Do not downgrade immutable verified proof due to transient sync ordering.
        if state.get("status") == FINAL_VERIFIED:
            candidate = dict(state)
            candidate["next_action"] = "KEEP_VERIFIED_WAIT_FOR_TRIPLET_REAPPEARANCE"
            candidate["blocked_reason"] = None
            return _finish(state, candidate, "VERIFIED_TRIPLET_TEMPORARILY_INCOMPLETE")
        candidate = dict(state)
        candidate.update({
            "status": INCOMPLETE,
            "triplet": None,
            "missing": list(row.get("missing") or []) if row else [],
            "blocked_reason": None,
            "next_action": "WAIT_FOR_MISSING_FILES",
        })
        return _finish(state, candidate, "SYNC_INCOMPLETE")

    if observed_status != "COMPLETE" or row is None:
        raise CloudRecoveryError("unhandled discovery classification")

    observed_triplet = _triplet_identity(row)
    prior_triplet = state.get("triplet") if isinstance(state.get("triplet"), dict) else None
    if state.get("status") == FINAL_VERIFIED and prior_triplet:
        if prior_triplet.get("fingerprint") != observed_triplet.get("fingerprint"):
            candidate = dict(state)
            candidate.update({
                "status": BLOCKED,
                "blocked_reason": "VERIFIED_EVIDENCE_FILE_IDS_CHANGED",
                "next_action": "REQUIRE_HUMAN_EVIDENCE_REPLACEMENT_REVIEW",
                "replacement_triplet": observed_triplet,
            })
            return _finish(state, candidate, "BLOCK_VERIFIED_FILE_ID_CHANGE")

    if intake is None:
        candidate = dict(state)
        candidate.update({
            "status": COMPLETE,
            "triplet": observed_triplet,
            "blocked_reason": None,
            "next_action": "FETCH_THREE_FILES_AND_VERIFY_READBACK",
        })
        return _finish(state, candidate, "TRIPLET_COMPLETE")

    if not isinstance(intake, dict) or intake.get("schema_version") != "ukie_cloud_intake_v1":
        raise CloudRecoveryError("intake uses an unsupported schema")
    if intake.get("file_name") != base_name:
        raise CloudRecoveryError("intake file_name does not match recovery candidate")
    if intake.get("status") != "DRIVE_READBACK_VERIFIED":
        candidate = dict(state)
        candidate.update({
            "status": READBACK_VERIFYING,
            "triplet": observed_triplet,
            "blocked_reason": None,
            "next_action": "WAIT_FOR_PROVIDER_READBACK_VERIFICATION",
        })
        return _finish(state, candidate, "READBACK_PENDING")
    if intake.get("drive_readback_proven") is not True or intake.get("cloud_presence_proven") is not True:
        raise CloudRecoveryError("DRIVE_READBACK_VERIFIED intake lacks provider proof")
    if intake.get("triplet_verified") is not True:
        raise CloudRecoveryError("Drive intake does not prove triplet verification")
    if intake.get("ready_for_ai") is not False or intake.get("promotion_performed") is not False:
        raise CloudRecoveryError("cloud intake illegally claims readiness or promotion")
    if intake.get("physical_provenance") is not True:
        raise CloudRecoveryError("physical recovery cannot promote synthetic/non-physical intake to verified state")

    provider = intake.get("provider") if isinstance(intake.get("provider"), dict) else {}
    file_ids = provider.get("file_ids") if isinstance(provider.get("file_ids"), dict) else {}
    observed_ids = {kind: observed_triplet["files"][kind]["file_id"] for kind in ("zip", "sha256", "handoff")}
    if any(file_ids.get(kind) != observed_ids[kind] for kind in observed_ids):
        raise CloudRecoveryError("intake provider file IDs disagree with the discovered triplet")

    verified_sha = intake.get("sha256")
    if not isinstance(verified_sha, str) or len(verified_sha) != 64:
        raise CloudRecoveryError("verified intake SHA-256 is missing")
    previous_sha = state.get("verified_sha256")
    if state.get("status") == FINAL_VERIFIED and previous_sha and previous_sha != verified_sha:
        candidate = dict(state)
        candidate.update({
            "status": BLOCKED,
            "blocked_reason": "VERIFIED_EVIDENCE_SHA_CHANGED",
            "next_action": "REQUIRE_HUMAN_EVIDENCE_REPLACEMENT_REVIEW",
            "replacement_sha256": verified_sha,
        })
        return _finish(state, candidate, "BLOCK_VERIFIED_SHA_CHANGE")

    candidate = dict(state)
    candidate.update({
        "status": FINAL_VERIFIED,
        "triplet": observed_triplet,
        "verified_sha256": verified_sha,
        "verified_provider_file_ids": observed_ids,
        "acceptance_id": intake.get("acceptance_id"),
        "release_key": intake.get("release_key"),
        "bridge_version": intake.get("bridge_version"),
        "physical_provenance": True,
        "blocked_reason": None,
        "next_action": "REGISTER_VERIFIED_INTAKE_THEN_EVALUATE_RELEASE_GATE",
    })
    return _finish(state, candidate, "DRIVE_READBACK_VERIFIED")
