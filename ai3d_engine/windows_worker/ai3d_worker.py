# SPDX-License-Identifier: MIT
"""NEVER TEAR AI3D Windows Worker canary.

This is intentionally a separate companion process to UKIE AI BRIDGE P0.18.2.
It reuses the already-paired DPAPI-protected worker credential, but has its own
transport endpoint and a one-action allowlist. It never executes arbitrary
cloud commands, scripts, executables, URLs, or filesystem paths.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from ctypes import wintypes
from pathlib import Path
from typing import Any

WORKER_VERSION = "0.1.0-ai3d-canary"
PROTOCOL = "never-tear-ai3d-worker-v1"
EDGE_URL = "https://vbuokbwglauibabinaqs.supabase.co/functions/v1/ai3d-worker-transport-canary"
ALLOWED_ACTIONS = frozenset({"ai3d_blender_physical_mvp_v1"})
POLL_SECONDS = 10
HEARTBEAT_SECONDS = 20
RENDER_TIMEOUT_SECONDS = 300
MAX_JSON_RESPONSE = 1024 * 1024
MAX_PNG_BYTES = 8 * 1024 * 1024
HEX64 = set("0123456789abcdef")


class WorkerError(RuntimeError):
    pass


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _blob_from_bytes(data: bytes) -> tuple[DATA_BLOB, Any]:
    buf = (ctypes.c_ubyte * len(data))(*data)
    return DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))), buf


def _bytes_from_blob(blob: DATA_BLOB) -> bytes:
    return ctypes.string_at(blob.pbData, blob.cbData) if blob.pbData and blob.cbData else b""


def unprotect_secret(encoded: str) -> str:
    if os.name != "nt":
        raise WorkerError("DPAPI credentials require Windows")
    try:
        protected = base64.b64decode(encoded.encode("ascii"), validate=True)
    except Exception as exc:
        raise WorkerError("credential protected token is invalid") from exc
    in_blob, keepalive = _blob_from_bytes(protected)
    out_blob = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    ok = crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob))
    _ = keepalive
    if not ok:
        raise WorkerError(f"CryptUnprotectData failed: {ctypes.GetLastError()}")
    try:
        return _bytes_from_blob(out_blob).decode("utf-8")
    finally:
        if out_blob.pbData:
            kernel32.LocalFree(out_blob.pbData)


def credential_path() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "UKIE_AI_BRIDGE" / "worker" / "credential.json"


def load_existing_credential() -> dict[str, str]:
    path = credential_path()
    if not path.is_file():
        raise WorkerError(f"paired UKIE worker credential not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise WorkerError("paired credential is unreadable") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "ukie_worker_credential_v1":
        raise WorkerError("unsupported paired credential schema")
    device_key = str(value.get("device_key") or "")
    protected = str(value.get("protected_device_token") or "")
    if len(device_key) < 8 or not protected:
        raise WorkerError("paired credential is incomplete")
    token = unprotect_secret(protected)
    if len(token) < 48:
        raise WorkerError("paired credential token is too short")
    return {"device_key": device_key, "device_token": token}


def app_root() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "UKIE_AI_BRIDGE" / "ai3d"
    root.mkdir(parents=True, exist_ok=True)
    return root


def bundled_file(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    path = base / name
    if not path.is_file():
        raise WorkerError(f"bundled file missing: {name}")
    return path


def discover_blender() -> Path:
    candidates: list[Path] = []
    found = shutil.which("blender")
    if found:
        candidates.append(Path(found))
    for env_name in ("ProgramFiles", "ProgramW6432"):
        root = os.environ.get(env_name)
        if not root:
            continue
        foundation = Path(root) / "Blender Foundation"
        if foundation.is_dir():
            candidates.extend(sorted(foundation.glob("Blender */blender.exe"), reverse=True))
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_file() and candidate.name.lower() in {"blender.exe", "blender"}:
            return candidate.resolve()
    raise WorkerError("Blender executable not found in PATH or standard Blender Foundation install folders")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_hex64(value: str) -> bool:
    return len(value) == 64 and all(ch in HEX64 for ch in value.lower())


def sanitize_plan(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WorkerError("cloud plan must be an object")
    allowed_top = {"object", "camera", "render"}
    if set(value) - allowed_top:
        raise WorkerError("cloud plan contains non-contract keys")
    obj = value.get("object")
    camera = value.get("camera")
    render = value.get("render")
    if not isinstance(obj, dict) or not isinstance(camera, dict) or not isinstance(render, dict):
        raise WorkerError("cloud plan sections missing")
    if set(obj) - {"name", "kind", "size", "position", "rotation", "material"}:
        raise WorkerError("object contains non-contract keys")
    if set(camera) - {"position", "target", "lens_mm"}:
        raise WorkerError("camera contains non-contract keys")
    if set(render) - {"width", "height", "engine", "output_format", "color_mode"}:
        raise WorkerError("render contains non-contract keys")
    material = obj.get("material")
    if not isinstance(material, dict) or set(material) - {"color_srgb", "roughness", "metallic"}:
        raise WorkerError("material contains non-contract keys")
    # The server already range-checks values. This local copy rejects type-shape drift
    # and, critically, any path/URL/script/command field before writing plan.json.
    for key in ("size", "position", "rotation"):
        if not isinstance(obj.get(key), list) or len(obj[key]) != 3:
            raise WorkerError(f"object.{key} must be vec3")
        if not all(isinstance(n, (int, float)) and not isinstance(n, bool) for n in obj[key]):
            raise WorkerError(f"object.{key} must be numeric")
    for key in ("position", "target"):
        if not isinstance(camera.get(key), list) or len(camera[key]) != 3:
            raise WorkerError(f"camera.{key} must be vec3")
    if obj.get("name") != "MVP_Physical_Box" or obj.get("kind") != "box":
        raise WorkerError("object identity/kind rejected")
    if render.get("engine") != "BLENDER_EEVEE_NEXT" or render.get("output_format") != "PNG" or render.get("color_mode") != "RGBA":
        raise WorkerError("render contract rejected")
    return json.loads(json.dumps(value))


def auth_headers(credential: dict[str, str]) -> dict[str, str]:
    return {
        "x-ukie-device-key": credential["device_key"],
        "x-ukie-device-token": credential["device_token"],
        "User-Agent": f"NEVER-TEAR-AI3D-Worker/{WORKER_VERSION}",
    }


def request_json(credential: dict[str, str], payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {**auth_headers(credential), "Content-Type": "application/json"}
    req = urllib.request.Request(EDGE_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(MAX_JSON_RESPONSE + 1)
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_JSON_RESPONSE + 1)
        try:
            detail = json.loads(raw.decode("utf-8", "replace"))
        except Exception:
            detail = {"error": f"http_{exc.code}"}
        raise WorkerError(f"transport HTTP {exc.code}: {detail}") from exc
    except OSError as exc:
        raise WorkerError(f"transport unavailable: {exc}") from exc
    if len(raw) > MAX_JSON_RESPONSE:
        raise WorkerError("transport response too large")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise WorkerError("transport response is not an object")
    return value


def heartbeat(credential: dict[str, str], job: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action": "heartbeat",
        "ai3d_worker_version": WORKER_VERSION,
        "capabilities": sorted(ALLOWED_ACTIONS),
    }
    if job:
        payload["job_id"] = job["id"]
        payload["lease_owner"] = job["lease_owner"]
    return request_json(credential, payload)


def claim(credential: dict[str, str]) -> dict[str, Any] | None:
    response = request_json(credential, {
        "action": "claim",
        "ai3d_worker_version": WORKER_VERSION,
        "capabilities": sorted(ALLOWED_ACTIONS),
    })
    if response.get("status") == "NO_JOB":
        return None
    if response.get("status") != "CLAIMED" or not isinstance(response.get("job"), dict):
        raise WorkerError(f"unexpected claim response: {response.get('status')}")
    job = response["job"]
    if job.get("action") not in ALLOWED_ACTIONS:
        raise WorkerError("server returned non-allowlisted action")
    job["plan"] = sanitize_plan(job.get("plan"))
    return job


def upload_png(credential: dict[str, str], job: dict[str, Any], png_path: Path, png_sha: str) -> dict[str, Any]:
    size = png_path.stat().st_size
    if size <= 0 or size > MAX_PNG_BYTES:
        raise WorkerError("PNG size outside worker contract")
    data = png_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != png_sha:
        raise WorkerError("local PNG hash changed before upload")
    headers = {
        **auth_headers(credential),
        "Content-Type": "image/png",
        "Content-Length": str(len(data)),
        "x-ai3d-job-id": str(job["id"]),
        "x-ai3d-lease-owner": str(job["lease_owner"]),
        "x-ai3d-png-sha256": png_sha,
    }
    req = urllib.request.Request(EDGE_URL, data=data, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read(MAX_JSON_RESPONSE + 1)
    except urllib.error.HTTPError as exc:
        detail = exc.read(MAX_JSON_RESPONSE).decode("utf-8", "replace")
        raise WorkerError(f"artifact upload HTTP {exc.code}: {detail}") from exc
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict) or value.get("status") != "ARTIFACT_READBACK_PASS":
        raise WorkerError("provider artifact readback did not pass")
    if value.get("png_sha256") != png_sha or value.get("readback_sha256") != png_sha:
        raise WorkerError("provider artifact hash mismatch")
    return value


def complete_pass(credential: dict[str, str], job: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return request_json(credential, {
        "action": "complete",
        "job_id": job["id"],
        "lease_owner": job["lease_owner"],
        "outcome": "PASS",
        "result": {
            "raw_pixel_sha256": result["raw_pixel_sha256"],
            "png_sha256": result["png_sha256"],
            "checkpoint_id": result["checkpoint_id"],
            "checkpoint_sha256": result["checkpoint_sha256"],
            "renderer": result["renderer"],
            "blender_version": result["blender_version"],
            "width": result["width"],
            "height": result["height"],
            "automated_qa": "PASS",
            "visual_qa": "PENDING",
        },
    })


def complete_fail(credential: dict[str, str], job: dict[str, Any], error_code: str, message: str) -> None:
    try:
        request_json(credential, {
            "action": "complete",
            "job_id": job["id"],
            "lease_owner": job["lease_owner"],
            "outcome": "FAIL",
            "error_code": error_code[:120],
            "error_message": message[:1000],
        })
    except Exception:
        pass


def validate_result(job_dir: Path) -> tuple[dict[str, Any], Path]:
    result_path = job_dir / "result.json"
    png_path = job_dir / "ai3d_physical_mvp.png"
    if not result_path.is_file() or not png_path.is_file():
        raise WorkerError("Blender evidence files missing")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict) or result.get("schema_version") != "never-tear-ai3d-worker-render-v1":
        raise WorkerError("Blender result schema rejected")
    if result.get("action") != "ai3d_blender_physical_mvp_v1" or result.get("status") != "PASS":
        raise WorkerError("Blender automated QA did not pass")
    if result.get("visual_qa") != "PENDING" or result.get("canary_promoted") is not False:
        raise WorkerError("Blender result violated canary boundary")
    for key in ("png_sha256", "raw_pixel_sha256", "checkpoint_sha256"):
        if not is_hex64(str(result.get(key, ""))):
            raise WorkerError(f"invalid {key}")
    if sha256_file(png_path) != result["png_sha256"]:
        raise WorkerError("local PNG readback SHA mismatch")
    if png_path.stat().st_size > MAX_PNG_BYTES:
        raise WorkerError("local PNG exceeds upload contract")
    return result, png_path


def run_blender_job(credential: dict[str, str], job: dict[str, Any], job_dir: Path) -> tuple[dict[str, Any], Path]:
    existing_result = job_dir / "result.json"
    existing_png = job_dir / "ai3d_physical_mvp.png"
    if existing_result.is_file() and existing_png.is_file():
        try:
            return validate_result(job_dir)
        except Exception:
            # Failed partial evidence is never trusted; overwrite only within this
            # command-id-derived worker-owned directory.
            pass

    job_dir.mkdir(parents=True, exist_ok=True)
    plan_path = job_dir / "plan.json"
    plan_path.write_text(json.dumps(sanitize_plan(job["plan"]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    blender = discover_blender()
    script = bundled_file("blender_physical_mvp.py")
    command = [
        str(blender),
        "--factory-startup",
        "--background",
        "--python",
        str(script),
        "--",
        "--plan",
        str(plan_path),
        "--output",
        str(job_dir),
    ]
    stdout_path = job_dir / "blender.stdout.log"
    stderr_path = job_dir / "blender.stderr.log"
    started = time.monotonic()
    next_heartbeat = started + HEARTBEAT_SECONDS
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        proc = subprocess.Popen(command, stdout=stdout, stderr=stderr, shell=False, cwd=str(job_dir))
        while proc.poll() is None:
            now = time.monotonic()
            if now - started > RENDER_TIMEOUT_SECONDS:
                proc.kill()
                proc.wait(timeout=10)
                raise WorkerError("Blender render timeout")
            if now >= next_heartbeat:
                heartbeat(credential, job)
                next_heartbeat = now + HEARTBEAT_SECONDS
            time.sleep(1.0)
        if proc.returncode != 0:
            raise WorkerError(f"Blender exited with code {proc.returncode}")
    heartbeat(credential, job)
    return validate_result(job_dir)


def command_dir(command_id: str) -> Path:
    digest = hashlib.sha256(command_id.encode("utf-8")).hexdigest()[:24]
    path = app_root() / "jobs" / digest
    path.mkdir(parents=True, exist_ok=True)
    return path


def receipt_path(command_id: str) -> Path:
    digest = hashlib.sha256(command_id.encode("utf-8")).hexdigest()
    root = app_root() / "receipts"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{digest}.json"


def process_job(credential: dict[str, str], job: dict[str, Any]) -> None:
    command_id = str(job.get("command_id") or "")
    if len(command_id) < 8:
        raise WorkerError("command_id invalid")
    if job.get("action") != "ai3d_blender_physical_mvp_v1":
        raise WorkerError("action rejected")
    job_dir = command_dir(command_id)
    result, png_path = run_blender_job(credential, job, job_dir)
    upload = upload_png(credential, job, png_path, result["png_sha256"])
    response = complete_pass(credential, job, result)
    if response.get("status") != "CANARY_AUTOMATED_PASS_VISUAL_PENDING":
        raise WorkerError(f"unexpected completion status: {response.get('status')}")
    receipt = {
        "schema_version": "never-tear-ai3d-worker-receipt-v1",
        "command_id": command_id,
        "job_key": job.get("job_key"),
        "status": response.get("status"),
        "artifact_id": upload.get("artifact_id"),
        "png_sha256": result["png_sha256"],
        "checkpoint_id": result["checkpoint_id"],
        "local_job_dir": str(job_dir),
    }
    receipt_path(command_id).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


def run_cycle(credential: dict[str, str]) -> bool:
    heartbeat(credential)
    job = claim(credential)
    if not job:
        return False
    try:
        process_job(credential, job)
    except Exception as exc:
        complete_fail(credential, job, "AI3D_WORKER_EXECUTION_FAILED", str(exc))
        raise
    return True


def self_test() -> int:
    failures: list[str] = []
    if ALLOWED_ACTIONS != frozenset({"ai3d_blender_physical_mvp_v1"}):
        failures.append("allowlist widened")
    if not EDGE_URL.endswith("/ai3d-worker-transport-canary"):
        failures.append("unexpected endpoint")
    valid = {
        "object": {"name": "MVP_Physical_Box", "kind": "box", "size": [1.8, 1.2, 1.4], "position": [1, 0.6, -2], "rotation": [0, 0.35, 0], "material": {"color_srgb": "#7c8792", "roughness": 0.42, "metallic": 0.12}},
        "camera": {"position": [6.5, 4.2, 7.5], "target": [1, 0.6, -2], "lens_mm": 50},
        "render": {"width": 960, "height": 540, "engine": "BLENDER_EEVEE_NEXT", "output_format": "PNG", "color_mode": "RGBA"},
    }
    try:
        sanitize_plan(valid)
    except Exception as exc:
        failures.append(f"valid plan rejected: {exc}")
    for bad_key, bad_value in (
        ("command", "powershell -enc ..."),
        ("script", "import os"),
        ("path", "C:/Windows/System32"),
        ("url", "https://example.invalid/payload"),
        ("executable", "cmd.exe"),
    ):
        candidate = json.loads(json.dumps(valid))
        candidate[bad_key] = bad_value
        try:
            sanitize_plan(candidate)
            failures.append(f"dangerous field accepted: {bad_key}")
        except WorkerError:
            pass
    if "shell=False" not in Path(__file__).read_text(encoding="utf-8"):
        failures.append("subprocess shell=False marker missing")
    result = {
        "schema_version": "never-tear-ai3d-worker-selftest-v1",
        "worker_version": WORKER_VERSION,
        "protocol": PROTOCOL,
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "arbitrary_shell": False,
        "cloud_filesystem_paths": False,
        "uses_existing_dpapi_pairing": True,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0 if not failures else 23


def main() -> int:
    parser = argparse.ArgumentParser(description="NEVER TEAR AI3D allowlisted Windows Worker canary")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--once", action="store_true", help="heartbeat + at most one claimed job")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    credential = load_existing_credential()
    if args.once:
        run_cycle(credential)
        return 0
    print(f"NEVER TEAR AI3D Worker {WORKER_VERSION} online", flush=True)
    while True:
        try:
            did_work = run_cycle(credential)
            if did_work:
                continue
        except KeyboardInterrupt:
            return 130
        except Exception as exc:
            print(f"AI3D_WORKER_ERROR: {exc}", file=sys.stderr, flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
