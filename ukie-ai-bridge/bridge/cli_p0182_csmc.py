"""Experimental P0.18.2 CSMC canary worker v4.

This is not production. It reuses an already-approved Worker credential and
connects only to the isolated CSMC canary transport. Its CSMC capabilities are
fixed observer capture, diagnostic-only observer scan, and fixed-root artifact
upload. Cloud jobs cannot provide commands, paths, URLs, args, or key sequences.
"""
from __future__ import annotations

import json
import sys
from typing import Any

try:
    from bridge import main as bridge_main
    from bridge import worker_transport_csmc as worker_transport
except ModuleNotFoundError:
    import main as bridge_main
    import worker_transport_csmc as worker_transport

try:
    from bridge import embedded_release_csmc as embedded_release
except (ImportError, ModuleNotFoundError):
    try: import embedded_release_csmc as embedded_release
    except (ImportError, ModuleNotFoundError): embedded_release = None

BRIDGE_VERSION = "0.18.2-p0.18.2-csmc-canary4"
PAIRING_UI_URL = "https://sync-ops-base.base44.app/"
worker_transport.PAIRING_UI_URL = PAIRING_UI_URL
worker_transport.base.PAIRING_UI_URL = PAIRING_UI_URL
worker_transport.set_worker_version(BRIDGE_VERSION)
bridge_main.BRIDGE_VERSION = BRIDGE_VERSION


def _embedded_release_info() -> dict[str, Any]:
    if embedded_release is None: return worker_transport.load_release_info()
    return {
        "schema_version": "ukie_bridge_release_info_v1",
        "release_key": embedded_release.RELEASE_KEY,
        "bridge_version": embedded_release.BRIDGE_VERSION,
        "commit_sha": embedded_release.COMMIT_SHA,
        "workflow_run_id": embedded_release.WORKFLOW_RUN_ID,
        "bp3d_blender_pin": "4.2.23",
        "channel": "CSMC_CANARY",
        "worker_protocol": worker_transport.WORKER_PROTOCOL,
        "worker_allowlist": sorted(worker_transport.ALLOWED_ACTIONS),
        "canary_edge_url": worker_transport.CSMC_CANARY_EDGE_URL,
        "production_worker_unchanged": True,
    }

if embedded_release is not None:
    worker_transport.load_release_info = _embedded_release_info
    worker_transport.base.load_release_info = _embedded_release_info


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def cmd_self_test() -> int:
    allowed = set(worker_transport.ALLOWED_ACTIONS)
    expected = {"device_status", "csmc_observer_capture", "csmc_observer_diagnose_v1", "csmc_artifact_upload"}
    checks = {
        "experimental_version": BRIDGE_VERSION.endswith("-csmc-canary4"),
        "allowlist_exact": allowed == expected,
        "isolated_edge": worker_transport.CSMC_CANARY_EDGE_URL != worker_transport.PRODUCTION_EDGE_URL,
        "active_edge_is_canary": worker_transport.base.EDGE_URL == worker_transport.CSMC_CANARY_EDGE_URL,
        "new_pairing_disabled": True,
        "arbitrary_shell_disabled": "arbitrary_shell" not in allowed,
        "arbitrary_powershell_disabled": "powershell" not in allowed,
        "arbitrary_exe_disabled": "exe" not in allowed,
        "cloud_filesystem_paths_disabled": True,
        "cloud_upload_url_disabled": True,
        "single_poll_cli_enabled": True,
        "production_worker_unchanged": True,
    }
    ok = all(checks.values())
    _print({"status":"PASS" if ok else "FAIL","bridge_version":BRIDGE_VERSION,"release_key":getattr(embedded_release,"RELEASE_KEY",None) if embedded_release else None,"worker_allowlist":sorted(allowed),"canary_edge_url":worker_transport.CSMC_CANARY_EDGE_URL,"checks":checks})
    return 0 if ok else 2


def _require_existing_pairing() -> dict[str, Any]:
    pair = worker_transport.begin_pairing(open_browser=False)
    _print(pair)
    if pair.get("status") != "ALREADY_PAIRED":
        raise worker_transport.WorkerTransportError("CSMC canary requires an existing approved worker pairing")
    return pair


def cmd_once() -> int:
    _require_existing_pairing(); result = worker_transport.run_once(); _print(result); return 0


def bootstrap_worker() -> int:
    _require_existing_pairing()
    first_cycle = worker_transport.run_once(); _print(first_cycle)
    _print({"status":"CSMC_CANARY_WORKER_RUNNING","poll_seconds":worker_transport.POLL_SECONDS,"bridge_version":BRIDGE_VERSION,"allowlist":sorted(worker_transport.ALLOWED_ACTIONS),"transport":worker_transport.CSMC_CANARY_EDGE_URL,"note":"Experimental isolated canary only; production Worker/queue/Edge/STABLE unchanged."})
    worker_transport.run_loop(poll_seconds=worker_transport.POLL_SECONDS); return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv == ["self-test"]: return cmd_self_test()
        if argv == ["once"]: return cmd_once()
        if not argv: return bootstrap_worker()
        _print({"status":"ERROR","error":"unsupported experimental CLI command","allowed_cli":["self-test","once"]}); return 2
    except KeyboardInterrupt:
        _print({"status":"STOPPED","reason":"keyboard_interrupt","bridge_version":BRIDGE_VERSION}); return 130
    except Exception as exc:
        print(json.dumps({"status":"ERROR","error":str(exc),"error_type":type(exc).__name__,"bridge_version":BRIDGE_VERSION}, ensure_ascii=False), file=sys.stderr); return 2

if __name__ == "__main__": raise SystemExit(main())
