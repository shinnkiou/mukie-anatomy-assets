"""Build a synthetic P0.9 physical-acceptance ZIP for verifier CI only.

The bundle deliberately marks itself synthetic_ci_only. Production CLI must reject
it as physical evidence; unit/CI code may opt in to validate the verifier path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import tempfile
import zlib
import zipfile


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def fake_png(width=128, height=128) -> bytes:
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(((x * 17 + y * 3) & 255, (x * 5 + y * 19) & 255, (x ^ y) & 255, 255))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    comment = b"UKIE_SYNTHETIC_CI_ONLY\x00" + bytes((i * 73) & 255 for i in range(1400))
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"tEXt", comment)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )


def build_canary_bytes() -> tuple[bytes, str, str]:
    canary_id = "BLENDER_CANARY_CI_SYNTHETIC"
    job_id = "CANARY_JOB_CI_SYNTHETIC"
    root = pathlib.PurePosixPath(canary_id)
    source = b"UKIE_SYNTHETIC_CANARY_SOURCE" * 64
    source_sha = hashlib.sha256(source).hexdigest()
    manifest = {
        "schema_version": "ukie_blender_canary_v1",
        "canary_id": canary_id,
        "job_id": job_id,
        "status": "CANARY_LOCAL_PASS",
        "source": {
            "name": "canary_source.blend",
            "byte_size": len(source),
            "sha256": source_sha,
            "unchanged_after_analysis": True,
        },
        "exact_once": {"decision": "LOCAL_SAVED", "executed": True},
        "semantic_verification": {
            "status": "PASS",
            "vertices": 8,
            "polygons": 6,
            "blender_version": "4.2.23 LTS / SYNTHETIC_CI_ONLY",
        },
        "previews": {"front": True, "side": True},
        "ready_for_ai": False,
        "synthetic_ci_only": True,
    }
    scene = {
        "schema_version": "ukie_scene_report_v1",
        "objects": [{
            "name": "UKIE_CANARY_CUBE",
            "type": "MESH",
            "mesh": {"vertices": 8, "polygons": 6},
        }],
    }
    job_manifest = {
        "schema_version": "ukie_job_manifest_v2",
        "job_id": job_id,
        "status": "LOCAL_SAVED",
        "source": {"source_unchanged": True},
        "artifact_validation": {"status": "PASS"},
    }

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        temp_path = pathlib.Path(tmp.name)
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(str(root / "canary_manifest.json"), json.dumps(manifest))
            zf.writestr(str(root / "canary_source.blend"), source)
            jr = root / "jobs" / job_id
            zf.writestr(str(jr / "manifest.json"), json.dumps(job_manifest))
            zf.writestr(str(jr / "scene_before.json"), json.dumps(scene))
            zf.writestr(str(jr / "preview_front.png"), fake_png())
            zf.writestr(str(jr / "preview_side.png"), fake_png())
        return temp_path.read_bytes(), canary_id, job_id
    finally:
        temp_path.unlink(missing_ok=True)


def _artifact(data: bytes, name: str) -> dict:
    return {"name": name, "byte_size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def build_bundle(output: pathlib.Path) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    acceptance_id = "PHYSICAL_ACCEPTANCE_CI_SYNTHETIC"
    root = pathlib.PurePosixPath(acceptance_id)
    canary_bytes, canary_id, _ = build_canary_bytes()
    canary_name = f"{canary_id}.zip"
    canary_sha = hashlib.sha256(canary_bytes).hexdigest()

    gpu_report = {
        "schema_version": "ukie_blender_gpu_probe_v1",
        "status": "GPU_RENDER_ROUTE_PASS",
        "chosen_backend": "CUDA",
        "selected_devices": [{"name": "Synthetic GPU", "type": "CUDA", "use": True}],
        "cpu_devices_disabled": True,
        "scene_cycles_device": "GPU",
        "render": {"completed": True, "byte_size": 4096},
        "ready_for_gpu_render": True,
        "hardware_utilization_sampled": False,
        "blender_version": "Blender 4.2.23 LTS / SYNTHETIC_CI_ONLY",
    }
    gpu_report_bytes = json.dumps(gpu_report).encode("utf-8")
    gpu_png = fake_png()

    release = {
        "schema_version": "ukie_bridge_release_info_v1",
        "release_key": "BRIDGE_P09_RUN_99999999999",
        "bridge_version": "0.11.0-p0.9",
        "commit_sha": "a" * 40,
        "workflow_run_id": 99999999999,
        "bp3d_blender_pin": "4.2.23",
        "channel": "FOUNDATION",
    }
    device = {
        "schema_version": "ukie_device_status_v1",
        "platform": {"system": "Windows", "machine": "AMD64"},
        "memory": {"supported": True, "total_bytes": 16 * 1024**3},
        "blender": {
            "found": True,
            "version_line": "Blender 4.2.23 LTS / SYNTHETIC_CI_ONLY",
            "path": "C:/Synthetic/Blender/blender.exe",
        },
    }
    artifacts = {
        "canary_bundle": _artifact(canary_bytes, canary_name),
        "gpu_probe.json": _artifact(gpu_report_bytes, "gpu_probe.json"),
        "gpu_probe.png": _artifact(gpu_png, "gpu_probe.png"),
    }
    manifest = {
        "schema_version": "ukie_physical_acceptance_v1",
        "acceptance_id": acceptance_id,
        "started_at": "2026-09-10T00:00:00+00:00",
        "completed_at": "2026-09-10T00:00:01+00:00",
        "status": "CORE_PASS_GPU_PASS",
        "release": release,
        "release_binding_status": "BOUND",
        "device": {"platform": device["platform"], "memory": device["memory"], "blender": device["blender"]},
        "core": {
            "status": "CORE_LOCAL_PASS",
            "canary": {
                "canary_id": canary_id,
                "status": "CANARY_LOCAL_PASS",
                "bundle": {"path": f"C:/Synthetic/{canary_name}", "byte_size": len(canary_bytes), "sha256": canary_sha},
            },
        },
        "gpu": {"status": "GPU_ROUTE_PASS", "result": {"ready_for_gpu_render": True}},
        "artifacts": artifacts,
        "ready_for_ai": False,
        "promotion_performed": False,
        "upload_performed": False,
        "local_core_ready": True,
        "local_gpu_render_ready": True,
        "next_gate": "DRIVE_UPLOAD_READBACK_THEN_ACCEPTANCE_VERIFICATION_AND_RELEASE_GATE",
        "metadata": {"synthetic_ci_only": True},
    }

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(str(root / "physical_acceptance_manifest.json"), json.dumps(manifest))
        zf.writestr(str(root / "device_status.json"), json.dumps(device))
        ev = root / "evidence"
        zf.writestr(str(ev / canary_name), canary_bytes)
        zf.writestr(str(ev / "gpu_probe.json"), gpu_report_bytes)
        zf.writestr(str(ev / "gpu_probe.png"), gpu_png)

    return hashlib.sha256(output.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = pathlib.Path(args.output)
    print(build_bundle(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
