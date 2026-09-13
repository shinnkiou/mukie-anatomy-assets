#!/usr/bin/env python3
"""Combine public-safe +965 family counts with counted-BE entropy ceilings.

No payload bytes are read. This is an aggregate compatibility calculation only.
It asks whether an entire already-known structural family could, in principle,
share one counted-BE f32 binding at each predeclared fixed role.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "csmc_p4_counted_be_family_compatibility_v1"
ROLE_EXPECTED_COUNTS = {
    "record_whole_48": 95,
    "record_whole_49": 97,
    "stable_prefix_0_20": 41,
    "control_zone_21_27": 13,
    "preserved_island_25_26": 3,
}


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    if doc.get("schema_version") != SCHEMA:
        errors.append("invalid_schema_version")
    families = doc.get("families")
    if not isinstance(families, list) or not families:
        errors.append("missing_families")
    else:
        total = 0
        for i, fam in enumerate(families):
            if not isinstance(fam, dict):
                errors.append(f"family_{i}_malformed")
                continue
            try:
                n = int(fam["count"])
                length = int(fam["length_qwords"])
            except Exception:
                errors.append(f"family_{i}_bad_count_or_length")
                continue
            if n <= 0 or length not in (48, 49):
                errors.append(f"family_{i}_unsupported_shape")
            total += n
            sig = str(fam.get("preserve_signature", ""))
            if len(sig) != 7 or any(c not in "01" for c in sig):
                errors.append(f"family_{i}_bad_signature")
        if total != 22:
            errors.append("family_count_total_not_22")
    ceilings = doc.get("entropy_fit_ceiling")
    if not isinstance(ceilings, dict):
        errors.append("missing_entropy_fit_ceiling")
    else:
        for role in ("record_whole", "stable_prefix_0_20", "control_zone_21_27", "preserved_island_25_26"):
            row = ceilings.get(role)
            if not isinstance(row, dict):
                errors.append(f"missing_ceiling_{role}")
                continue
            for surface in ("A", "B"):
                try:
                    v = int(row[surface])
                    if v < 0 or v > 22:
                        errors.append(f"invalid_ceiling_{role}_{surface}")
                except Exception:
                    errors.append(f"invalid_ceiling_{role}_{surface}")
    guardrails = doc.get("guardrails", {})
    for key in ("codec_binding_confirmed", "semantic_owner_confirmed", "geometry_confirmed", "runtime_executed"):
        if guardrails.get(key) is not False:
            errors.append(f"guardrail_{key}_must_be_false")
    return sorted(set(errors))


def analyze(doc: dict) -> dict:
    errors = validate(doc)
    if errors:
        return {"schema_version": "csmc_p4_counted_be_family_compatibility_result_v1", "valid": False, "errors": errors}

    ceilings = doc["entropy_fit_ceiling"]
    results = []
    excluded = []
    possible = []
    for fam in doc["families"]:
        fam_id = fam["family_id"]
        n = int(fam["count"])
        length = int(fam["length_qwords"])
        sig = str(fam["preserve_signature"])
        roles = {}
        for role in ("record_whole", "stable_prefix_0_20", "control_zone_21_27", "preserved_island_25_26"):
            a = int(ceilings[role]["A"])
            b = int(ceilings[role]["B"])
            cross = min(a, b)
            can_full = n <= cross
            entry = {
                "family_count": n,
                "surface_A_max_fit_rows": a,
                "surface_B_max_fit_rows": b,
                "cross_surface_max_fit_rows": cross,
                "entire_family_binding_compatible": can_full,
            }
            if role == "record_whole":
                entry["expected_be_f32_count"] = ROLE_EXPECTED_COUNTS[f"record_whole_{length}"]
            else:
                entry["expected_be_f32_count"] = ROLE_EXPECTED_COUNTS[role]
            roles[role] = entry
            token = f"{fam_id}:{role}"
            (possible if can_full else excluded).append(token)
        results.append({
            "family_id": fam_id,
            "length_qwords": length,
            "preserve_signature": sig,
            "count": n,
            "q21_preserved": sig[0] == "1",
            "q25_q26_preserved": sig[4:6] == "11",
            "roles": roles,
        })

    # Strong aggregate deductions from family size alone.
    control_excluded_families = [r["family_id"] for r in results if not r["roles"]["control_zone_21_27"]["entire_family_binding_compatible"]]
    island_excluded_families = [r["family_id"] for r in results if not r["roles"]["preserved_island_25_26"]["entire_family_binding_compatible"]]
    q21_preserved_families = [r for r in results if r["q21_preserved"]]

    special = []
    for r in q21_preserved_families:
        if not r["roles"]["control_zone_21_27"]["entire_family_binding_compatible"]:
            special.append({
                "family_id": r["family_id"],
                "deduction": "Q21_PRESERVED_FAMILY_CANNOT_BE_UNIVERSALLY_COUNTED_BE_F32_AT_CONTROL_ROLE",
                "reason": f"family_size={r['count']} exceeds cross-surface entropy fit ceiling={r['roles']['control_zone_21_27']['cross_surface_max_fit_rows']}",
            })

    return {
        "schema_version": "csmc_p4_counted_be_family_compatibility_result_v1",
        "valid": True,
        "family_count": len(results),
        "record_count": sum(r["count"] for r in results),
        "encoding_under_test": "COUNTED_BE_F32",
        "roles_are_predeclared": True,
        "families": results,
        "entire_family_bindings_excluded": excluded,
        "entire_family_bindings_still_compatible": possible,
        "control_role_fully_bound_family_exclusions": control_excluded_families,
        "island_role_fully_bound_family_exclusions": island_excluded_families,
        "special_deductions": special,
        "codec_binding_confirmed": False,
        "semantic_promotions": 0,
        "runtime_executed": False,
    }


def fixture() -> dict:
    return {
        "schema_version": SCHEMA,
        "families": [
            {"family_id": "F48_0000110", "length_qwords": 48, "preserve_signature": "0000110", "count": 7},
            {"family_id": "F48_0000111", "length_qwords": 48, "preserve_signature": "0000111", "count": 3},
            {"family_id": "F48_0001110", "length_qwords": 48, "preserve_signature": "0001110", "count": 3},
            {"family_id": "F49_0000111", "length_qwords": 49, "preserve_signature": "0000111", "count": 3},
            {"family_id": "F49_1000111", "length_qwords": 49, "preserve_signature": "1000111", "count": 6},
        ],
        "entropy_fit_ceiling": {
            "record_whole": {"A": 7, "B": 7},
            "stable_prefix_0_20": {"A": 7, "B": 7},
            "control_zone_21_27": {"A": 6, "B": 5},
            "preserved_island_25_26": {"A": 6, "B": 6},
        },
        "guardrails": {
            "codec_binding_confirmed": False,
            "semantic_owner_confirmed": False,
            "geometry_confirmed": False,
            "runtime_executed": False,
        },
    }


def self_test() -> None:
    out = analyze(fixture())
    assert out["valid"] is True
    assert out["record_count"] == 22
    assert set(out["control_role_fully_bound_family_exclusions"]) == {"F48_0000110", "F49_1000111"}
    assert out["island_role_fully_bound_family_exclusions"] == ["F48_0000110"]
    # The only q21-preserved family has six rows, but surface B permits at most five counted-BE control-role fits.
    assert out["special_deductions"] == [{
        "family_id": "F49_1000111",
        "deduction": "Q21_PRESERVED_FAMILY_CANNOT_BE_UNIVERSALLY_COUNTED_BE_F32_AT_CONTROL_ROLE",
        "reason": "family_size=6 exceeds cross-surface entropy fit ceiling=5",
    }]
    # Whole/prefix ceilings of seven do not exclude any family by size.
    assert all(r["roles"]["record_whole"]["entire_family_binding_compatible"] for r in out["families"])
    assert all(r["roles"]["stable_prefix_0_20"]["entire_family_binding_compatible"] for r in out["families"])
    bad = fixture()
    bad["guardrails"]["codec_binding_confirmed"] = True
    assert analyze(bad)["valid"] is False
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
