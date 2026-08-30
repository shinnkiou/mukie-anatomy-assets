#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Mapping

from memory_context_loader import RULES, classify_task, select_context

VERSION = "context-guard-v1.2"
DETERMINISTIC_CONFIDENCE_MIN = float(RULES.get("defaults", {}).get("deterministic_confidence_min", 0.60))


def routing_decision(instruction: str) -> Dict[str, Any]:
    task = classify_task(instruction)
    deterministic = task["task_kind"] != "GENERAL" and float(task.get("confidence", 0)) >= DETERMINISTIC_CONFIDENCE_MIN
    return {
        **task,
        "guard_version": VERSION,
        "route_mode": "DETERMINISTIC" if deterministic else "BRAIN_FALLBACK",
        "fallback_brain": None if deterministic else "BASE44_SUPER_AGENT",
        "reason": "classifier-confident" if deterministic else "ambiguous-or-low-confidence",
    }


def context_identity(context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "project_key": context.get("project_key", ""),
        "mission_key": context.get("mission_key", ""),
        "task_kind": context.get("task_kind", "GENERAL"),
        "domains": sorted(set(context.get("domains") or [])),
        "rules_version": context.get("rules_version", RULES["version"]),
    }


def requires_context_rebuild(previous: Dict[str, Any] | None, current: Dict[str, Any]) -> Dict[str, Any]:
    if not previous:
        return {"rebuild": True, "reason": "no-previous-context"}
    old = context_identity(previous)
    new = context_identity(current)
    if old["project_key"] != new["project_key"]:
        return {"rebuild": True, "reason": "project-changed", "old": old, "new": new}
    if old["mission_key"] != new["mission_key"]:
        return {"rebuild": True, "reason": "mission-changed", "old": old, "new": new}
    if old["task_kind"] != new["task_kind"]:
        return {"rebuild": True, "reason": "task-kind-changed", "old": old, "new": new}
    if old["rules_version"] != new["rules_version"]:
        return {"rebuild": True, "reason": "rules-version-changed", "old": old, "new": new}
    old_domains = set(old["domains"])
    new_domains = set(new["domains"])
    if old_domains != new_domains:
        return {"rebuild": True, "reason": "domains-changed", "old": old, "new": new}
    return {"rebuild": False, "reason": "context-compatible", "old": old, "new": new}


def _parse_source_docs(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [x for x in parsed if isinstance(x, dict)]
    return []


def validate_context_packet(
    packet: Dict[str, Any] | None,
    context_load: Dict[str, Any],
    *,
    current_revisions: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    """Validate a Base44 RelayContextPacket before an agent may execute."""
    if not packet:
        return {"valid": False, "execution_gate": "WAITING_SYNC", "reason": "packet-missing"}
    if packet.get("status") != "FRESH":
        return {"valid": False, "execution_gate": "WAITING_SYNC", "reason": f"packet-{str(packet.get('status', 'unknown')).lower()}"}
    if packet.get("context_load_key") != context_load.get("context_load_key"):
        return {"valid": False, "execution_gate": "WAITING_SYNC", "reason": "context-load-mismatch"}

    for field in ("project_key", "mission_key", "task_kind"):
        if str(packet.get(field, "")) != str(context_load.get(field, "")):
            return {"valid": False, "execution_gate": "WAITING_SYNC", "reason": f"{field}-mismatch"}

    expected_rules_version = str(context_load.get("rules_version") or RULES["version"])
    packet_rules_version = str(packet.get("rules_version") or "")
    if not packet_rules_version:
        return {"valid": False, "execution_gate": "WAITING_SYNC", "reason": "rules-version-missing"}
    if packet_rules_version != expected_rules_version:
        return {
            "valid": False,
            "execution_gate": "WAITING_SYNC",
            "reason": "rules-version-mismatch",
            "expected": expected_rules_version,
            "actual": packet_rules_version,
        }

    selected = [x for x in str(context_load.get("selected_memory_keys", "")).split(",") if x]
    sources = _parse_source_docs(packet.get("source_docs_json"))
    source_keys = {str(x.get("memory_key", "")) for x in sources}
    missing_sources = [key for key in selected if key not in source_keys]
    if missing_sources:
        return {
            "valid": False,
            "execution_gate": "WAITING_SYNC",
            "reason": "selected-source-missing",
            "missing_sources": missing_sources,
        }

    expected_count = int(context_load.get("selected_doc_count") or len(selected))
    packet_count = int(packet.get("doc_count") or len(sources))
    if packet_count != expected_count:
        return {
            "valid": False,
            "execution_gate": "WAITING_SYNC",
            "reason": "doc-count-mismatch",
            "expected": expected_count,
            "actual": packet_count,
        }

    stale_files: list[str] = []
    if current_revisions:
        for src in sources:
            file_id = str(src.get("drive_file_id", ""))
            packet_revision = str(src.get("revision_id", ""))
            current_revision = str(current_revisions.get(file_id, ""))
            if current_revision and packet_revision and current_revision != packet_revision:
                stale_files.append(file_id)
    if stale_files:
        return {
            "valid": False,
            "execution_gate": "WAITING_SYNC",
            "reason": "source-revision-changed",
            "stale_files": stale_files,
        }

    return {
        "valid": True,
        "execution_gate": "READY",
        "reason": "fresh-matching-packet",
        "packet_key": packet.get("packet_key", ""),
        "doc_count": packet_count,
        "rules_version": packet_rules_version,
    }


def build_guarded_context(
    instruction: str,
    catalog: Iterable[Dict[str, Any]],
    *,
    project_key: str = "project_relay",
    mission_key: str = "",
    max_docs: int = 8,
    char_budget: int = 24000,
) -> Dict[str, Any]:
    route = routing_decision(instruction)
    context = select_context(
        instruction,
        catalog,
        project_key=project_key,
        mission_key=mission_key,
        max_docs=max_docs,
        char_budget=char_budget,
    )
    if route["route_mode"] == "BRAIN_FALLBACK":
        context["execution_gate"] = "WAITING_BRAIN_CLASSIFICATION"
    else:
        context["execution_gate"] = "READY"
    context["route_mode"] = route["route_mode"]
    context["fallback_brain"] = route["fallback_brain"]
    context["guard_version"] = VERSION
    return context
