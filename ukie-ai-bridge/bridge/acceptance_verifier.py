"""Offline verification for UKIE AI BRIDGE physical acceptance bundles.

The outer acceptance ZIP is untrusted until this module validates archive safety,
release binding, local-only invariants, Windows/Blender identity, the embedded
physical canary bundle, and capability-scoped GPU evidence. No evidence is
executed. Nested evidence bytes are copied only into a private temporary directory
for existing offline verifiers and are deleted automatically.
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from .canary_verifier import CanaryVerificationError, verify_canary_bundle
    from .gpu_probe import GPUProbeError, verify_gpu_report
except ImportError:
    from canary_verifier import CanaryVerificationError, verify_canary_bundle
    from gpu_probe import GPUProbeError, verify_gpu_report


ACCEPTANCE_SCHEMA = "ukie_physical_acceptance_v1"
RELEASE_INFO_SCHEMA = "ukie_bridge_release_info_v1"
VERIFICATION_SCHEMA = "ukie_physical_acceptance_verification_v1"
BLENDER_PIN = "4.2.23"
HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
MAX_FILES = 512
MAX_TOTAL_UNCOMPRESSED = 1536 * 1024 * 1024
MAX_SINGLE_UNCOMPRESSED = 768 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250.0
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
FINAL_STATUSES = {"CORE_FAILED", "CORE_PASS_GPU_BLOCKED", "CORE_PASS_GPU_PASS"}


class AcceptanceVerificationError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_member_name(name: str) -> PurePosixPath:
    if not name or "\\" in name:
        raise AcceptanceVerificationError("archive contains an invalid member name")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise AcceptanceVerificationError(f"unsafe archive member path: {name}")
    return path


def _validate_archive_shape(zf: zipfile.ZipFile) -> dict[str, Any]:
    infos = zf.infolist()
    if not infos or len(infos) > MAX_FILES:
        raise AcceptanceVerificationError("acceptance archive file count is outside the allowed range")
    total = 0
    for info in infos:
        _safe_member_name(info.filename)
        if info.is_dir():
            continue
        if info.file_size < 0 or info.file_size > MAX_SINGLE_UNCOMPRESSED:
            raise AcceptanceVerificationError(f"acceptance archive member is too large: {info.filename}")
        total += info.file_size
        if total > MAX_TOTAL_UNCOMPRESSED:
            raise AcceptanceVerificationError("acceptance archive uncompressed size exceeds the safety cap")
        ratio = info.file_size / max(1, info.compress_size)
        if info.file_size > 1024 * 1024 and ratio > MAX_COMPRESSION_RATIO:
            raise AcceptanceVerificationError(f"suspicious compression ratio: {info.filename}")
    return {"file_count": len(infos), "total_uncompressed_bytes": int(total)}


def _read_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcceptanceVerificationError(f"invalid JSON {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise AcceptanceVerificationError(f"JSON {label} must be an object")
    return value


def _read_json(zf: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        data = zf.read(name)
    except KeyError as exc:
        raise AcceptanceVerificationError(f"missing JSON member: {name}") from exc
    return _read_json_bytes(data, name)


def _valid_release_info(value: Any) -> dict[str, Any]:
    info = value if isinstance(value, dict) else {}
    if info.get("schema_version") != RELEASE_INFO_SCHEMA:
        raise AcceptanceVerificationError("acceptance release binding schema is missing or unsupported")
    release_key = info.get("release_key")
    bridge_version = info.get("bridge_version")
    commit_sha = info.get("commit_sha")
    workflow_run_id = info.get("workflow_run_id")
    if not isinstance(release_key, str) or not release_key.startswith("BRIDGE_P"):
        raise AcceptanceVerificationError("acceptance release_key is invalid or unbound")
    if not isinstance(bridge_version, str) or not bridge_version.strip():
        raise AcceptanceVerificationError("acceptance bridge_version is missing")
    if not isinstance(commit_sha, str) or not HEX40.fullmatch(commit_sha):
        raise AcceptanceVerificationError("acceptance commit_sha is invalid")
    if not isinstance(workflow_run_id, int) or isinstance(workflow_run_id, bool) or workflow_run_id <= 0:
        raise AcceptanceVerificationError("acceptance workflow_run_id is invalid")
    if str(info.get("bp3d_blender_pin") or "") != BLENDER_PIN:
        raise AcceptanceVerificationError("acceptance release binding has the wrong Blender pin")
    return info


def _artifact_matches(entry: Any, data: bytes, label: str) -> dict[str, Any]:
    value = entry if isinstance(entry, dict) else {}
    expected_sha = value.get("sha256")
    expected_size = value.get("byte_size")
    actual_sha = sha256_bytes(data)
    if not isinstance(expected_sha, str) or not HEX64.fullmatch(expected_sha):
        raise AcceptanceVerificationError(f"{label} artifact SHA-256 is missing or invalid")
    if actual_sha.lower() != expected_sha.lower():
        raise AcceptanceVerificationError(f"{label} artifact SHA-256 mismatch")
    if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size != len(data):
        raise AcceptanceVerificationError(f"{label} artifact byte size mismatch")
    return {"byte_size": len(data), "sha256": actual_sha}


def _verify_nested_canary(canary_bytes: bytes, outer_manifest: dict[str, Any]) -> dict[str, Any]:
    core = outer_manifest.get("core") if isinstance(outer_manifest.get("core"), dict) else {}
    canary_claim = core.get("canary") if isinstance(core.get("canary"), dict) else {}
    canary_id = canary_claim.get("canary_id")
    bundle_claim = canary_claim.get("bundle") if isinstance(canary_claim.get("bundle"), dict) else {}
    actual_sha = sha256_bytes(canary_bytes)
    if isinstance(bundle_claim.get("sha256"), str) and actual_sha.lower() != bundle_claim["sha256"].lower():
        raise AcceptanceVerificationError("nested canary SHA disagrees with core canary claim")
    if isinstance(bundle_claim.get("byte_size"), int) and bundle_claim["byte_size"] != len(canary_bytes):
        raise AcceptanceVerificationError("nested canary size disagrees with core canary claim")

    with tempfile.TemporaryDirectory(prefix="ukie_acceptance_canary_") as temp:
        nested_path = Path(temp) / "nested_canary.zip"
        nested_path.write_bytes(canary_bytes)
        try:
            verified = verify_canary_bundle(nested_path)
        except CanaryVerificationError as exc:
            raise AcceptanceVerificationError(f"nested canary verification failed: {exc}") from exc

    if canary_id and verified.get("canary_id") != canary_id:
        raise AcceptanceVerificationError("outer acceptance and nested canary IDs disagree")
    if verified.get("status") != "CANARY_EVIDENCE_VALID":
        raise AcceptanceVerificationError("nested canary evidence is not valid")
    return verified


def _verify_gpu(zf: zipfile.ZipFile, root: PurePosixPath, manifest: dict[str, Any], files: set[str]) -> dict[str, Any]:
    gpu = manifest.get("gpu") if isinstance(manifest.get("gpu"), dict) else {}
    gpu_status = gpu.get("status")
    local_ready = manifest.get("local_gpu_render_ready") is True

    if gpu_status == "GPU_ROUTE_PASS":
        if not local_ready:
            raise AcceptanceVerificationError("GPU PASS conflicts with local_gpu_render_ready=false")
        report_name = str(root / "evidence" / "gpu_probe.json")
        render_name = str(root / "evidence" / "gpu_probe.png")
        if report_name not in files or render_name not in files:
            raise AcceptanceVerificationError("GPU PASS is missing report/render evidence")
        report_bytes = zf.read(report_name)
        render_bytes = zf.read(render_name)
        artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
        _artifact_matches(artifacts.get("gpu_probe.json"), report_bytes, "gpu_probe.json")
        _artifact_matches(artifacts.get("gpu_probe.png"), render_bytes, "gpu_probe.png")
        if len(render_bytes) < 1024 or render_bytes[:8] != PNG_SIGNATURE:
            raise AcceptanceVerificationError("GPU render evidence is not a plausible PNG")
        report = _read_json_bytes(report_bytes, report_name)
        with tempfile.TemporaryDirectory(prefix="ukie_acceptance_gpu_") as temp:
            render_path = Path(temp) / "gpu_probe.png"
            render_path.write_bytes(render_bytes)
            try:
                verified = verify_gpu_report(report, render_path)
            except GPUProbeError as exc:
                raise AcceptanceVerificationError(f"GPU report verification failed: {exc}") from exc
        if verified.get("ready_for_gpu_render") is not True:
            raise AcceptanceVerificationError("GPU PASS evidence does not verify a non-CPU render route")
        return verified

    if gpu_status in {"GPU_ROUTE_BLOCKED", "GPU_ROUTE_FAILED"}:
        if local_ready:
            raise AcceptanceVerificationError("blocked GPU status conflicts with local_gpu_render_ready=true")
        return {"status": gpu_status, "ready_for_gpu_render": False}

    if gpu_status == "SKIPPED_CORE_FAILED":
        if local_ready:
            raise AcceptanceVerificationError("skipped GPU status conflicts with local_gpu_render_ready=true")
        return {"status": gpu_status, "ready_for_gpu_render": False}

    raise AcceptanceVerificationError(f"unsupported GPU acceptance status: {gpu_status}")


def verify_acceptance_bundle(
    bundle: str | Path,
    expected_sha256: str | None = None,
    expected_release_key: str | None = None,
    *,
    allow_synthetic_test_fixture: bool = False,
) -> dict[str, Any]:
    path = Path(bundle)
    if not path.is_file() or path.suffix.lower() != ".zip":
        raise AcceptanceVerificationError("acceptance bundle must be an existing .zip file")

    bundle_sha = sha256_file(path)
    if expected_sha256 is not None:
        if not HEX64.fullmatch(expected_sha256):
            raise AcceptanceVerificationError("expected acceptance SHA-256 is invalid")
        if bundle_sha.lower() != expected_sha256.lower():
            raise AcceptanceVerificationError("acceptance SHA-256 does not match expected Drive readback hash")

    try:
        zf = zipfile.ZipFile(path, "r")
    except zipfile.BadZipFile as exc:
        raise AcceptanceVerificationError("acceptance bundle is not a valid ZIP") from exc

    with zf:
        archive = _validate_archive_shape(zf)
        files = {info.filename for info in zf.infolist() if not info.is_dir()}
        manifests = [name for name in files if PurePosixPath(name).name == "physical_acceptance_manifest.json"]
        if len(manifests) != 1:
            raise AcceptanceVerificationError("bundle must contain exactly one physical_acceptance_manifest.json")
        manifest_name = manifests[0]
        root = PurePosixPath(manifest_name).parent
        if str(root) in {"", "."} or not root.name.startswith("PHYSICAL_ACCEPTANCE_"):
            raise AcceptanceVerificationError("acceptance manifest must be inside a PHYSICAL_ACCEPTANCE root")
        manifest = _read_json(zf, manifest_name)
        if manifest.get("schema_version") != ACCEPTANCE_SCHEMA:
            raise AcceptanceVerificationError("unsupported physical acceptance schema")
        if manifest.get("acceptance_id") != root.name:
            raise AcceptanceVerificationError("archive root and acceptance_id disagree")
        if manifest.get("status") not in FINAL_STATUSES:
            raise AcceptanceVerificationError("acceptance manifest is not in a final local state")
        if manifest.get("ready_for_ai") is not False:
            raise AcceptanceVerificationError("local acceptance must not self-promote ready_for_ai")
        if manifest.get("promotion_performed") is not False:
            raise AcceptanceVerificationError("local acceptance must not promote a release")
        if manifest.get("upload_performed") is not False:
            raise AcceptanceVerificationError("local acceptance must not claim cloud upload")

        metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
        synthetic = metadata.get("synthetic_ci_only") is True
        if synthetic and not allow_synthetic_test_fixture:
            raise AcceptanceVerificationError("synthetic CI acceptance cannot verify as physical evidence")

        release = _valid_release_info(manifest.get("release"))
        if manifest.get("release_binding_status") != "BOUND":
            raise AcceptanceVerificationError("acceptance release binding is not BOUND")
        if expected_release_key is not None and release.get("release_key") != expected_release_key:
            raise AcceptanceVerificationError("acceptance release_key does not match expected release")

        device_name = str(root / "device_status.json")
        if device_name not in files:
            raise AcceptanceVerificationError("device_status.json is missing")
        device = _read_json(zf, device_name)
        if device.get("schema_version") != "ukie_device_status_v1":
            raise AcceptanceVerificationError("device status schema is unsupported")
        platform = device.get("platform") if isinstance(device.get("platform"), dict) else {}
        if str(platform.get("system") or "").lower() != "windows":
            raise AcceptanceVerificationError("physical acceptance did not originate from Windows")

        status = manifest.get("status")
        core = manifest.get("core") if isinstance(manifest.get("core"), dict) else {}
        core_pass = status in {"CORE_PASS_GPU_BLOCKED", "CORE_PASS_GPU_PASS"}
        if core_pass:
            if core.get("status") != "CORE_LOCAL_PASS" or manifest.get("local_core_ready") is not True:
                raise AcceptanceVerificationError("core PASS state is internally inconsistent")
            blender = device.get("blender") if isinstance(device.get("blender"), dict) else {}
            if blender.get("found") is not True or BLENDER_PIN not in str(blender.get("version_line") or ""):
                raise AcceptanceVerificationError("core PASS did not prove the pinned Blender version")
            nested = [
                name for name in files
                if PurePosixPath(name).parent == root / "evidence"
                and PurePosixPath(name).name.startswith("BLENDER_CANARY_")
                and PurePosixPath(name).suffix.lower() == ".zip"
            ]
            if len(nested) != 1:
                raise AcceptanceVerificationError("core PASS must contain exactly one embedded canary ZIP")
            canary_bytes = zf.read(nested[0])
            artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
            canary_artifact = _artifact_matches(artifacts.get("canary_bundle"), canary_bytes, "canary_bundle")
            canary_verified = _verify_nested_canary(canary_bytes, manifest)
        else:
            if core.get("status") != "CORE_LOCAL_FAILED" or manifest.get("local_core_ready") is not False:
                raise AcceptanceVerificationError("core FAILED state is internally inconsistent")
            canary_artifact = None
            canary_verified = None

        gpu_verified = _verify_gpu(zf, root, manifest, files)
        if status == "CORE_PASS_GPU_PASS" and gpu_verified.get("ready_for_gpu_render") is not True:
            raise AcceptanceVerificationError("CORE_PASS_GPU_PASS lacks verified GPU evidence")
        if status == "CORE_PASS_GPU_BLOCKED" and gpu_verified.get("ready_for_gpu_render") is True:
            raise AcceptanceVerificationError("GPU blocked acceptance unexpectedly verifies GPU readiness")
        if status == "CORE_FAILED" and (manifest.get("gpu") or {}).get("status") != "SKIPPED_CORE_FAILED":
            raise AcceptanceVerificationError("core failure must skip the GPU probe")

        drive_readback = expected_sha256 is not None
        physical_provenance = not synthetic
        promotion_input_ready = bool(core_pass and drive_readback and physical_provenance)
        if not core_pass:
            next_gate = "INSPECT_CORE_FAILURE_EVIDENCE"
        elif not drive_readback:
            next_gate = "DRIVE_UPLOAD_READBACK"
        elif not physical_provenance:
            next_gate = "SYNTHETIC_TEST_ONLY"
        else:
            next_gate = "REGISTER_CANARY_AND_EVALUATE_RELEASE_PROMOTION"

        return {
            "schema_version": VERIFICATION_SCHEMA,
            "status": "ACCEPTANCE_EVIDENCE_VALID",
            "acceptance_id": manifest.get("acceptance_id"),
            "acceptance_status": status,
            "release": release,
            "archive": archive,
            "bundle": {
                "file_name": path.name,
                "byte_size": path.stat().st_size,
                "sha256": bundle_sha,
                "expected_sha256_matched": drive_readback,
            },
            "device": {
                "system": platform.get("system"),
                "machine": platform.get("machine"),
                "blender": device.get("blender"),
            },
            "core": {
                "ready": core_pass,
                "canary_artifact": canary_artifact,
                "canary_verification": canary_verified,
            },
            "gpu": gpu_verified,
            "synthetic_ci_only": synthetic,
            "physical_provenance": physical_provenance,
            "drive_readback_proven": drive_readback,
            "promotion_input_ready": promotion_input_ready,
            "ready_for_ai": False,
            "mutation_performed": False,
            "next_gate": next_gate,
        }
