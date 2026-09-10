"""Packaged UKIE AI BRIDGE entrypoint.

The packaged entrypoint keeps the established diagnostic command surface while
routing artifact-producing local-analyze jobs through the atomic exact-once state
store and the preview-producing analysis runner. It exposes physical canary,
release-bound acceptance, offline verification, capability-scoped GPU probing,
release promotion evaluation, and P0.10 safe sync-folder handoff.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _configure_stdio() -> None:
    """Make structured JSON output Unicode-safe on Windows consoles/CI."""
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError, OSError):
                pass


_configure_stdio()

try:
    from bridge import main as bridge_main
    from bridge.acceptance_verifier import AcceptanceVerificationError, verify_acceptance_bundle
    from bridge.analyze_runner import run_local_analyze as run_preview_analyze
    from bridge.blender_canary import run_blender_canary
    from bridge.canary_verifier import CanaryVerificationError, verify_canary_bundle
    from bridge.gpu_probe import GPUProbeError, run_gpu_probe, verify_gpu_report
    from bridge.handoff import HandoffError, configure_handoff, run_acceptance_and_handoff
    from bridge.job_controller import execute_once
    from bridge.physical_acceptance import run_physical_acceptance
    from bridge.release_gate import ReleasePromotionError, evaluate_release_promotion
    from bridge.retry_contract import RetryContractError, validate_retry_contract
    from bridge.state_store import BridgeStateStore, StateConflictError
    from bridge.validator import JobValidationError, load_and_validate
    from bridge.install_manifest import InstallManifestError
    from bridge.artifact_validation import ArtifactValidationError
except ModuleNotFoundError:
    import main as bridge_main
    from acceptance_verifier import AcceptanceVerificationError, verify_acceptance_bundle
    from analyze_runner import run_local_analyze as run_preview_analyze
    from blender_canary import run_blender_canary
    from canary_verifier import CanaryVerificationError, verify_canary_bundle
    from gpu_probe import GPUProbeError, run_gpu_probe, verify_gpu_report
    from handoff import HandoffError, configure_handoff, run_acceptance_and_handoff
    from job_controller import execute_once
    from physical_acceptance import run_physical_acceptance
    from release_gate import ReleasePromotionError, evaluate_release_promotion
    from retry_contract import RetryContractError, validate_retry_contract
    from state_store import BridgeStateStore, StateConflictError
    from validator import JobValidationError, load_and_validate
    from install_manifest import InstallManifestError
    from artifact_validation import ArtifactValidationError


BRIDGE_VERSION = "0.12.0-p0.10"
CURRENT_CAPABILITIES = [
    "device_status",
    "analyze_blend",
    "preflight",
    "artifact_contract_validation",
    "known_failure_classification",
    "auth_health",
    "state_store_v2",
    "exact_once_local_analyze",
    "explicit_retry_contract",
    "utf8_stdio_guard",
    "preview_front",
    "preview_side",
    "blender_canary",
    "canary_evidence_verifier_v2",
    "release_promotion_gate_v1",
    "windows_display_adapter_inventory",
    "gpu_render_route_probe_v1",
    "physical_acceptance_v1",
    "one_click_acceptance_launcher",
    "acceptance_evidence_verifier_v1",
    "release_bound_physical_acceptance",
    "sync_folder_handoff_v1",
    "atomic_handoff_copy",
    "handoff_sha_sidecar",
]


def _load_object(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def cmd_current_self_test() -> int:
    result = {
        "status": "PASS",
        "bridge_version": BRIDGE_VERSION,
        "bridge_core_version": bridge_main.BRIDGE_VERSION,
        "protocol_version": bridge_main.PROTOCOL_VERSION,
        "browser_protocol_version": bridge_main.BROWSER_PROTOCOL_VERSION,
        "bp3d_blender_pin": bridge_main.BP3D_BLENDER_PIN,
        "capabilities": CURRENT_CAPABILITIES,
        "safety": {
            "arbitrary_shell": False,
            "arbitrary_powershell": False,
            "arbitrary_exe": False,
            "source_blend_overwrite": False,
            "synthetic_canary_release_promotion": False,
            "synthetic_acceptance_physical_verification": False,
            "release_gate_mutation": False,
            "stable_requires_separate_soak": True,
            "gpu_probe_saves_preferences": False,
            "gpu_probe_claims_external_utilization": False,
            "physical_acceptance_uploads": False,
            "physical_acceptance_promotes_release": False,
            "acceptance_verifier_executes_evidence": False,
            "handoff_uses_google_api_tokens": False,
            "handoff_claims_cloud_presence": False,
            "handoff_claims_drive_readback": False,
            "handoff_overwrites_different_content": False,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_current_device_status() -> int:
    result = bridge_main.device_status()
    result["bridge_version"] = BRIDGE_VERSION
    result["bridge_core_version"] = bridge_main.BRIDGE_VERSION
    result["capabilities"] = list(dict.fromkeys([*(result.get("capabilities") or []), *CURRENT_CAPABILITIES]))
    result["ready_for_ai"] = False
    result["readiness_gate"] = "PHYSICAL_ACCEPTANCE_CLOUD_READBACK_AND_RELEASE_PROMOTION_REQUIRED"
    result["physical_canary_verified"] = False
    result["gpu_render_ready"] = False
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_validate_retry(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE validate-retry")
    parser.add_argument("retry")
    args = parser.parse_args(argv)
    validated = validate_retry_contract(_load_object(Path(args.retry)))
    print(json.dumps({
        "status": "VALID",
        "bridge_version": BRIDGE_VERSION,
        **validated.__dict__,
        "execution_started": False,
        "rule": "intentional retry requires a new job_id; transport replay never re-executes",
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_state_snapshot(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE state-snapshot")
    parser.add_argument("--state-root")
    args = parser.parse_args(argv)
    store = BridgeStateStore(args.state_root)
    print(json.dumps(store.snapshot(), ensure_ascii=False, indent=2))
    return 0


def cmd_blender_canary(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE blender-canary")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--state-root")
    args = parser.parse_args(argv)
    result = run_blender_canary(Path(args.workspace), Path(args.state_root) if args.state_root else None)
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "CANARY_LOCAL_PASS" else 2


def cmd_verify_canary_bundle(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE verify-canary-bundle")
    parser.add_argument("bundle")
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)
    result = verify_canary_bundle(Path(args.bundle), args.expected_sha256)
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "CANARY_EVIDENCE_VALID" else 2


def cmd_gpu_check(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE gpu-check")
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args(argv)
    result = run_gpu_probe(Path(args.workspace))
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ready_for_gpu_render") is True else 2


def cmd_verify_gpu_report(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE verify-gpu-report")
    parser.add_argument("--report", required=True)
    parser.add_argument("--render")
    args = parser.parse_args(argv)
    result = verify_gpu_report(_load_object(Path(args.report)), Path(args.render) if args.render else None)
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ready_for_gpu_render") is True else 2


def cmd_physical_acceptance(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE physical-acceptance")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--state-root")
    parser.add_argument("--release-info")
    args = parser.parse_args(argv)
    release_info = _load_object(Path(args.release_info)) if args.release_info else None
    result = run_physical_acceptance(
        Path(args.workspace),
        Path(args.state_root) if args.state_root else None,
        release_info,
    )
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("local_core_ready") is True else 2


def cmd_verify_acceptance_bundle(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE verify-acceptance-bundle")
    parser.add_argument("bundle")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-release-key")
    args = parser.parse_args(argv)
    result = verify_acceptance_bundle(
        Path(args.bundle),
        args.expected_sha256,
        args.expected_release_key,
        allow_synthetic_test_fixture=False,
    )
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "ACCEPTANCE_EVIDENCE_VALID" else 2


def cmd_configure_handoff(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE configure-handoff")
    parser.add_argument("--destination")
    parser.add_argument("--config")
    args = parser.parse_args(argv)
    result = configure_handoff(
        Path(args.destination) if args.destination else None,
        config_path=Path(args.config) if args.config else None,
        interactive=args.destination is None,
    )
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_acceptance_and_handoff(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE acceptance-and-handoff")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--state-root")
    parser.add_argument("--release-info", required=True)
    parser.add_argument("--handoff-config")
    args = parser.parse_args(argv)
    release_info = _load_object(Path(args.release_info))
    result = run_acceptance_and_handoff(
        Path(args.workspace),
        release_info,
        run_physical_acceptance,
        state_root=Path(args.state_root) if args.state_root else None,
        config_path=Path(args.handoff_config) if args.handoff_config else None,
    )
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    acceptance = result.get("acceptance") if isinstance(result.get("acceptance"), dict) else {}
    return 0 if acceptance.get("local_core_ready") is True else 2


def cmd_validate_release_promotion(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE validate-release-promotion")
    parser.add_argument("--release", required=True)
    parser.add_argument("--canary", required=True)
    parser.add_argument("--target", choices=["CANARY_PASS", "STABLE"], required=True)
    parser.add_argument("--soak")
    args = parser.parse_args(argv)
    result = evaluate_release_promotion(
        _load_object(Path(args.release)),
        _load_object(Path(args.canary)),
        target=args.target,
        soak=_load_object(Path(args.soak)) if args.soak else None,
        allow_synthetic_test_fixture=False,
    )
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("eligible") else 2


def cmd_local_analyze_once(args: argparse.Namespace) -> int:
    job_path = Path(args.job)
    input_path = Path(args.input)
    workspace = Path(args.workspace)
    job = load_and_validate(job_path)
    store = BridgeStateStore(args.state_root if getattr(args, "state_root", None) else None)
    outcome = execute_once(job, store, lambda: run_preview_analyze(job_path, input_path, workspace))
    outcome["bridge_version"] = BRIDGE_VERSION
    outcome["exact_once"] = True
    outcome["visual_qa_artifacts_required"] = ["preview_front.png", "preview_side.png"]
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    if outcome.get("executed"):
        return 0 if outcome.get("decision") in {"LOCAL_SAVED", "VERIFIED", "COMPLETED"} else 2
    receipt = outcome.get("receipt") or {}
    status = receipt.get("status")
    if status in {"LOCAL_SAVED", "HASHED", "UPLOADING", "UPLOADED", "READBACK_VERIFYING", "VERIFIED", "COMPLETED"}:
        return 0
    return 2


def run_passthrough(argv: list[str]) -> int:
    parser = bridge_main.build_parser()
    state_root = None
    if argv and argv[0] == "local-analyze" and "--state-root" in argv:
        idx = argv.index("--state-root")
        if idx + 1 >= len(argv):
            raise JobValidationError("--state-root requires a value")
        state_root = argv[idx + 1]
        argv = argv[:idx] + argv[idx + 2:]
    args = parser.parse_args(argv)
    if getattr(args, "command", None) == "local-analyze":
        args.state_root = state_root
        return cmd_local_analyze_once(args)
    return int(args.func(args))


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv == ["self-test"]:
            return cmd_current_self_test()
        if argv == ["device-status"]:
            return cmd_current_device_status()
        if argv and argv[0] == "validate-retry":
            return cmd_validate_retry(argv[1:])
        if argv and argv[0] == "state-snapshot":
            return cmd_state_snapshot(argv[1:])
        if argv and argv[0] == "blender-canary":
            return cmd_blender_canary(argv[1:])
        if argv and argv[0] == "verify-canary-bundle":
            return cmd_verify_canary_bundle(argv[1:])
        if argv and argv[0] == "gpu-check":
            return cmd_gpu_check(argv[1:])
        if argv and argv[0] == "verify-gpu-report":
            return cmd_verify_gpu_report(argv[1:])
        if argv and argv[0] == "physical-acceptance":
            return cmd_physical_acceptance(argv[1:])
        if argv and argv[0] == "verify-acceptance-bundle":
            return cmd_verify_acceptance_bundle(argv[1:])
        if argv and argv[0] == "configure-handoff":
            return cmd_configure_handoff(argv[1:])
        if argv and argv[0] == "acceptance-and-handoff":
            return cmd_acceptance_and_handoff(argv[1:])
        if argv and argv[0] == "validate-release-promotion":
            return cmd_validate_release_promotion(argv[1:])
        return run_passthrough(argv)
    except (
        JobValidationError,
        InstallManifestError,
        ArtifactValidationError,
        RetryContractError,
        StateConflictError,
        CanaryVerificationError,
        GPUProbeError,
        AcceptanceVerificationError,
        HandoffError,
        ReleasePromotionError,
        FileNotFoundError,
        RuntimeError,
        ValueError,
    ) as exc:
        print(json.dumps({
            "status": "ERROR",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "bridge_version": BRIDGE_VERSION,
        }, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
