#!/usr/bin/env python3
"""C-057: derive public-safe transitive invariant suffix cores from pair aggregates.

No raw qword values are present. The proof uses only qword counts, exact-run
positions/lengths, phase labels, and trailing counts already published by the
mainline phase aggregate.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Mapping

PIPELINE_STAGE = "STRUCTURAL_ONLY"
CLASSIFICATION = "PHASE_CLASS_TRANSITIVE_INVARIANT_SUFFIX_CORE_CANDIDATE"

BASELINE = {
    "pipeline_stage": PIPELINE_STAGE,
    "semantic_promotion_count": 0,
    "blender_emit_ready": False,
    "runtime_dispatch": False,
    "raw_private_bytes_published": False,
    "mod7": {
        "ab": {"a":"F02","b":"F04","phase":7,"qa":2212,"qb":2320,"sa":402,"sb":510,"length":1809,"ta":1,"tb":1},
        "ac": {"a":"F02","b":"R01","phase":7,"qa":2212,"qb":2233,"sa":402,"sb":423,"length":1809,"ta":1,"tb":1},
    },
    "mod1": {
        "ab": {"a":"F06","b":"F07","phase":1,"qa":2564,"qb":2576,"sa":445,"sb":457,"length":2118,"ta":1,"tb":1},
        "ac": {"a":"F06","b":"R03","phase":1,"qa":2564,"qb":2275,"sa":762,"sb":473,"length":1801,"ta":1,"tb":1},
    },
}


def _validate_pair(p: Mapping[str, Any], errors: list[str], label: str) -> None:
    required = ("a","b","phase","qa","qb","sa","sb","length","ta","tb")
    if any(k not in p for k in required):
        errors.append(f"{label}_missing_fields")
        return
    for k in ("phase","qa","qb","sa","sb","length","ta","tb"):
        if type(p[k]) is not int or p[k] < 0:
            errors.append(f"{label}_invalid_{k}")
            return
    if p["sa"] + p["length"] + p["ta"] != p["qa"]:
        errors.append(f"{label}_a_not_suffix_anchored")
    if p["sb"] + p["length"] + p["tb"] != p["qb"]:
        errors.append(f"{label}_b_not_suffix_anchored")


def evaluate(row: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(row, Mapping):
        return {"accepted": False, "errors": ["input_not_mapping"]}
    if row.get("pipeline_stage") != PIPELINE_STAGE:
        errors.append("pipeline_not_structural_only")
    if row.get("semantic_promotion_count") != 0:
        errors.append("semantic_promotion_must_be_zero")
    if row.get("blender_emit_ready") is not False:
        errors.append("blender_emit_must_remain_blocked")
    if row.get("runtime_dispatch") is not False:
        errors.append("runtime_dispatch_must_remain_false")
    if row.get("raw_private_bytes_published") is not False:
        errors.append("raw_private_bytes_must_not_be_public")

    m7 = row.get("mod7") or {}
    m1 = row.get("mod1") or {}
    for group, name in ((m7,"mod7"),(m1,"mod1")):
        if not isinstance(group, Mapping) or not isinstance(group.get("ab"), Mapping) or not isinstance(group.get("ac"), Mapping):
            errors.append(f"{name}_missing_pairs")
            continue
        _validate_pair(group["ab"], errors, f"{name}_ab")
        _validate_pair(group["ac"], errors, f"{name}_ac")

    if errors:
        return {"accepted": False, "errors": errors, "classification": "REJECTED"}

    m7ab, m7ac = m7["ab"], m7["ac"]
    if m7ab["a"] != m7ac["a"] or m7ab["phase"] != 7 or m7ac["phase"] != 7:
        errors.append("mod7_anchor_or_phase_mismatch")
    if (m7ab["sa"],m7ab["length"],m7ab["ta"]) != (m7ac["sa"],m7ac["length"],m7ac["ta"]):
        errors.append("mod7_anchor_ranges_not_identical")
    if m7ab["tb"] != m7ac["tb"]:
        errors.append("mod7_target_tail_mismatch")

    m1ab, m1ac = m1["ab"], m1["ac"]
    if m1ab["a"] != m1ac["a"] or m1ab["phase"] != 1 or m1ac["phase"] != 1:
        errors.append("mod1_anchor_or_phase_mismatch")
    end_ab = m1ab["sa"] + m1ab["length"]
    end_ac = m1ac["sa"] + m1ac["length"]
    if end_ab != end_ac:
        errors.append("mod1_anchor_runs_not_common_end")
    if m1ac["sa"] < m1ab["sa"] or m1ac["length"] > m1ab["length"]:
        errors.append("mod1_short_run_not_nested")
    if m1ab["ta"] != m1ac["ta"] or m1ab["tb"] != m1ac["tb"]:
        errors.append("mod1_tail_mismatch")

    mod1_b_core_start = m1ab["sb"] + (m1ac["sa"] - m1ab["sa"])
    if mod1_b_core_start + m1ac["length"] + m1ab["tb"] != m1ab["qb"]:
        errors.append("mod1_mapped_core_not_suffix_anchored")

    if errors:
        return {"accepted": False, "errors": errors, "classification": "REJECTED"}

    return {
        "accepted": True,
        "errors": [],
        "classification": CLASSIFICATION,
        "cores": {
            "mod7": {
                "fixtures": [m7ab["a"], m7ab["b"], m7ac["b"]],
                "common_exact_core_qwords": 1809,
                "trailing_qwords_each": 1,
                "ranges": {
                    m7ab["a"]: [m7ab["sa"], m7ab["sa"] + m7ab["length"]],
                    m7ab["b"]: [m7ab["sb"], m7ab["sb"] + m7ab["length"]],
                    m7ac["b"]: [m7ac["sb"], m7ac["sb"] + m7ac["length"]],
                },
            },
            "mod1": {
                "fixtures": [m1ab["a"], m1ab["b"], m1ac["b"]],
                "common_exact_core_qwords": 1801,
                "trailing_qwords_each": 1,
                "pair_specific_extension_f06_f07_qwords": m1ab["length"] - m1ac["length"],
                "ranges": {
                    m1ab["a"]: [m1ac["sa"], m1ac["sa"] + m1ac["length"]],
                    m1ab["b"]: [mod1_b_core_start, mod1_b_core_start + m1ac["length"]],
                    m1ac["b"]: [m1ac["sb"], m1ac["sb"] + m1ac["length"]],
                },
            },
        },
        "semantic_binding": "UNRESOLVED",
        "semantic_promotion": False,
        "blender_emit_ready": False,
        "runtime_dispatch": False,
    }


def self_test() -> None:
    out = evaluate(BASELINE)
    assert out["accepted"] is True
    assert out["cores"]["mod7"]["common_exact_core_qwords"] == 1809
    assert out["cores"]["mod1"]["common_exact_core_qwords"] == 1801
    assert out["cores"]["mod1"]["pair_specific_extension_f06_f07_qwords"] == 317
    assert out["cores"]["mod1"]["ranges"]["F07"] == [774, 2575]

    cases = []
    bad = deepcopy(BASELINE); bad["mod7"]["ac"]["sa"] = 403; cases.append(bad)
    bad = deepcopy(BASELINE); bad["mod1"]["ac"]["length"] = 1800; cases.append(bad)
    bad = deepcopy(BASELINE); bad["mod1"]["ab"]["tb"] = 2; cases.append(bad)
    bad = deepcopy(BASELINE); bad["semantic_promotion_count"] = 1; cases.append(bad)
    bad = deepcopy(BASELINE); bad["blender_emit_ready"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["runtime_dispatch"] = True; cases.append(bad)
    bad = deepcopy(BASELINE); bad["raw_private_bytes_published"] = True; cases.append(bad)
    for candidate in cases:
        assert evaluate(candidate)["accepted"] is False

    print("C057_SELF_TEST_PASS 8/8")


if __name__ == "__main__":
    self_test()
