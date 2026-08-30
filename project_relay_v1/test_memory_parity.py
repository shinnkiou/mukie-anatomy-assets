import json
import subprocess
from pathlib import Path

from memory_context_loader import select_context

ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "testdata" / "memory_catalog_fixture.json"
CATALOG = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
JS = ROOT / "memory_context_loader.mjs"

CASES = [
    ("サブカルキャラTの歴史についてまとめる", "subculture_character_t_history_20260830"),
    ("ガンダムにおいて、ザクが完成するまでにどのような紆余曲折を経たのかをまとめる資料を作成。ただしジ・オリジンの設定は参照しない", "gundam_zaku_development_pre_origin_20260830"),
    ("Blenderでバーの3Dモデルを作る", "bar3d_sandbox"),
    ("PROJECT RELAYのDiscord transportを整理する", ""),
    ("いい感じにやっておいて", ""),
]


def js_result(instruction: str, mission_key: str):
    cp = subprocess.run(
        ["node", str(JS), instruction, str(CATALOG_PATH), mission_key],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(cp.stdout)


def main():
    for instruction, mission_key in CASES:
        py = select_context(instruction, CATALOG, mission_key=mission_key)
        js = js_result(instruction, mission_key)
        assert py["rules_version"] == js["rules_version"], (py, js)
        assert py["task_kind"] == js["task_kind"], (instruction, py, js)
        assert py["domains"] == js["domains"], (instruction, py, js)
        assert py.get("constraint_mode") == js.get("constraint_mode"), (instruction, py, js)
        assert py.get("excluded_sources") == js.get("excluded_sources"), (instruction, py, js)
        assert py["selected_memory_keys"] == js["selected_memory_keys"], (instruction, py, js)
        assert py["selected_doc_count"] == js["selected_doc_count"], (instruction, py, js)
        assert py["estimated_chars"] == js["estimated_chars"], (instruction, py, js)
        print(f"PARITY PASS: {instruction} -> {py['task_kind']} / constraints={py.get('excluded_sources')} / {py['selected_memory_keys']}")
    print("PROJECT RELAY PYTHON/JS MEMORY PARITY PASS")


if __name__ == "__main__":
    main()
