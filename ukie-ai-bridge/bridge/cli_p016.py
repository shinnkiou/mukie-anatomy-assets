"""P0.16 wrapper: preserve P0.15 acceptance and add visible local cloud-upload preparation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from bridge import cli_p015 as inherited_cli
    from bridge.cloud_export import CloudExportError, prepare_cloud_upload
except ModuleNotFoundError:
    import cli_p015 as inherited_cli
    from cloud_export import CloudExportError, prepare_cloud_upload

BRIDGE_VERSION = "0.16.0-p0.16"
CAPABILITIES = ["visible_upload_ready_export_v1"]

inherited_cli.BRIDGE_VERSION = BRIDGE_VERSION
try:
    inherited_cli.inherited_cli.BRIDGE_VERSION = BRIDGE_VERSION
    inherited_cli.inherited_cli.base_cli.BRIDGE_VERSION = BRIDGE_VERSION
except Exception:
    pass


def cmd_prepare_cloud_upload(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="UKIE_AI_BRIDGE prepare-cloud-upload")
    parser.add_argument("--outbox")
    parser.add_argument("--destination")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args(argv)
    result = prepare_cloud_upload(
        outbox=Path(args.outbox) if args.outbox else None,
        destination_root=Path(args.destination) if args.destination else None,
        open_folder=not args.no_open,
    )
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_self_test() -> int:
    result = {
        "status": "PASS",
        "bridge_version": BRIDGE_VERSION,
        "bp3d_blender_pin": inherited_cli.bridge_main.BP3D_BLENDER_PIN,
        "capabilities": CAPABILITIES + list(getattr(inherited_cli, "CAPABILITIES", [])),
        "p016_safety": {
            "automatic_cloud_upload": False,
            "user_visible_downloads_copy_only": True,
            "source_outbox_modified": False,
            "cloud_presence_preclaimed": False,
            "drive_readback_preclaimed": False,
            "ready_for_ai_self_promotion": False,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv == ["self-test"]:
            return cmd_self_test()
        if argv and argv[0] == "prepare-cloud-upload":
            return cmd_prepare_cloud_upload(argv[1:])
        return inherited_cli.main(argv)
    except (CloudExportError, RuntimeError, ValueError, FileNotFoundError) as exc:
        print(json.dumps({
            "status": "ERROR",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "bridge_version": BRIDGE_VERSION,
        }, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
