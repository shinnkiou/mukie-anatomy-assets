"""Packaged UKIE AI BRIDGE entrypoint.

The packaged entrypoint keeps the established diagnostic command surface while
routing artifact-producing local-analyze jobs through the atomic exact-once state
store and the P0.4 preview-producing analysis runner.
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
    from bridge.analyze_runner import run_local_analyze as run_preview_analyze
    from bridge.job_controller import execute_once
    from bridge.retry_contract import RetryContractError, validate_retry_contract
    from bridge.state_store import BridgeStateStore, StateConflictError
    from bridge.validator import JobValidationError, load_and_validate
    from bridge.install_manifest import InstallManifestError
    from bridge.artifact_validation import ArtifactValidationError
except ModuleNotFoundError:
    import main as bridge_main
    from analyze_runner import run_local_analyze as run_preview_analyze
    from job_controller import execute_once
    from retry_contract import RetryContractError, validate_retry_contract
    from state_store import BridgeStateStore, StateConflictError
    from validator import JobValidationError, load_and_validate
    from install_manifest import InstallManifestError
    from artifact_validation import ArtifactValidationError


BRIDGE_VERSION = "0.5.0-p0.4"


def _load_object(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RetryContractError("JSON root must be an object")
    return value


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


def cmd_local_analyze_once(args: argparse.Namespace) -> int:
    job_path = Path(args.job)
    input_path = Path(args.input)
    workspace = Path(args.workspace)
    job = load_and_validate(job_path)
    store = BridgeStateStore(args.state_root if getattr(args, "state_root", None) else None)

    outcome = execute_once(
        job,
        store,
        lambda: run_preview_analyze(job_path, input_path, workspace),
    )
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
        if argv and argv[0] == "validate-retry":
            return cmd_validate_retry(argv[1:])
        if argv and argv[0] == "state-snapshot":
            return cmd_state_snapshot(argv[1:])
        return run_passthrough(argv)
    except (
        JobValidationError,
        InstallManifestError,
        ArtifactValidationError,
        RetryContractError,
        StateConflictError,
        FileNotFoundError,
        RuntimeError,
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
