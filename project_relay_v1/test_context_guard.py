import json
from pathlib import Path

from context_guard import build_guarded_context, requires_context_rebuild, routing_decision, validate_context_packet
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


def context_load_fixture():
    return {
        "context_load_key": "ctx-1",
        "project_key": "project_relay",
        "mission_key": "subculture_character_t_history_20260830",
        "task_kind": "HISTORICAL_RESEARCH",
        "selected_memory_keys": "global-project-relay-principles-v1,task-research-summary-rules-v1,mission-subculture-character-t-history-brief-v1",
        "selected_doc_count": 3,
    }


def packet_fixture():
    return {
        "packet_key": "packet-1",
        "context_load_key": "ctx-1",
        "project_key": "project_relay",
        "mission_key": "subculture_character_t_history_20260830",
        "task_kind": "HISTORICAL_RESEARCH",
        "status": "FRESH",
        "doc_count": 3,
        "source_docs_json": json.dumps([
            {"memory_key": "global-project-relay-principles-v1", "drive_file_id": "g", "revision_id": "g1"},
            {"memory_key": "task-research-summary-rules-v1", "drive_file_id": "r", "revision_id": "r1"},
            {"memory_key": "mission-subculture-character-t-history-brief-v1", "drive_file_id": "m", "revision_id": "m1"},
        ]),
    }


def test_context_packet_gate():
    context = context_load_fixture()

    missing = validate_context_packet(None, context)
    assert missing["valid"] is False and missing["reason"] == "packet-missing", missing

    stale_packet = packet_fixture()
    stale_packet["status"] = "STALE"
    stale = validate_context_packet(stale_packet, context)
    assert stale["valid"] is False and stale["reason"] == "packet-stale", stale

    wrong_task = packet_fixture()
    wrong_task["task_kind"] = "BLENDER_3D"
    mismatch = validate_context_packet(wrong_task, context)
    assert mismatch["valid"] is False and mismatch["reason"] == "task_kind-mismatch", mismatch

    missing_source = packet_fixture()
    sources = json.loads(missing_source["source_docs_json"])
    missing_source["source_docs_json"] = json.dumps(sources[:-1])
    missing_source["doc_count"] = 2
    missing_result = validate_context_packet(missing_source, context)
    assert missing_result["valid"] is False and missing_result["reason"] == "selected-source-missing", missing_result

    changed = validate_context_packet(packet_fixture(), context, current_revisions={"g": "g2", "r": "r1", "m": "m1"})
    assert changed["valid"] is False and changed["reason"] == "source-revision-changed", changed

    fresh = validate_context_packet(packet_fixture(), context, current_revisions={"g": "g1", "r": "r1", "m": "m1"})
    assert fresh["valid"] is True and fresh["execution_gate"] == "READY", fresh


def main():
    test_ambiguous_instruction_does_not_auto_execute()
    test_task_change_forces_context_rebuild()
    test_same_task_can_reuse_context_identity()
    test_context_packet_gate()
    print("PROJECT RELAY CONTEXT GUARD TESTS PASS")


if __name__ == "__main__":
    main()
