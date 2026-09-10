"""Disposable Blender 4.2 GPU render-route probe for UKIE AI BRIDGE.

This script runs only inside a separate factory-startup Blender process. It never
saves preferences or a .blend file. It enumerates Cycles backends, disables CPU
fallback for the chosen probe backend, renders a tiny disposable scene, and emits
JSON evidence. A successful probe proves the Blender render route accepted a
non-CPU device; external hardware-utilization telemetry remains a separate gate.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone

import bpy


BACKEND_ORDER = ("OPTIX", "CUDA", "HIP", "ONEAPI")


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--render-output", required=True)
    return parser.parse_args(argv)


def device_record(device):
    return {
        "name": str(getattr(device, "name", "")),
        "type": str(getattr(device, "type", "")),
        "id": str(getattr(device, "id", "")),
        "use": bool(getattr(device, "use", False)),
    }


def enumerate_backend(prefs, backend):
    try:
        prefs.compute_device_type = backend
        prefs.get_devices()
        devices = [device_record(d) for d in prefs.devices]
        return {"backend": backend, "supported": True, "devices": devices, "error": None}
    except Exception as exc:
        return {"backend": backend, "supported": False, "devices": [], "error": f"{type(exc).__name__}: {exc}"}


def create_probe_scene(scene):
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
    cube = bpy.context.active_object
    cube.name = "UKIE_GPU_PROBE_CUBE"

    bpy.ops.object.light_add(type="AREA", location=(3.0, -3.0, 4.0))
    light = bpy.context.active_object
    light.name = "UKIE_GPU_PROBE_LIGHT"
    light.data.energy = 800.0
    light.data.shape = "DISK"
    light.data.size = 5.0

    bpy.ops.object.camera_add(location=(4.0, -4.0, 3.0))
    camera = bpy.context.active_object
    camera.name = "UKIE_GPU_PROBE_CAMERA"
    direction = cube.location - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera


def main():
    args = parse_args()
    output = os.path.abspath(args.output)
    render_output = os.path.abspath(args.render_output)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    os.makedirs(os.path.dirname(render_output), exist_ok=True)

    result = {
        "schema_version": "ukie_blender_gpu_probe_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "blender_version": bpy.app.version_string,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "status": "GPU_RENDER_ROUTE_NOT_AVAILABLE",
        "backend_attempts": [],
        "chosen_backend": None,
        "selected_devices": [],
        "cpu_devices_disabled": False,
        "scene_cycles_device": None,
        "render": {"attempted": False, "completed": False, "path": render_output, "byte_size": 0},
        "hardware_utilization_sampled": False,
        "ready_for_gpu_render": False,
    }

    addon = bpy.context.preferences.addons.get("cycles")
    if addon is None:
        result["error"] = "Cycles addon is unavailable"
    else:
        prefs = addon.preferences
        chosen = None
        for backend in BACKEND_ORDER:
            attempt = enumerate_backend(prefs, backend)
            result["backend_attempts"].append(attempt)
            non_cpu = [d for d in attempt["devices"] if d["type"].upper() != "CPU"]
            if attempt["supported"] and non_cpu:
                chosen = backend
                break

        if chosen is None:
            result["error"] = "No non-CPU Cycles compute device was enumerated"
        else:
            prefs.compute_device_type = chosen
            prefs.get_devices()
            selected = []
            cpu_seen = False
            cpu_disabled = True
            for device in prefs.devices:
                dtype = str(getattr(device, "type", "")).upper()
                if dtype == "CPU":
                    cpu_seen = True
                    device.use = False
                    cpu_disabled = cpu_disabled and (not bool(device.use))
                else:
                    device.use = True
                    selected.append(device_record(device))

            result["chosen_backend"] = chosen
            result["selected_devices"] = selected
            result["cpu_devices_disabled"] = bool((not cpu_seen) or cpu_disabled)

            scene = bpy.context.scene
            create_probe_scene(scene)
            scene.render.engine = "CYCLES"
            scene.cycles.device = "GPU"
            scene.cycles.samples = 1
            scene.render.resolution_x = 96
            scene.render.resolution_y = 96
            scene.render.resolution_percentage = 100
            scene.render.image_settings.file_format = "PNG"
            scene.render.filepath = render_output
            result["scene_cycles_device"] = str(scene.cycles.device)
            result["render"]["attempted"] = True

            try:
                bpy.ops.render.render(write_still=True)
                size = os.path.getsize(render_output) if os.path.isfile(render_output) else 0
                result["render"]["completed"] = bool(size >= 1024)
                result["render"]["byte_size"] = int(size)
                if selected and result["cpu_devices_disabled"] and result["render"]["completed"]:
                    result["status"] = "GPU_RENDER_ROUTE_PASS"
                    result["ready_for_gpu_render"] = True
            except Exception as exc:
                result["error"] = f"render failed: {type(exc).__name__}: {exc}"

    with open(output, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    print(
        "UKIE_GPU_PROBE "
        f"status={result['status']} backend={result.get('chosen_backend')} "
        f"selected={len(result.get('selected_devices', []))}"
    )


if __name__ == "__main__":
    main()
