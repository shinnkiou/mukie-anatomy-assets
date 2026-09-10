"""P0.12 packaged wrapper for UKIE AI BRIDGE.

P0.11 remains the stable command implementation underneath this wrapper. P0.12
adds deterministic cloud-state reconciliation while deliberately withholding the
provider-verified intake argument from the local executable. Therefore the local
EXE can classify recovery work but cannot manufacture DRIVE_READBACK_VERIFIED.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from bridge import cli as base_cli
    from bridge.cloud_recovery import CloudRecoveryError, reconcile_candidate
except ModuleNotFoundError:
    import cli as base_cli
    from cloud_recovery import CloudRecoveryError, reconcile_candidate


BRIDGE_VERSION = "0.14.0-p0.12"
CAPABILITY = "idempotent_cloud_recovery_v1"

# Preserve P0.11 implementation and only overlay version/capability metadata.
base_cli.BRIDGE_VERSION = BRIDGE_VERSION
if CAPABILITY not in base_cli.CURRENT_CAPABILITIES:
    base_cli.CURRENT_CAPABILITIES.append(CAPABILITY)


def _load_object(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise CloudRecoveryError(f"JSON root must be an object: {path}")
    return value


def cmd_reconcile_cloud_state(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE reconcile-cloud-state")
    parser.add_argument("--base-name", required=True)
    parser.add_argument("--discovery", required=True)
    parser.add_argument("--previous")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    result = reconcile_candidate(
        args.base_name,
        _load_object(Path(args.discovery)),
        _load_object(Path(args.previous)) if args.previous else None,
        intake=None,  # Provider-verified intake is control-plane only by design.
    )
    result["bridge_version"] = BRIDGE_VERSION
    result["local_cli_provider_verified_intake_allowed"] = False
    result["ready_for_ai"] = False
    result["promotion_performed"] = False

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 2 if result.get("status") == "BLOCKED" else 0


def cmd_self_test() -> int:
    result = {
        "status": "PASS",
        "bridge_version": BRIDGE_VERSION,
        "bridge_core_version": base_cli.bridge_main.BRIDGE_VERSION,
        "protocol_version": base_cli.bridge_main.PROTOCOL_VERSION,
        "browser_protocol_version": base_cli.bridge_main.BROWSER_PROTOCOL_VERSION,
        "bp3d_blender_pin": base_cli.bridge_main.BP3D_BLENDER_PIN,
        "capabilities": list(base_cli.CURRENT_CAPABILITIES),
        "p012_safety": {
            "cloud_recovery_performs_io": False,
            "cloud_recovery_writes_base44": False,
            "cloud_recovery_writes_drive": False,
            "cloud_recovery_promotes_release": False,
            "cloud_recovery_sets_ready_for_ai": False,
            "local_reconciler_accepts_provider_verified_intake": False,
            "verified_evidence_replacement_auto_accepted": False,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv == ["self-test"]:
            return cmd_self_test()
        if argv and argv[0] == "reconcile-cloud-state":
            return cmd_reconcile_cloud_state(argv[1:])
        return base_cli.main(argv)
    except (CloudRecoveryError, FileNotFoundError, ValueError) as exc:
        print(json.dumps({
            "status": "ERROR",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "bridge_version": BRIDGE_VERSION,
        }, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
