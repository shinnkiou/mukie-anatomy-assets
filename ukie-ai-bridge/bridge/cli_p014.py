"""P0.14 packaged wrapper for UKIE AI BRIDGE.

P0.14 inherits P0.12 cloud recovery and all earlier safety/acceptance functions,
while replacing only first-run handoff configuration with bounded automatic Drive
for desktop discovery plus a durable local-outbox fallback. No local command can
claim Drive readback or promote a release.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from bridge import cli_p012 as inherited_cli
    from bridge import handoff as handoff_base
    from bridge.handoff_auto import configure_handoff_auto, run_acceptance_and_handoff_auto
except ModuleNotFoundError:
    import cli_p012 as inherited_cli
    import handoff as handoff_base
    from handoff_auto import configure_handoff_auto, run_acceptance_and_handoff_auto


BRIDGE_VERSION = "0.14.0-p0.14"
CAPABILITIES = [
    "drive_sync_auto_discovery_v1",
    "local_outbox_fallback_v1",
    "stale_handoff_config_recovery_v1",
    "no_picker_first_run_v1",
]

# Overlay metadata without forking the proven earlier command implementations.
inherited_cli.BRIDGE_VERSION = BRIDGE_VERSION
inherited_cli.base_cli.BRIDGE_VERSION = BRIDGE_VERSION
for capability in CAPABILITIES:
    if capability not in inherited_cli.base_cli.CURRENT_CAPABILITIES:
        inherited_cli.base_cli.CURRENT_CAPABILITIES.append(capability)


def _load_object(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def cmd_configure_handoff(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE configure-handoff")
    parser.add_argument("--destination")
    parser.add_argument("--config")
    args = parser.parse_args(argv)
    result = configure_handoff_auto(
        Path(args.destination) if args.destination else None,
        config_path=Path(args.config) if args.config else None,
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
    result = run_acceptance_and_handoff_auto(
        Path(args.workspace),
        release_info,
        inherited_cli.base_cli.run_physical_acceptance,
        state_root=Path(args.state_root) if args.state_root else None,
        config_path=Path(args.handoff_config) if args.handoff_config else None,
    )
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    acceptance = result.get("acceptance") if isinstance(result.get("acceptance"), dict) else {}
    return 0 if acceptance.get("local_core_ready") is True else 2


def cmd_self_test() -> int:
    result = {
        "status": "PASS",
        "bridge_version": BRIDGE_VERSION,
        "bridge_core_version": inherited_cli.base_cli.bridge_main.BRIDGE_VERSION,
        "protocol_version": inherited_cli.base_cli.bridge_main.PROTOCOL_VERSION,
        "browser_protocol_version": inherited_cli.base_cli.bridge_main.BROWSER_PROTOCOL_VERSION,
        "bp3d_blender_pin": inherited_cli.base_cli.bridge_main.BP3D_BLENDER_PIN,
        "capabilities": list(inherited_cli.base_cli.CURRENT_CAPABILITIES),
        "p014_safety": {
            "whole_disk_recursive_search": False,
            "folder_picker_required": False,
            "auto_discovery_claims_cloud_sync": False,
            "local_outbox_claims_drive_sync": False,
            "local_outbox_claims_drive_readback": False,
            "local_exe_promotes_release": False,
            "source_blend_overwrite": False,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv == ["self-test"]:
            return cmd_self_test()
        if argv and argv[0] == "configure-handoff":
            return cmd_configure_handoff(argv[1:])
        if argv and argv[0] == "acceptance-and-handoff":
            return cmd_acceptance_and_handoff(argv[1:])
        return inherited_cli.main(argv)
    except (handoff_base.HandoffError, FileNotFoundError, RuntimeError, ValueError) as exc:
        print(json.dumps({
            "status": "ERROR",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "bridge_version": BRIDGE_VERSION,
        }, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
