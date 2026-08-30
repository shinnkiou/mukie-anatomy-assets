import json
from pathlib import Path

from context_guard import build_guarded_context, requires_context_rebuild, routing_decision
from memory_context_loader import select_context

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT / "testdata" / "memory_catalog_fixture.json").read_text(encoding="utf-8"))


def test_ambiguous_instruction_does_not_auto_execute():
    instruction = "いい感じにやっておいて"
    route = routing_decision(instruction)
    assert route["route_mode"] == "BRAIN_FALLBACK", route
    assert route["fallback_brain"] == "BASE44_SUPER_AGENT", route
    context = build_guarded_context(instruction, CATALOG)
    assert context["execution_gate"] == "WAITING_BRAIN_CLASSIFICATION", context
    # Only ALWAYS/global memory may survive an ambiguous task. Task-specific rules must not leak in.
    assert context["selected_memory_keys"] == ["global-project-relay-principles-v1"], context


def test_task_change_forces_context_rebuild():
    old = select_context(
        "サブカルキャラTの歴史についてまとめる",
        CATALOG,
        mission_key="subculture_character_t_history_20260830",
    )
    new = select_context(
        "Blenderでバーの3Dモデルを作る",
        CATALOG,
        mission_key="bar3d_sandbox",
    )
    decision = requires_context_rebuild(old, new)
    assert decision["rebuild"] is True, decision
    assert decision["reason"] in {"mission-changed", "task-kind-changed", "domains-changed"}, decision


def test_same_task_can_reuse_context_identity():
    a = select_context(
        "サブカルキャラTの歴史についてまとめる",
        CATALOG,
        mission_key="subculture_character_t_history_20260830",
    )
    b = select_context(
        "サブカルキャラTの歴史についてまとめる",
        CATALOG,
        mission_key="subculture_character_t_history_20260830",
    )
    decision = requires_context_rebuild(a, b)
    assert decision["rebuild"] is False, decision
    assert decision["reason"] == "context-compatible", decision


def main():
    test_ambiguous_instruction_does_not_auto_execute()
    test_task_change_forces_context_rebuild()
    test_same_task_can_reuse_context_identity()
    print("PROJECT RELAY CONTEXT GUARD TESTS PASS")


if __name__ == "__main__":
    main()
