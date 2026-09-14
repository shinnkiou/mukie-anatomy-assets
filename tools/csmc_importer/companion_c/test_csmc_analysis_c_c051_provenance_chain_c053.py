#!/usr/bin/env python3
"""Regression tests for C-053 provenance continuity gate."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "csmc_analysis_c_c051_provenance_chain_c053.py"
spec = importlib.util.spec_from_file_location("c053", TARGET)
c053 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(c053)


def _base():
    teachers = c053._teacher_rows()
    conversions = c053._conversion_rows(teachers)
    analyses = c053._analysis_rows(teachers, conversions)
    return teachers, conversions, analyses


def test_full_chain_accepts():
    t, c, a = _base()
    out = c053.validate_analysis_manifest(t, c, a)
    assert out["accepted"] is True
    assert out["semantic_promotion_count"] == 0
    assert out["runtime_dispatch"] is False


def test_teacher_hash_required():
    t, _, _ = _base()
    t[0]["source_blend_sha256"] = "x"
    assert c053.validate_teacher_provenance(t)["reason"] == "invalid_source_blend_sha256"


def test_teacher_fingerprint_binds_metadata():
    t, _, _ = _base()
    t[0]["triangles_total"] += 1
    assert c053.validate_teacher_provenance(t)["reason"] == "teacher_row_fingerprint_mismatch"


def test_conversion_binds_source():
    t, c, _ = _base()
    c[0]["source_blend_sha256"] = c053._hash("wrong")
    assert c053.validate_conversion_manifest(t, c)["reason"] == "source_blend_hash_mismatch"


def test_conversion_binds_teacher():
    t, c, _ = _base()
    c[0]["teacher_row_sha256"] = c053._hash("wrong")
    assert c053.validate_conversion_manifest(t, c)["reason"] == "teacher_binding_mismatch"


def test_analysis_binds_csmc_hash():
    t, c, a = _base()
    a[0]["csmc_container_sha256"] = c053._hash("wrong")
    assert c053.validate_analysis_manifest(t, c, a)["reason"] == "csmc_container_sha256_analysis_binding_mismatch"


def test_outer_framing_fail_closed():
    t, c, a = _base()
    a[0]["stored_length"] += 8
    assert c053.validate_analysis_manifest(t, c, a)["reason"] == "outer_framing_rule_failed"


def test_raw_payload_rejected():
    t, c, a = _base()
    a[0]["raw_csmc_bytes"] = "forbidden"
    assert c053.validate_analysis_manifest(t, c, a)["reason"] == "forbidden_raw_field"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for test in tests:
        test()
    print(f"TEST_PASS {len(tests)}/{len(tests)}")
