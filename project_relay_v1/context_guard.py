#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Dict, Iterable

from memory_context_loader import classify_task, select_context

VERSION = "context-guard-v1"
DETERMINISTIC_CONFIDENCE_MIN = 0.60


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
    old_domains = set(old["domains"])
    new_domains = set(new["domains"])
    if old_domains != new_domains:
        # Domain drift can mean the user narrowed or changed the task. Rebuild rather than silently carry old docs.
        return {"rebuild": True, "reason": "domains-changed", "old": old, "new": new}
    return {"rebuild": False, "reason": "context-compatible", "old": old, "new": new}


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
        # Ambiguous input may still load ALWAYS/global memory, but it must not auto-execute a task-specific runner.
        context["execution_gate"] = "WAITING_BRAIN_CLASSIFICATION"
    else:
        context["execution_gate"] = "READY"
    context["route_mode"] = route["route_mode"]
    context["fallback_brain"] = route["fallback_brain"]
    context["guard_version"] = VERSION
    return context
