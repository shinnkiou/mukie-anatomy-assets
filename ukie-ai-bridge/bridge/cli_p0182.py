"""P0.18.2 standalone Windows worker bootstrap.

Double-clicking the packaged EXE with no arguments performs the one-time pairing
bootstrap and then enters the bounded P0.18 worker loop. Explicit CLI commands
remain available through the inherited P0.18.1 surface.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

try:
    from bridge import cli_p0181 as inherited_cli
    from bridge import main as bridge_main
    from bridge import worker_transport
except ModuleNotFoundError:
    import cli_p0181 as inherited_cli
    import main as bridge_main
    import worker_transport

try:
    from bridge import embedded_release_p0182 as embedded_release
except (ImportError, ModuleNotFoundError):
    try:
        import embedded_release_p0182 as embedded_release
    except (ImportError, ModuleNotFoundError):
        embedded_release = None

BRIDGE_VERSION = "0.18.2-p0.18.2"
PAIRING_UI_URL = "https://sync-ops-base.base44.app/"
PAIR_WAIT_SECONDS = 5
PAIR_WAIT_CHECKS = 120

worker_transport.PAIRING_UI_URL = PAIRING_UI_URL
worker_transport.WORKER_VERSION = BRIDGE_VERSION
bridge_main.BRIDGE_VERSION = BRIDGE_VERSION
inherited_cli.BRIDGE_VERSION = BRIDGE_VERSION
if hasattr(inherited_cli, "inherited_cli"):
    inherited_cli.inherited_cli.BRIDGE_VERSION = BRIDGE_VERSION


def _embedded_release_info() -> dict[str, Any]:
    if embedded_release is None:
        return worker_transport.load_release_info()
    return {
        "schema_version": "ukie_bridge_release_info_v1",
        "release_key": embedded_release.RELEASE_KEY,
        "bridge_version": embedded_release.BRIDGE_VERSION,
        "commit_sha": embedded_release.COMMIT_SHA,
        "workflow_run_id": embedded_release.WORKFLOW_RUN_ID,
        "bp3d_blender_pin": "4.2.23",
        "channel": "CANARY",
        "worker_protocol": worker_transport.WORKER_PROTOCOL,
        "worker_allowlist": ["device_status"],
    }


if embedded_release is not None:
    worker_transport.load_release_info = _embedded_release_info


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def cmd_bootstrap_self_test() -> int:
    frozen = bool(getattr(sys, "frozen", False))
    embedded_ok = embedded_release is not None
    checks = {
        "pairing_ui_root": worker_transport.PAIRING_UI_URL == PAIRING_UI_URL,
        "worker_version": worker_transport.WORKER_VERSION == BRIDGE_VERSION,
        "allowlist_device_status_only": worker_transport.ALLOWED_ACTIONS == {"device_status"},
        "embedded_release_present_when_packaged": (not frozen) or embedded_ok,
        "no_arg_bootstrap_enabled": True,
        "arbitrary_shell": False,
        "arbitrary_powershell": False,
        "arbitrary_exe": False,
        "cloud_filesystem_paths": False,
    }
    ok = all(checks.values())
    _print({
        "status": "PASS" if ok else "FAIL",
        "bridge_version": BRIDGE_VERSION,
        "frozen": frozen,
        "embedded_release": embedded_ok,
        "release_key": getattr(embedded_release, "RELEASE_KEY", None) if embedded_ok else None,
        "checks": checks,
    })
    return 0 if ok else 2


def bootstrap_worker() -> int:
    pair = worker_transport.begin_pairing(open_browser=True)
    _print(pair)

    status = pair.get("status")
    if status != "ALREADY_PAIRED":
        paired = False
        for _ in range(PAIR_WAIT_CHECKS):
            time.sleep(PAIR_WAIT_SECONDS)
            current = worker_transport.refresh_pairing()
            _print(current)
            if current.get("status") == "PAIRED":
                paired = True
                break
            if current.get("status") in {"EXPIRED", "REVOKED"}:
                raise worker_transport.WorkerTransportError(
                    f"worker pairing ended with status {current.get('status')}; restart the app to request a fresh code"
                )
        if not paired:
            raise worker_transport.WorkerTransportError("worker pairing approval timed out after 10 minutes")

    first_cycle = worker_transport.run_once()
    _print(first_cycle)
    _print({
        "status": "WORKER_RUNNING",
        "poll_seconds": worker_transport.POLL_SECONDS,
        "bridge_version": BRIDGE_VERSION,
        "note": "Keep this app open while cloud jobs are allowed to run.",
    })
    worker_transport.run_loop(poll_seconds=worker_transport.POLL_SECONDS)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if not argv:
            return bootstrap_worker()
        if argv == ["bootstrap-self-test"]:
            return cmd_bootstrap_self_test()
        return inherited_cli.main(argv)
    except KeyboardInterrupt:
        _print({"status": "STOPPED", "reason": "keyboard_interrupt", "bridge_version": BRIDGE_VERSION})
        return 130
    except (
        worker_transport.WorkerTransportError,
        RuntimeError,
        ValueError,
        FileNotFoundError,
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
