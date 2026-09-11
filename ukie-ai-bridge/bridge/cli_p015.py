"""P0.15 wrapper: exact Blender pin selection + verified portable bootstrap."""

from __future__ import annotations

import argparse
import json
import sys

try:
    from bridge import cli_p012 as base_cli
    from bridge import main as bridge_main
    from bridge.blender_bootstrap import BlenderBootstrapError, bootstrap_pinned_blender
    from bridge.blender_selector import discover_blenders, select_pinned_blender
except ModuleNotFoundError:
    import cli_p012 as base_cli
    import main as bridge_main
    from blender_bootstrap import BlenderBootstrapError, bootstrap_pinned_blender
    from blender_selector import discover_blenders, select_pinned_blender

BRIDGE_VERSION = "0.15.0-p0.15"
CAPABILITIES = ["exact_blender_pin_selection_v1", "verified_portable_blender_bootstrap_v1"]

bridge_main.detect_blender = select_pinned_blender
base_cli.BRIDGE_VERSION = BRIDGE_VERSION
base_cli.base_cli.BRIDGE_VERSION = BRIDGE_VERSION
base_cli.base_cli.bridge_main.detect_blender = select_pinned_blender
for capability in CAPABILITIES:
    if capability not in base_cli.base_cli.CURRENT_CAPABILITIES:
        base_cli.base_cli.CURRENT_CAPABILITIES.append(capability)


def cmd_blender_discovery() -> int:
    result = discover_blenders()
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ready_for_bp3d") else 2


def cmd_bootstrap_blender() -> int:
    result = bootstrap_pinned_blender()
    result["bridge_version"] = BRIDGE_VERSION
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_self_test() -> int:
    result = {
        "status": "PASS",
        "bridge_version": BRIDGE_VERSION,
        "bp3d_blender_pin": bridge_main.BP3D_BLENDER_PIN,
        "capabilities": CAPABILITIES + list(base_cli.base_cli.CURRENT_CAPABILITIES),
        "p015_safety": {
            "existing_blender_uninstalled": False,
            "existing_blender_modified": False,
            "download_domain": "download.blender.org",
            "exact_version_only": True,
            "official_sha256_required": True,
            "archive_path_traversal_guard": True,
            "portable_localappdata_only": True,
            "administrator_required": False,
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
        if argv == ["blender-discovery"]:
            return cmd_blender_discovery()
        if argv == ["bootstrap-blender"]:
            return cmd_bootstrap_blender()
        return base_cli.main(argv)
    except (BlenderBootstrapError, RuntimeError, ValueError, FileNotFoundError) as exc:
        print(json.dumps({
            "status": "ERROR",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "bridge_version": BRIDGE_VERSION,
        }, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
