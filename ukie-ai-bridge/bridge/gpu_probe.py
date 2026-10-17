"""Physical Windows + Blender GPU capability probe.

The Windows side inventories display adapters using EnumDisplayDevicesW without
PowerShell. The Blender side launches a separate factory-startup Blender process
that attempts a tiny Cycles render with CPU devices disabled. The result is a
capability report, not a global READY_FOR_AI flag.
"""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
from pathlib import Path
from typing import Any

try:
    from . import main as bridge_main
except ImportError:
    import main as bridge_main


GPU_SCHEMA = "ukie_gpu_capability_v1"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class GPUProbeError(RuntimeError):
    pass


def windows_display_adapters() -> list[dict[str, Any]]:
    if os.name != "nt":
        return []

    class DISPLAY_DEVICEW(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("DeviceName", ctypes.c_wchar * 32),
            ("DeviceString", ctypes.c_wchar * 128),
            ("StateFlags", ctypes.c_ulong),
            ("DeviceID", ctypes.c_wchar * 128),
            ("DeviceKey", ctypes.c_wchar * 128),
        ]

    user32 = ctypes.windll.user32
    adapters: list[dict[str, Any]] = []
    index = 0
    while index < 32:
        dev = DISPLAY_DEVICEW()
        dev.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        ok = user32.EnumDisplayDevicesW(None, index, ctypes.byref(dev), 0)
        if not ok:
            break
        if dev.DeviceString or dev.DeviceID:
            adapters.append({
                "index": index,
                "device_name": str(dev.DeviceName),
                "description": str(dev.DeviceString),
                "device_id": str(dev.DeviceID),
                "state_flags": int(dev.StateFlags),
            })
        index += 1
    return adapters


def _png_file_ok(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 1024:
        return False
    with path.open("rb") as handle:
        return handle.read(8) == PNG_SIGNATURE


def verify_gpu_report(report: dict[str, Any], render_path: Path | None = None) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise GPUProbeError("GPU report must be a JSON object")
    if report.get("schema_version") != "ukie_blender_gpu_probe_v1":
        raise GPUProbeError("unsupported Blender GPU probe schema")

    selected = report.get("selected_devices")
    if not isinstance(selected, list):
        selected = []
    non_cpu = [d for d in selected if isinstance(d, dict) and str(d.get("type", "")).upper() != "CPU"]
    render = report.get("render") if isinstance(report.get("render"), dict) else {}

    checks = {
        "probe_status": report.get("status") == "GPU_RENDER_ROUTE_PASS",
        "non_cpu_selected": len(non_cpu) > 0,
        "cpu_fallback_disabled": report.get("cpu_devices_disabled") is True,
        "scene_cycles_device_gpu": str(report.get("scene_cycles_device", "")).upper() == "GPU",
        "render_completed": render.get("completed") is True and int(render.get("byte_size") or 0) >= 1024,
        "ready_for_gpu_render_claim": report.get("ready_for_gpu_render") is True,
        "hardware_utilization_not_overclaimed": report.get("hardware_utilization_sampled") is False,
    }
    if render_path is not None:
        checks["render_png_present"] = _png_file_ok(render_path)

    passed = all(checks.values())
    return {
        "schema_version": GPU_SCHEMA,
        "status": "GPU_RENDER_ROUTE_VERIFIED" if passed else "GPU_RENDER_ROUTE_BLOCKED",
        "checks": checks,
        "chosen_backend": report.get("chosen_backend"),
        "selected_devices": non_cpu,
        "blender_version": report.get("blender_version"),
        "hardware_utilization_sampled": False,
        "hardware_utilization_gate": "NOT_IMPLEMENTED",
        "ready_for_gpu_render": passed,
        "ready_for_ai_core": None,
        "notes": "This proves Blender accepted a non-CPU Cycles render route with CPU devices disabled. It does not sample VRAM/GPU utilization telemetry.",
    }


def run_gpu_probe(workspace: Path) -> dict[str, Any]:
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    blender = bridge_main.detect_blender()
    if not blender.get("found"):
        raise GPUProbeError(blender.get("error") or "Blender not found")
    version_line = str(blender.get("version_line") or "")
    if bridge_main.BP3D_BLENDER_PIN not in version_line:
        raise GPUProbeError(
            f"BP3D GPU probe requires Blender {bridge_main.BP3D_BLENDER_PIN}; detected {version_line or 'unknown'}"
        )

    script = bridge_main.bundle_root() / "blender" / "gpu_probe.py"
    if not script.is_file():
        raise GPUProbeError(f"bundled gpu probe missing: {script}")

    report_path = workspace / "gpu_probe.json"
    render_path = workspace / "gpu_probe.png"
    stdout_path = workspace / "gpu_probe_stdout.log"
    stderr_path = workspace / "gpu_probe_stderr.log"

    proc = subprocess.run(
        [
            blender["path"],
            "-b",
            "--factory-startup",
            "--python",
            str(script),
            "--",
            "--output",
            str(report_path),
            "--render-output",
            str(render_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    stdout_path.write_text(proc.stdout or "", encoding="utf-8", newline="\n")
    stderr_path.write_text(proc.stderr or "", encoding="utf-8", newline="\n")
    if proc.returncode != 0 or not report_path.is_file():
        raise GPUProbeError(f"Blender GPU probe failed with exit={proc.returncode}")

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GPUProbeError(f"GPU report unreadable: {exc}") from exc

    verified = verify_gpu_report(report, render_path)
    return {
        "schema_version": "ukie_gpu_probe_bundle_v1",
        "status": verified["status"],
        "windows_adapters": windows_display_adapters(),
        "blender": blender,
        "blender_report": report,
        "verification": verified,
        "artifacts": {
            "report": str(report_path),
            "render": str(render_path) if render_path.is_file() else None,
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        },
        "ready_for_gpu_render": verified["ready_for_gpu_render"],
        "ready_for_ai_core": False,
    }
