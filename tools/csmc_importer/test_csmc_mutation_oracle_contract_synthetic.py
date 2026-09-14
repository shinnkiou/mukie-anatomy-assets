#!/usr/bin/env python3
from __future__ import annotations
import copy
from csmc_mutation_oracle_contract import build_oracle_report, OracleContractError


def row(i: int, result="PENDING_MANUAL_ORACLE", visual="PENDING_MANUAL_ORACLE"):
    region = (
        "PREFIX_INTERIOR" if i <= 10 else
        "INVARIANT_BOUNDARY" if i <= 17 else
        "INVARIANT_INTERIOR" if i <= 21 else
        "ALIGNMENT_EXTENSION" if i == 22 else
        "FRAMING_REMAINDER"
    )
    return {
        "variant_id": f"M{i:02d}",
        "filename": f"CSMC_M{i:02d}_synthetic.csmc",
        "source_offset": i,
        "structural_region": region,
        "byte_before": "00",
        "byte_after": "01",
        "oracle_result": result,
        "visible_effect": visual,
        "error_class": "NONE" if result != "PENDING_MANUAL_ORACLE" else "PENDING",
        "process_survival": "ALIVE" if result not in {"CRASH", "PENDING_MANUAL_ORACLE"} else "NOT_OBSERVED",
        "evidence_strength": "PENDING" if result == "PENDING_MANUAL_ORACLE" else "MODERATE",
        "save_normalization_result": "NOT_RUN_POLICY",
        "serialization_triggered": False,
    }


def main():
    pending = build_oracle_report([row(i) for i in range(1, 31)])
    assert pending["observation_count"] == 30
    assert pending["pending_count"] == 30
    assert pending["oracle_complete"] is False
    assert pending["save_allowed"] is False
    assert pending["serialization_trigger_allowed"] is False
    assert pending["semantic_promotion"] is False
    assert pending["blender_emit"] is False

    complete_rows = []
    for i in range(1, 31):
        complete_rows.append(row(i, "LOAD_ACCEPTED", "VISIBLE_MODEL_UNCHANGED"))
    complete = build_oracle_report(complete_rows)
    assert complete["pending_count"] == 0
    assert complete["oracle_complete"] is True
    assert complete["result_counts"] == {"LOAD_ACCEPTED": 30}

    bad = copy.deepcopy(complete_rows)
    bad[0]["save_normalization_result"] = "SAVED"
    try:
        build_oracle_report(bad)
        raise AssertionError("save policy violation accepted")
    except OracleContractError:
        pass

    bad = copy.deepcopy(complete_rows)
    bad[0]["serialization_triggered"] = True
    try:
        build_oracle_report(bad)
        raise AssertionError("serialization trigger accepted")
    except OracleContractError:
        pass

    bad = copy.deepcopy(complete_rows)
    bad[1]["variant_id"] = bad[0]["variant_id"]
    try:
        build_oracle_report(bad)
        raise AssertionError("duplicate variant accepted")
    except OracleContractError:
        pass

    try:
        build_oracle_report(complete_rows[:-1])
        raise AssertionError("29-row complete batch accepted")
    except OracleContractError:
        pass

    print("PASS csmc mutation oracle contract synthetic")


if __name__ == "__main__":
    main()
