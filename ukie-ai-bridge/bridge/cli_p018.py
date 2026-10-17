"""P0.18 wrapper: paired cloud worker transport for allowlisted jobs only."""

from __future__ import annotations

import json
import sys

try:
    from bridge import cli_p015 as inherited_cli
    from bridge import main as bridge_main
    from bridge.worker_credentials import WorkerCredentialError
    from bridge.worker_transport import (
        WORKER_PROTOCOL,
        WORKER_VERSION,
        WorkerTransportError,
        begin_pairing,
        refresh_pairing,
        run_loop,
        run_once,
    )
except ModuleNotFoundError:
    import cli_p015 as inherited_cli
    import main as bridge_main
    from worker_credentials import WorkerCredentialError
    from worker_transport import WORKER_PROTOCOL, WORKER_VERSION, WorkerTransportError, begin_pairing, refresh_pairing, run_loop, run_once


BRIDGE_VERSION = WORKER_VERSION
bridge_main.BRIDGE_VERSION = BRIDGE_VERSION
inherited_cli.BRIDGE_VERSION = BRIDGE_VERSION


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def cmd_self_test() -> int:
    result = {
        "status": "PASS",
        "bridge_version": BRIDGE_VERSION,
        "worker_protocol": WORKER_PROTOCOL,
        "bp3d_blender_pin": bridge_main.BP3D_BLENDER_PIN,
        "p018_safety": {
            "cloud_allowlist": ["device_status"],
            "arbitrary_shell": False,
            "arbitrary_powershell": False,
            "arbitrary_exe": False,
            "cloud_filesystem_paths": False,
            "device_secret_generated_locally": True,
            "device_secret_cloud_plaintext": False,
            "windows_dpapi_required": True,
            "lease_required_for_completion": True,
            "stale_lease_completion_rejected": True,
            "source_blend_mutation": False,
            "ready_for_ai_self_promotion": False,
        },
    }
    _print(result)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv == ["self-test"]:
            return cmd_self_test()
        if argv and argv[0] == "worker-pair":
            allowed = {"--open-browser"}
            unknown = [v for v in argv[1:] if v not in allowed]
            if unknown:
                raise ValueError(f"unknown worker-pair option: {unknown[0]}")
            _print(begin_pairing(open_browser="--open-browser" in argv[1:]))
            return 0
        if argv == ["worker-pair-status"]:
            result = refresh_pairing()
            _print(result)
            return 0 if result.get("status") == "PAIRED" else 2
        if argv == ["worker-once"]:
            _print(run_once())
            return 0
        if argv and argv[0] == "worker-run":
            if len(argv) > 2:
                raise ValueError("worker-run accepts at most one poll interval")
            poll = int(argv[1]) if len(argv) == 2 else 10
            _print({"status": "WORKER_RUNNING", "poll_seconds": poll, "bridge_version": BRIDGE_VERSION})
            run_loop(poll_seconds=poll)
            return 0
        return inherited_cli.main(argv)
    except KeyboardInterrupt:
        _print({"status": "STOPPED", "reason": "keyboard_interrupt", "bridge_version": BRIDGE_VERSION})
        return 130
    except (WorkerTransportError, WorkerCredentialError, RuntimeError, ValueError, FileNotFoundError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc), "error_type": type(exc).__name__, "bridge_version": BRIDGE_VERSION}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
