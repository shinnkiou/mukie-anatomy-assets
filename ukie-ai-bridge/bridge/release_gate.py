"""Fail-closed release promotion policy for UKIE AI BRIDGE.

This module does not mutate Base44/GitHub/Drive state. It judges immutable snapshots
and returns a promotion decision. CANARY_PASS requires evidence from a real physical
Windows + Blender canary. STABLE additionally requires a completed soak window and a
verified rollback path. Synthetic CI fixtures can exercise the evaluator only when
explicit test-mode is enabled by the caller; production CLI never enables it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any


HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
BLENDER_PIN = "4.2.23"
MIN_STABLE_SOAK_HOURS = 24
MIN_STABLE_SUCCESSFUL_JOBS = 3
TARGETS = {"CANARY_PASS", "STABLE"}


class ReleasePromotionError(ValueError):
    pass


@dataclass(frozen=True)
class GateCheck:
    key: str
    passed: bool
    observed: Any
    expected: Any

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _check(checks: list[GateCheck], key: str, passed: bool, observed: Any, expected: Any) -> None:
    checks.append(GateCheck(key, bool(passed), observed, expected))


def _blender_pin_matches(value: Any) -> bool:
    text = _text(value)
    return bool(re.search(r"(?<!\d)4\.2\.23(?!\d)", text))


def _physical_canary_checks(
    release: dict[str, Any],
    canary: dict[str, Any],
    *,
    allow_synthetic_test_fixture: bool,
) -> list[GateCheck]:
    checks: list[GateCheck] = []
    metadata = _obj(canary.get("metadata"))
    evidence = _obj(canary.get("evidence_verification"))
    exact_once = _obj(canary.get("exact_once_verification"))
    semantic = _obj(canary.get("semantic_verification"))

    release_key = _text(release.get("release_key"))
    bridge_version = _text(release.get("bridge_version"))

    _check(checks, "release_key_present", bool(release_key), release_key or None, "non-empty release_key")
    _check(checks, "release_sha256_valid", bool(HEX64.fullmatch(_text(release.get("sha256")))), release.get("sha256"), "64 hex chars")
    _check(checks, "canary_status_verified", canary.get("status") == "VERIFIED", canary.get("status"), "VERIFIED")
    _check(checks, "canary_release_binding", canary.get("release_key") == release_key, canary.get("release_key"), release_key)
    _check(checks, "canary_bridge_version_binding", canary.get("bridge_version") == bridge_version, canary.get("bridge_version"), bridge_version)
    _check(checks, "physical_device_present", bool(_text(canary.get("device_key"))), canary.get("device_key"), "non-empty physical device key")
    _check(checks, "blender_pin", _blender_pin_matches(canary.get("blender_version")), canary.get("blender_version"), BLENDER_PIN)
    _check(checks, "drive_file_present", bool(_text(canary.get("drive_file_id"))), canary.get("drive_file_id"), "non-empty Drive file id")
    _check(checks, "bundle_sha256_valid", bool(HEX64.fullmatch(_text(canary.get("bundle_sha256")))), canary.get("bundle_sha256"), "64 hex chars")
    _check(checks, "drive_readback_proven", canary.get("drive_readback_proven") is True, canary.get("drive_readback_proven"), True)
    _check(checks, "source_unchanged", canary.get("source_unchanged") is True, canary.get("source_unchanged"), True)
    _check(checks, "evidence_status", evidence.get("status") == "CANARY_EVIDENCE_VALID", evidence.get("status"), "CANARY_EVIDENCE_VALID")
    _check(checks, "evidence_schema", evidence.get("schema_version") == "ukie_canary_evidence_verification_v2", evidence.get("schema_version"), "ukie_canary_evidence_verification_v2")
    _check(checks, "exact_once_decision", exact_once.get("decision") == "LOCAL_SAVED", exact_once.get("decision"), "LOCAL_SAVED")
    _check(checks, "exact_once_executed", exact_once.get("executed") is True, exact_once.get("executed"), True)
    _check(checks, "semantic_status", semantic.get("status") == "PASS", semantic.get("status"), "PASS")
    _check(checks, "semantic_vertices", semantic.get("vertices") == 8, semantic.get("vertices"), 8)
    _check(checks, "semantic_polygons", semantic.get("polygons") == 6, semantic.get("polygons"), 6)

    synthetic = metadata.get("synthetic_ci_only") is True
    physical_flag = metadata.get("physical_windows_blender_test") is True
    if allow_synthetic_test_fixture:
        _check(checks, "physical_provenance", physical_flag or synthetic, {"physical": physical_flag, "synthetic_ci_only": synthetic}, "physical=true OR explicit test fixture")
    else:
        _check(checks, "not_synthetic", not synthetic, synthetic, False)
        _check(checks, "physical_provenance", physical_flag, physical_flag, True)

    return checks


def _stable_checks(release: dict[str, Any], soak: dict[str, Any] | None) -> list[GateCheck]:
    checks: list[GateCheck] = []
    soak = _obj(soak)
    _check(checks, "release_already_canary_pass", release.get("status") == "CANARY_PASS", release.get("status"), "CANARY_PASS")
    _check(checks, "soak_schema", soak.get("schema_version") == "ukie_release_soak_v1", soak.get("schema_version"), "ukie_release_soak_v1")
    _check(checks, "soak_release_binding", soak.get("release_key") == release.get("release_key"), soak.get("release_key"), release.get("release_key"))
    _check(checks, "soak_status", soak.get("status") == "PASS", soak.get("status"), "PASS")
    observed_hours = soak.get("observed_hours")
    _check(checks, "soak_window", isinstance(observed_hours, (int, float)) and observed_hours >= MIN_STABLE_SOAK_HOURS, observed_hours, f">={MIN_STABLE_SOAK_HOURS} hours")
    jobs = soak.get("successful_jobs")
    _check(checks, "successful_jobs", isinstance(jobs, int) and not isinstance(jobs, bool) and jobs >= MIN_STABLE_SUCCESSFUL_JOBS, jobs, f">={MIN_STABLE_SUCCESSFUL_JOBS}")
    _check(checks, "crash_count_zero", soak.get("crash_count") == 0, soak.get("crash_count"), 0)
    _check(checks, "unresolved_high_failures_zero", soak.get("unresolved_high_failures") == 0, soak.get("unresolved_high_failures"), 0)
    _check(checks, "rollback_path_verified", soak.get("rollback_path_verified") is True, soak.get("rollback_path_verified"), True)
    _check(checks, "previous_release_available", bool(_text(release.get("rollback_release_key"))), release.get("rollback_release_key"), "non-empty rollback release key")
    return checks


def evaluate_release_promotion(
    release: dict[str, Any],
    canary: dict[str, Any],
    *,
    target: str,
    soak: dict[str, Any] | None = None,
    allow_synthetic_test_fixture: bool = False,
) -> dict[str, Any]:
    if not isinstance(release, dict) or not isinstance(canary, dict):
        raise ReleasePromotionError("release and canary snapshots must be JSON objects")
    if target not in TARGETS:
        raise ReleasePromotionError(f"unsupported promotion target: {target}")

    checks = _physical_canary_checks(
        release,
        canary,
        allow_synthetic_test_fixture=allow_synthetic_test_fixture,
    )

    if target == "CANARY_PASS":
        _check(checks, "release_pre_canary_state", release.get("status") in {"DRIVE_VERIFIED", "CANARY_PENDING"}, release.get("status"), ["DRIVE_VERIFIED", "CANARY_PENDING"])
    else:
        checks.extend(_stable_checks(release, soak))

    failed = [c.as_dict() for c in checks if not c.passed]
    passed = [c.as_dict() for c in checks if c.passed]
    eligible = not failed

    return {
        "schema_version": "ukie_release_promotion_gate_v1",
        "status": "PROMOTION_ELIGIBLE" if eligible else "PROMOTION_BLOCKED",
        "target": target,
        "release_key": release.get("release_key"),
        "bridge_version": release.get("bridge_version"),
        "eligible": eligible,
        "checks": [c.as_dict() for c in checks],
        "summary": {"passed": len(passed), "failed": len(failed), "total": len(checks)},
        "failed_checks": failed,
        "auto_update_eligible_after_promotion": bool(eligible and target == "STABLE"),
        "mutation_performed": False,
        "notes": (
            "This evaluator never changes release state. A separate authorized control-plane action must persist an eligible decision."
        ),
    }
