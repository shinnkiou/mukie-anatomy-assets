"""Fail-closed release promotion evaluation for UKIE AI BRIDGE.

Promotion is evidence-based. A release cannot become CANARY_PASS, READY_FOR_AI,
or AUTO_UPDATE_ELIGIBLE because a UI flag changed or because a process exited 0.
Every target has explicit gates; missing evidence is a refusal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


TARGETS = ("FOUNDATION_VERIFIED", "CANARY_PASS", "READY_FOR_AI", "AUTO_UPDATE_ELIGIBLE")


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    detail: str


def _bool(evidence: dict[str, Any], key: str) -> bool:
    return evidence.get(key) is True


def _eq(evidence: dict[str, Any], key: str, expected: Any) -> bool:
    return evidence.get(key) == expected


def evaluate_promotion(evidence: dict[str, Any], target: str) -> dict[str, Any]:
    if target not in TARGETS:
        raise ValueError(f"unsupported promotion target: {target}")

    gates: list[GateResult] = [
        GateResult("windows_ci", _bool(evidence, "windows_ci_pass"), "Windows source/regression CI passed"),
        GateResult("packaged_exe_selftest", _bool(evidence, "packaged_exe_selftest_pass"), "generated EXE self-test passed"),
        GateResult("drive_package_readback", _bool(evidence, "drive_package_readback_sha_match"), "release package Drive readback SHA matched"),
        GateResult("rollback_release_known", bool(evidence.get("rollback_release_key")), "a rollback target is recorded"),
    ]

    if target in {"CANARY_PASS", "READY_FOR_AI", "AUTO_UPDATE_ELIGIBLE"}:
        gates.extend([
            GateResult("physical_windows_handshake", _bool(evidence, "physical_windows_handshake"), "physical Windows worker identified itself"),
            GateResult("blender_pin", _eq(evidence, "blender_version", "4.2.23"), "BP3D production Blender pin is exactly 4.2.23"),
            GateResult("physical_canary_local", _bool(evidence, "physical_canary_local_pass"), "disposable physical Blender canary passed locally"),
            GateResult("canary_drive_readback", _bool(evidence, "canary_drive_readback_sha_match"), "physical canary bundle Drive readback SHA matched"),
            GateResult("canary_evidence", _eq(evidence, "canary_evidence_status", "CANARY_EVIDENCE_VALID"), "offline canary verifier accepted readback evidence"),
            GateResult("source_immutable", _bool(evidence, "canary_source_unchanged"), "canary source SHA was unchanged"),
            GateResult("preview_front", _bool(evidence, "preview_front_verified"), "front preview passed evidence validation"),
            GateResult("preview_side", _bool(evidence, "preview_side_verified"), "side preview passed evidence validation"),
        ])

    if target in {"READY_FOR_AI", "AUTO_UPDATE_ELIGIBLE"}:
        gates.extend([
            GateResult("gpu_windows", _bool(evidence, "windows_gpu_detected"), "Windows GPU inventory completed"),
            GateResult("gpu_blender", _bool(evidence, "blender_gpu_detected"), "Blender enumerated a render-capable GPU"),
            GateResult("gpu_workload", _bool(evidence, "gpu_workload_pass"), "small Blender GPU workload completed"),
            GateResult("job_roundtrip", _bool(evidence, "drive_blender_drive_roundtrip_pass"), "real Drive -> Blender -> Drive job roundtrip passed"),
            GateResult("exact_once_replay", _bool(evidence, "exact_once_replay_test_pass"), "duplicate transport delivery did not re-execute"),
            GateResult("timeout_recovery", _bool(evidence, "timeout_recovery_test_pass"), "Blender timeout recovery kept Bridge alive"),
        ])

    if target == "AUTO_UPDATE_ELIGIBLE":
        crash_free = evidence.get("crash_free_canary_runs")
        gates.extend([
            GateResult("rollback_test", _bool(evidence, "rollback_test_pass"), "automatic rollback path was tested"),
            GateResult("crash_free_runs", isinstance(crash_free, int) and not isinstance(crash_free, bool) and crash_free >= 3, "at least 3 consecutive crash-free physical canary runs"),
            GateResult("update_signature", _bool(evidence, "update_signature_verified"), "candidate update signature was verified"),
            GateResult("human_policy_approval", _bool(evidence, "human_auto_update_policy_approval"), "user enabled the auto-update policy for this channel"),
        ])

    missing = [g.name for g in gates if not g.passed]
    passed = not missing
    stage = target if passed else "BLOCKED"
    return {
        "schema_version": "ukie_release_promotion_v1",
        "target": target,
        "status": "PASS" if passed else "BLOCKED",
        "promoted_stage": stage,
        "auto_update_eligible": bool(passed and target == "AUTO_UPDATE_ELIGIBLE"),
        "gate_count": len(gates),
        "passed_count": sum(1 for g in gates if g.passed),
        "missing_gates": missing,
        "gates": [g.__dict__ for g in gates],
        "fail_closed": True,
    }
