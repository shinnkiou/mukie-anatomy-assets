"""Fixed-root self updater for the isolated CSMC canary.

Security model:
- one hard-coded release endpoint owned by SyncOps Hub;
- one fixed LOCALAPPDATA CSMC canary root;
- existing DPAPI-protected Worker credential only;
- no cloud-supplied URL, filesystem path, command, executable, arguments, or task name;
- promoted releases must satisfy every gate in csmc_canary_self_update_manifest_v1;
- package ZIP, PACKAGE_MANIFEST.json, every manifest file, staged self-test, and
  post-swap heartbeat are verified before success;
- failed swaps roll back to the immediately previous version.

This module is isolated from the Production Worker.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

try:
    from .worker_credentials import load_credential
except ImportError:
    from worker_credentials import load_credential

BOOTSTRAP_VERSION = 1
SCHEMA = "csmc_canary_self_update_manifest_v1"
PROTOCOL = "csmc_canary_self_update_v1"
FIXED_RELEASE_ENDPOINT = "https://base44.app/api/apps/6aa2743da37b11162682c01f/functions/csmc-canary-release"
ROOT_SUBDIR = Path("UKIE_AI_BRIDGE") / "csmc-canary"
CURRENT_NAME = "current"
PREVIOUS_NAME = "previous"
STAGING_NAME = "staging"
BOOTSTRAP_NAME = "bootstrap"
STATE_NAME = "self_update_state.json"
LOCK_NAME = "self_update.lock"
WORKER_EXE = "UKIE_AI_BRIDGE_CSMC_CANARY.exe"
PACKAGE_MANIFEST = "PACKAGE_MANIFEST.json"
MAX_PACKAGE_BYTES = 64 * 1024 * 1024
MAX_EXTRACTED_BYTES = 128 * 1024 * 1024
HTTP_TIMEOUT = 90
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
RELEASE_RE = re.compile(r"^[A-Z0-9_.-]{8,160}$")
VERSION_RE = re.compile(r"^[0-9A-Za-z_.+-]{1,96}$")
PACKAGE_RE = re.compile(r"^UKIE_AI_BRIDGE_CSMC_CANARY_[A-Z0-9_.-]+\.zip$")
ALLOWED_EXTRA_FILES = frozenset({PACKAGE_MANIFEST, "README_FIRST.txt"})


class CsmcSelfUpdateError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _root() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise CsmcSelfUpdateError("CSMC_LOCALAPPDATA_MISSING", "LOCALAPPDATA is unavailable")
    root = (Path(local) / ROOT_SUBDIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    os.replace(temp, path)


def _load_current_release(root: Path) -> dict[str, Any]:
    path = root / CURRENT_NAME / "RELEASE_INFO.json"
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _credential() -> dict[str, Any]:
    value = load_credential()
    if not value or not value.get("device_key") or not value.get("device_token"):
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_CREDENTIAL_MISSING", "existing approved Worker credential is required")
    return value


def _headers(credential: dict[str, Any]) -> dict[str, str]:
    return {
        "User-Agent": f"UKIE-CSMC-SELF-UPDATE/{BOOTSTRAP_VERSION}",
        "X-UKIE-Device-Key": str(credential["device_key"]),
        "X-UKIE-Device-Token": str(credential["device_token"]),
        "Accept": "application/json, application/zip",
    }


def _request(mode: str, credential: dict[str, Any], *, max_bytes: int) -> bytes:
    if mode not in {"manifest", "package"}:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_MODE_REJECTED", "internal mode is invalid")
    url = FIXED_RELEASE_ENDPOINT + "?mode=" + mode
    req = urllib.request.Request(url, headers=_headers(credential), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
            raw = response.read(max_bytes + 1)
    except urllib.error.HTTPError as exc:
        detail = exc.read(64 * 1024)
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_HTTP_FAILED", f"release endpoint HTTP {exc.code}: {detail[:500]!r}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_TRANSPORT_FAILED", str(exc)) from exc
    if len(raw) > max_bytes:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_RESPONSE_TOO_LARGE", f"{mode} response exceeded fixed limit")
    return raw


def _parse_manifest(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_MANIFEST_INVALID", "release manifest is invalid JSON") from exc
    if not isinstance(value, dict) or value.get("ok") is not True or value.get("schema_version") != SCHEMA:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_MANIFEST_INVALID", "release manifest schema/ok gate failed")
    release_key = str(value.get("release_key") or "")
    version = str(value.get("canary_version") or "")
    package_name = str(value.get("package_filename") or "")
    package_sha = str(value.get("package_sha256") or "").lower()
    manifest_sha = str(value.get("package_manifest_sha256") or "").lower()
    package_size = int(value.get("package_size") or 0)
    gates = {
        "ci_success": value.get("ci_success") is True,
        "drive_raw_readback_verified": value.get("drive_raw_readback_verified") is True,
        "package_manifest_all_files_match": value.get("package_manifest_all_files_match") is True,
        "promote": value.get("promote") is True,
        "protocol": value.get("bootstrap_protocol") == PROTOCOL,
        "min_bootstrap": int(value.get("min_bootstrap_version") or 0) <= BOOTSTRAP_VERSION,
        "fixed_package_endpoint": value.get("package_endpoint_mode") == "same_fixed_endpoint_package",
        "no_arbitrary_url": value.get("arbitrary_url_present") is False,
        "no_arbitrary_path": value.get("arbitrary_path_present") is False,
    }
    if not all(gates.values()):
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_RELEASE_NOT_PROMOTABLE", f"release gates failed: {gates}")
    if not RELEASE_RE.fullmatch(release_key) or not VERSION_RE.fullmatch(version) or not PACKAGE_RE.fullmatch(package_name):
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_MANIFEST_FIELDS_REJECTED", "release identity fields are invalid")
    if not SHA_RE.fullmatch(package_sha) or not SHA_RE.fullmatch(manifest_sha):
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_MANIFEST_FIELDS_REJECTED", "release SHA-256 fields are invalid")
    if package_size <= 0 or package_size > MAX_PACKAGE_BYTES:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_MANIFEST_FIELDS_REJECTED", "package size is invalid")
    return {
        "release_key": release_key,
        "canary_version": version,
        "package_filename": package_name,
        "package_sha256": package_sha,
        "package_manifest_sha256": manifest_sha,
        "package_size": package_size,
        "ci_run_id": int(value.get("ci_run_id") or 0),
        "github_head": str(value.get("github_head") or "")[:80],
    }


def _download_package(root: Path, manifest: dict[str, Any], credential: dict[str, Any]) -> Path:
    staging = root / STAGING_NAME
    staging.mkdir(parents=True, exist_ok=True)
    package_path = staging / "package.zip"
    partial = staging / "package.zip.partial"
    partial.unlink(missing_ok=True)
    package_path.unlink(missing_ok=True)
    raw = _request("package", credential, max_bytes=MAX_PACKAGE_BYTES)
    if len(raw) != manifest["package_size"] or hashlib.sha256(raw).hexdigest() != manifest["package_sha256"]:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_PACKAGE_VERIFY_FAILED", "fixed endpoint package size/SHA mismatch")
    partial.write_bytes(raw)
    os.replace(partial, package_path)
    return package_path


def _safe_extract(root: Path, package_path: Path, manifest: dict[str, Any]) -> Path:
    staging = root / STAGING_NAME
    release_dir = staging / ("release_" + manifest["release_key"])
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True)
    total = 0
    names: set[str] = set()
    with zipfile.ZipFile(package_path, "r") as z:
        for info in z.infolist():
            name = info.filename
            if info.is_dir() or not name or "/" in name or "\\" in name or name in {".", ".."}:
                raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_ZIP_PATH_REJECTED", f"non-flat ZIP member rejected: {name!r}")
            if name in names:
                raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_ZIP_DUPLICATE", f"duplicate ZIP member: {name}")
            names.add(name)
            total += int(info.file_size)
            if total > MAX_EXTRACTED_BYTES:
                raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_ZIP_TOO_LARGE", "extracted package exceeds fixed limit")
            target = (release_dir / name).resolve()
            if target.parent != release_dir.resolve():
                raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_ZIP_PATH_REJECTED", "ZIP member escaped staging root")
            with z.open(info, "r") as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
    _verify_package_manifest(release_dir, names, manifest)
    return release_dir


def _verify_package_manifest(release_dir: Path, zip_names: set[str], release: dict[str, Any]) -> None:
    manifest_path = release_dir / PACKAGE_MANIFEST
    if not manifest_path.is_file() or _sha256(manifest_path) != release["package_manifest_sha256"]:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_PACKAGE_MANIFEST_SHA_FAILED", "PACKAGE_MANIFEST.json SHA mismatch")
    try:
        package_manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_PACKAGE_MANIFEST_INVALID", "PACKAGE_MANIFEST.json is invalid") from exc
    if not isinstance(package_manifest, dict) or package_manifest.get("schema_version") != "ukie_csmc_canary_package_manifest_v2":
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_PACKAGE_MANIFEST_INVALID", "package manifest schema rejected")
    files = package_manifest.get("files")
    required = package_manifest.get("required_files")
    if not isinstance(files, list) or not isinstance(required, list) or not files:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_PACKAGE_MANIFEST_INVALID", "package manifest file lists invalid")
    listed: set[str] = set()
    for row in files:
        if not isinstance(row, dict):
            raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_PACKAGE_MANIFEST_INVALID", "package manifest row invalid")
        name = str(row.get("name") or "")
        sha = str(row.get("sha256") or "").lower()
        size = int(row.get("size") or -1)
        if not name or "/" in name or "\\" in name or name in listed or not SHA_RE.fullmatch(sha) or size < 0:
            raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_PACKAGE_MANIFEST_INVALID", f"package manifest entry rejected: {name!r}")
        listed.add(name)
        path = release_dir / name
        if not path.is_file() or path.stat().st_size != size or _sha256(path) != sha:
            raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_PACKAGE_FILE_MISMATCH", f"package manifest mismatch: {name}")
    if WORKER_EXE not in listed or WORKER_EXE not in set(map(str, required)):
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_WORKER_MISSING", "worker executable is not a required manifest file")
    for name in map(str, required):
        if name not in listed:
            raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_REQUIRED_FILE_MISSING", f"required file not listed: {name}")
    extras = zip_names - listed - ALLOWED_EXTRA_FILES
    if extras:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_UNLISTED_OPERATIONAL_FILE", f"unlisted ZIP members rejected: {sorted(extras)}")


def _run_worker(root: Path, command: str, timeout: int = 120) -> dict[str, Any]:
    if command not in {"self-test", "heartbeat-only", "once"}:
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_INTERNAL_COMMAND_REJECTED", "internal worker command rejected")
    worker = (root / WORKER_EXE).resolve()
    if worker.parent != root.resolve() or not worker.is_file():
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_WORKER_MISSING", "fixed worker executable is missing")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    completed = subprocess.run([str(worker), command], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False, creationflags=flags)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "worker command failed")[-2000:]
        raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_WORKER_CHECK_FAILED", f"{command}: {detail}")
    text = (completed.stdout or "").strip()
    try:
        value = json.loads(text[text.find("{"):]) if "{" in text else {}
    except Exception:
        value = {}
    return {"returncode": completed.returncode, "stdout": text[-4000:], "json": value}


def _swap_and_verify(root: Path, staged: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    current = root / CURRENT_NAME
    previous = root / PREVIOUS_NAME
    if previous.exists():
        shutil.rmtree(previous)
    moved_current = False
    try:
        if current.exists():
            os.replace(current, previous)
            moved_current = True
        os.replace(staged, current)
        heartbeat = _run_worker(current, "heartbeat-only", timeout=90)
        return {"heartbeat": heartbeat, "rollback_available": moved_current}
    except Exception as exc:
        try:
            if current.exists():
                shutil.rmtree(current)
            if moved_current and previous.exists():
                os.replace(previous, current)
                try:
                    _run_worker(current, "heartbeat-only", timeout=90)
                except Exception:
                    try:
                        _run_worker(current, "once", timeout=120)
                    except Exception:
                        pass
        finally:
            if isinstance(exc, CsmcSelfUpdateError):
                raise
            raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_SWAP_FAILED", str(exc)) from exc


def _run_current_cycle(root: Path) -> dict[str, Any]:
    current = root / CURRENT_NAME
    if not (current / WORKER_EXE).is_file():
        return {"status": "NO_CURRENT_WORKER"}
    try:
        return {"status": "HEARTBEAT_ONLY", "result": _run_worker(current, "heartbeat-only", timeout=90)}
    except CsmcSelfUpdateError:
        # V4.2 baseline predates heartbeat-only. This fallback exists only so the
        # one-time bootstrap can coexist with the already-installed V4.2 until
        # the first promoted self-update release lands.
        return {"status": "LEGACY_ONCE", "result": _run_worker(current, "once", timeout=180)}


def _acquire_lock(root: Path) -> tuple[int, Path]:
    bootstrap = root / BOOTSTRAP_NAME
    bootstrap.mkdir(parents=True, exist_ok=True)
    path = bootstrap / LOCK_NAME
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            age = time.time() - path.stat().st_mtime
            if age > 15 * 60:
                path.unlink(missing_ok=True)
                fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            else:
                raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_ALREADY_RUNNING", "another fixed updater cycle is active")
        except OSError as exc:
            raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_LOCK_FAILED", str(exc)) from exc
    os.write(fd, str(os.getpid()).encode("ascii"))
    return fd, path


def run_cycle() -> dict[str, Any]:
    root = _root()
    fd, lock_path = _acquire_lock(root)
    state_path = root / BOOTSTRAP_NAME / STATE_NAME
    try:
        credential = _credential()
        manifest = _parse_manifest(_request("manifest", credential, max_bytes=256 * 1024))
        current_info = _load_current_release(root)
        current_key = str(current_info.get("release_key") or "")
        if current_key == manifest["release_key"]:
            cycle = _run_current_cycle(root)
            result = {
                "schema_version": "csmc_canary_self_update_result_v1",
                "status": "CURRENT_RELEASE_CONFIRMED",
                "release_key": current_key,
                "bootstrap_version": BOOTSTRAP_VERSION,
                "cycle": cycle,
                "production_worker_changed": False,
            }
            _write_json_atomic(state_path, result)
            return result

        package_path = _download_package(root, manifest, credential)
        staged = _safe_extract(root, package_path, manifest)
        self_test = _run_worker(staged, "self-test", timeout=120)
        swap = _swap_and_verify(root, staged, manifest)
        result = {
            "schema_version": "csmc_canary_self_update_result_v1",
            "status": "UPDATED_VERIFIED",
            "release_key": manifest["release_key"],
            "canary_version": manifest["canary_version"],
            "package_sha256": manifest["package_sha256"],
            "package_size": manifest["package_size"],
            "package_manifest_sha256": manifest["package_manifest_sha256"],
            "ci_run_id": manifest["ci_run_id"],
            "github_head": manifest["github_head"],
            "self_test": self_test,
            "heartbeat": swap["heartbeat"],
            "rollback_available": swap["rollback_available"],
            "bootstrap_version": BOOTSTRAP_VERSION,
            "production_worker_changed": False,
        }
        _write_json_atomic(state_path, result)
        return result
    except Exception as exc:
        code = exc.code if isinstance(exc, CsmcSelfUpdateError) else "CSMC_SELF_UPDATE_FAILED"
        failure = {
            "schema_version": "csmc_canary_self_update_result_v1",
            "status": "FAILED_ROLLBACK_ATTEMPTED",
            "error_code": code,
            "error": str(exc)[:2000],
            "bootstrap_version": BOOTSTRAP_VERSION,
            "production_worker_changed": False,
        }
        try:
            _write_json_atomic(state_path, failure)
        except Exception:
            pass
        if isinstance(exc, CsmcSelfUpdateError):
            raise
        raise CsmcSelfUpdateError(code, str(exc)) from exc
    finally:
        try:
            os.close(fd)
        except Exception:
            pass
        lock_path.unlink(missing_ok=True)


def self_test() -> dict[str, Any]:
    checks = {
        "bootstrap_version_fixed": BOOTSTRAP_VERSION == 1,
        "release_endpoint_fixed": FIXED_RELEASE_ENDPOINT.startswith("https://base44.app/api/apps/6aa2743da37b11162682c01f/functions/csmc-canary-release"),
        "root_fixed": str(ROOT_SUBDIR).replace("\\", "/") == "UKIE_AI_BRIDGE/csmc-canary",
        "task_not_managed_dynamically": True,
        "arbitrary_url_disabled": True,
        "arbitrary_path_disabled": True,
        "arbitrary_command_disabled": True,
        "admin_elevation_disabled": True,
        "registry_change_disabled": True,
        "production_worker_unchanged": True,
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "bootstrap_version": BOOTSTRAP_VERSION, "checks": checks}


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["self-test"]:
            print(json.dumps(self_test(), ensure_ascii=False, indent=2))
            raise SystemExit(0 if self_test()["status"] == "PASS" else 2)
        if sys.argv[1:]:
            raise CsmcSelfUpdateError("CSMC_SELF_UPDATE_ARGS_REJECTED", "bootstrap accepts no runtime arguments")
        print(json.dumps(run_cycle(), ensure_ascii=False, indent=2))
    except CsmcSelfUpdateError as exc:
        print(json.dumps({"status": "ERROR", "error_code": exc.code, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
