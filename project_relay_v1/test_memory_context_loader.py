import json
from pathlib import Path

from memory_context_loader import classify_task, select_context

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT / "testdata" / "memory_catalog_fixture.json").read_text(encoding="utf-8"))


def assert_contains(keys, *wanted):
    missing = [x for x in wanted if x not in keys]
    assert not missing, f"missing expected memory keys: {missing}; actual={keys}"


def assert_excludes(keys, *blocked):
    present = [x for x in blocked if x in keys]
    assert not present, f"unrelated memory leaked into context: {present}; actual={keys}"


def test_subculture_history():
    instruction = "サブカルキャラTの歴史についてまとめる"
    task = classify_task(instruction)
    assert task["task_kind"] == "HISTORICAL_RESEARCH", task
    assert "fashion_history" in task["domains"], task
    assert "character_merchandise" in task["domains"], task
    assert "subculture" in task["domains"], task

    result = select_context(
        instruction,
        CATALOG,
        mission_key="subculture_character_t_history_20260830",
        max_docs=8,
        char_budget=24000,
    )
    keys = result["selected_memory_keys"]
    assert_contains(
        keys,
        "global-project-relay-principles-v1",
        "task-research-summary-rules-v1",
        "mission-subculture-character-t-history-brief-v1",
    )
    assert_excludes(
        keys,
        "task-explicit-source-exclusion-rules-v1",
        "mission-gundam-zaku-development-pre-origin-brief-v1",
        "task-blender-runner-rules-v1",
        "mission-never-tear-3d-brief-v1",
        "task-discord-transport-v1",
    )
    assert result["selected_doc_count"] == 3, result
    assert result["estimated_chars"] <= result["char_budget"], result
    assert result["selected_doc_count"] <= result["max_docs"], result


def test_gundam_zaku_history_with_negative_source_constraint():
    instruction = "ガンダムにおいて、ザクが完成するまでにどのような紆余曲折を経たのかをまとめる資料を作成。ただしジ・オリジンの設定は参照しない"
    task = classify_task(instruction)
    assert task["task_kind"] == "HISTORICAL_RESEARCH", task
    assert "gundam_uc" in task["domains"], task
    assert "mecha_development" in task["domains"], task
    assert "fictional_lore" in task["domains"], task
    assert "source_exclusion" in task["domains"], task
    assert "ジ・オリジン" in task["excluded_sources"], task
    assert task["constraint_mode"] == "EXPLICIT_SOURCE_EXCLUSION", task

    result = select_context(
        instruction,
        CATALOG,
        mission_key="gundam_zaku_development_pre_origin_20260830",
        max_docs=8,
        char_budget=24000,
    )
    keys = result["selected_memory_keys"]
    assert_contains(
        keys,
        "global-project-relay-principles-v1",
        "task-research-summary-rules-v1",
        "task-explicit-source-exclusion-rules-v1",
        "mission-gundam-zaku-development-pre-origin-brief-v1",
    )
    assert_excludes(
        keys,
        "mission-subculture-character-t-history-brief-v1",
        "task-blender-runner-rules-v1",
        "mission-never-tear-3d-brief-v1",
        "task-discord-transport-v1",
    )
    assert result["selected_doc_count"] == 4, result
    assert result["estimated_chars"] <= result["char_budget"], result


def test_blender_does_not_load_research_rule():
    instruction = "Blenderでバーの3Dモデルを作る"
    result = select_context(instruction, CATALOG, mission_key="bar3d_sandbox")
    keys = result["selected_memory_keys"]
    assert result["task_kind"] == "BLENDER_3D", result
    assert_contains(keys, "global-project-relay-principles-v1", "task-blender-runner-rules-v1", "mission-never-tear-3d-brief-v1")
    assert_excludes(keys, "task-research-summary-rules-v1", "task-explicit-source-exclusion-rules-v1", "mission-subculture-character-t-history-brief-v1", "mission-gundam-zaku-development-pre-origin-brief-v1")


def test_budget_keeps_global():
    result = select_context(
        "サブカルキャラTの歴史についてまとめる",
        CATALOG,
        mission_key="subculture_character_t_history_20260830",
        max_docs=2,
        char_budget=7000,
    )
    keys = result["selected_memory_keys"]
    assert "global-project-relay-principles-v1" in keys, result
    assert len(keys) <= 2, result
    assert result["estimated_chars"] <= 7000, result


def main():
    test_subculture_history()
    test_gundam_zaku_history_with_negative_source_constraint()
    test_blender_does_not_load_research_rule()
    test_budget_keeps_global()
    print("PROJECT RELAY SELECTIVE MEMORY TESTS PASS")


if __name__ == "__main__":
    main()
