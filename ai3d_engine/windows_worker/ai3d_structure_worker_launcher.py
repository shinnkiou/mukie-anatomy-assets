# SPDX-License-Identifier: MIT
"""Stable one-time launcher/updater for the NEVER TEAR AI3D Structure Worker.

Security properties:
- update endpoints are hard-coded to one GitHub repository/release channel;
- remote manifests cannot supply URLs, paths, commands, scripts, or executables;
- the worker asset name/capability/release tag are fixed;
- downloaded bytes are SHA-256 verified and must pass the worker self-test before activation;
- updates are installed side-by-side and current.json is switched atomically;
- update failure falls back to the last locally verified worker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

LAUNCHER_VERSION = "0.1.0-ai3d-structure-launcher"
SCHEMA_VERSION = "never-tear-ai3d-structure-worker-channel-v1"
CHANNEL = "ai3d-structure-canary"
CAPABILITY = "ai3d_structure_module_v1"
RELEASE_TAG = "ai3d-structure-worker-canary-channel"
ASSET_NAME = "NEVER_TEAR_AI3D_STRUCTURE_WORKER.exe"
CHANNEL_ASSET_NAME = "AI3D_STRUCTURE_WORKER_CHANNEL_V1.json"
REPO = "shinnkiou/mukie-anatomy-assets"
CHANNEL_URL = f"https://github.com/{REPO}/releases/download/{RELEASE_TAG}/{CHANNEL_ASSET_NAME}"
WORKER_URL = f"https://github.com/{REPO}/releases/download/{RELEASE_TAG}/{ASSET_NAME}"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_WORKER_BYTES = 32 * 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 25
SELF_TEST_TIMEOUT_SECONDS = 45
HEX = set("0123456789abcdef")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9][a-z0-9.-]{0,95})?$")
ALLOWED_MANIFEST_KEYS = frozenset({
    "schema_version", "channel", "capability", "release_tag", "asset_name",
    "worker_version", "sha256", "size_bytes", "min_launcher_version", "source_commit",
})


class LauncherError(RuntimeError):
    pass


def app_root() -> Path:
    root = os.environ.get("LOCALAPPDATA")
    if not root:
        raise LauncherError("LOCALAPPDATA is not available")
    path = Path(root) / "UKIE_AI_BRIDGE" / "ai3d" / "structure_canary"
    path.mkdir(parents=True, exist_ok=True)
    return path


def launcher_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_hex(value: str, length: int) -> bool:
    return len(value) == length and all(ch in HEX for ch in value.lower())


def semver_triplet(value: str) -> tuple[int, int, int]:
    prefix = value.split("-", 1)[0]
    parts = prefix.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise LauncherError(f"invalid semantic version: {value}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def validate_manifest(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LauncherError("channel manifest must be an object")
    extra = set(value) - ALLOWED_MANIFEST_KEYS
    if extra:
        raise LauncherError(f"channel manifest contains forbidden keys: {sorted(extra)}")
    missing = ALLOWED_MANIFEST_KEYS - set(value)
    if missing:
        raise LauncherError(f"channel manifest missing keys: {sorted(missing)}")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise LauncherError("channel schema rejected")
    if value.get("channel") != CHANNEL:
        raise LauncherError("channel identity rejected")
    if value.get("capability") != CAPABILITY:
        raise LauncherError("capability rejected")
    if value.get("release_tag") != RELEASE_TAG:
        raise LauncherError("release tag rejected")
    if value.get("asset_name") != ASSET_NAME:
        raise LauncherError("worker asset name rejected")

    worker_version = str(value.get("worker_version") or "")
    if not VERSION_RE.fullmatch(worker_version):
        raise LauncherError("worker version rejected")
    sha = str(value.get("sha256") or "").lower()
    if not is_hex(sha, 64):
        raise LauncherError("worker SHA-256 rejected")
    try:
        size = int(value.get("size_bytes"))
    except Exception as exc:
        raise LauncherError("worker size is invalid") from exc
    if size <= 0 or size > MAX_WORKER_BYTES:
        raise LauncherError("worker size outside fixed launcher limit")

    min_launcher = str(value.get("min_launcher_version") or "")
    if not VERSION_RE.fullmatch(min_launcher):
        raise LauncherError("min launcher version rejected")
    if semver_triplet(min_launcher) > semver_triplet(LAUNCHER_VERSION):
        raise LauncherError(
            f"channel requires launcher {min_launcher}; installed launcher is {LAUNCHER_VERSION}"
        )

    source_commit = str(value.get("source_commit") or "").lower()
    if not is_hex(source_commit, 40):
        raise LauncherError("source commit rejected")

    return {
        "schema_version": SCHEMA_VERSION,
        "channel": CHANNEL,
        "capability": CAPABILITY,
        "release_tag": RELEASE_TAG,
        "asset_name": ASSET_NAME,
        "worker_version": worker_version,
        "sha256": sha,
        "size_bytes": size,
        "min_launcher_version": min_launcher,
        "source_commit": source_commit,
    }


def allowed_final_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        return False
    host = (parsed.hostname or "").lower()
    return host == "github.com" or host == "release-assets.githubusercontent.com" or host.endswith(".githubusercontent.com")


def read_https(url: str, max_bytes: int, timeout: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"NEVER-TEAR-AI3D-Structure-Launcher/{LAUNCHER_VERSION}"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        if not allowed_final_url(final_url):
            raise LauncherError(f"update redirect host rejected: {final_url}")
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                advertised = int(content_length)
            except ValueError as exc:
                raise LauncherError("invalid Content-Length") from exc
            if advertised < 0 or advertised > max_bytes:
                raise LauncherError("download exceeds launcher limit")
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise LauncherError("download exceeds launcher limit")
    return data


def fetch_remote_manifest() -> dict[str, Any]:
    raw = read_https(CHANNEL_URL, MAX_MANIFEST_BYTES, DOWNLOAD_TIMEOUT_SECONDS)
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise LauncherError("channel manifest is not valid UTF-8 JSON") from exc
    return validate_manifest(value)


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise LauncherError(f"unreadable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise LauncherError(f"JSON object required: {path}")
    return value


def verify_worker_self_test(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            [str(path), "--self-test"],
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=SELF_TEST_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        raise LauncherError(f"worker self-test could not run: {exc}") from exc
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode != 0:
        raise LauncherError(f"worker self-test failed rc={proc.returncode}: {output[-1200:].strip()}")
    start = output.find("{")
    end = output.rfind("}")
    if start < 0 or end <= start:
        raise LauncherError("worker self-test returned no JSON object")
    try:
        result = json.loads(output[start:end + 1])
    except Exception as exc:
        raise LauncherError("worker self-test JSON is invalid") from exc
    if not isinstance(result, dict) or result.get("status") != "PASS":
        raise LauncherError("worker self-test did not report PASS")
    if result.get("worker_version") != manifest["worker_version"]:
        raise LauncherError("worker self-test version does not match channel manifest")
    if result.get("allowed_actions") != [CAPABILITY]:
        raise LauncherError("worker self-test allowlist does not match fixed capability")
    if result.get("arbitrary_shell") is not False:
        raise LauncherError("worker self-test did not prove arbitrary_shell=false")
    return result


def install_verified_worker(source: Path, manifest: dict[str, Any], root: Path) -> Path:
    expected_sha = manifest["sha256"]
    if source.stat().st_size != manifest["size_bytes"]:
        raise LauncherError("worker byte size does not match channel manifest")
    actual_sha = sha256_file(source)
    if actual_sha != expected_sha:
        raise LauncherError(f"worker SHA mismatch expected={expected_sha} actual={actual_sha}")
    verify_worker_self_test(source, manifest)

    release_dir = root / "releases" / expected_sha[:16]
    release_dir.mkdir(parents=True, exist_ok=True)
    target = release_dir / ASSET_NAME
    if target.is_file():
        if target.stat().st_size != manifest["size_bytes"] or sha256_file(target) != expected_sha:
            raise LauncherError("existing release directory contains mismatched worker bytes")
    else:
        tmp = release_dir / (ASSET_NAME + ".tmp")
        shutil.copyfile(source, tmp)
        if sha256_file(tmp) != expected_sha:
            try:
                tmp.unlink()
            finally:
                raise LauncherError("worker changed while copying into release store")
        os.replace(tmp, target)

    state = {
        "schema_version": "never-tear-ai3d-structure-launcher-state-v1",
        "launcher_version": LAUNCHER_VERSION,
        "worker_version": manifest["worker_version"],
        "sha256": expected_sha,
        "size_bytes": manifest["size_bytes"],
        "capability": CAPABILITY,
        "source_commit": manifest["source_commit"],
        "release_relpath": str(target.relative_to(root)).replace("\\", "/"),
    }
    atomic_json(root / "current.json", state)
    return target


def current_worker(root: Path) -> tuple[Path, dict[str, Any]] | None:
    state_path = root / "current.json"
    if not state_path.is_file():
        return None
    state = load_json(state_path)
    if state.get("schema_version") != "never-tear-ai3d-structure-launcher-state-v1":
        raise LauncherError("local current.json schema rejected")
    if state.get("capability") != CAPABILITY:
        raise LauncherError("local current.json capability rejected")
    rel = str(state.get("release_relpath") or "")
    rel_path = Path(rel)
    if not rel or rel_path.is_absolute() or ".." in rel_path.parts:
        raise LauncherError("local current.json release path rejected")
    path = (root / rel_path).resolve()
    releases = (root / "releases").resolve()
    try:
        path.relative_to(releases)
    except ValueError as exc:
        raise LauncherError("local worker escaped releases root") from exc
    sha = str(state.get("sha256") or "").lower()
    if not is_hex(sha, 64) or not path.is_file():
        raise LauncherError("local current worker is missing or has invalid SHA state")
    if sha256_file(path) != sha:
        raise LauncherError("local current worker SHA check failed")
    return path, state


def seed_if_needed(root: Path) -> None:
    if (root / "current.json").is_file():
        return
    seed_dir = launcher_dir() / "seed"
    manifest_path = seed_dir / CHANNEL_ASSET_NAME
    worker_path = seed_dir / ASSET_NAME
    if not manifest_path.is_file() or not worker_path.is_file():
        raise LauncherError("no verified local worker is installed and bootstrap seed is missing")
    manifest = validate_manifest(load_json(manifest_path))
    install_verified_worker(worker_path, manifest, root)
    print(f"Seed worker activated: {manifest['worker_version']}", flush=True)


def update_if_available(root: Path) -> str:
    current = current_worker(root)
    current_sha = current[1]["sha256"] if current else None
    manifest = fetch_remote_manifest()
    if manifest["sha256"] == current_sha:
        return f"Worker already current: {manifest['worker_version']}"

    downloads = root / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    tmp = downloads / (manifest["sha256"] + ".download")
    raw = read_https(WORKER_URL, MAX_WORKER_BYTES, DOWNLOAD_TIMEOUT_SECONDS)
    if len(raw) != manifest["size_bytes"]:
        raise LauncherError(f"downloaded worker size mismatch expected={manifest['size_bytes']} actual={len(raw)}")
    tmp.write_bytes(raw)
    try:
        path = install_verified_worker(tmp, manifest, root)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
    return f"Updated worker to {manifest['worker_version']} ({path})"


def run_current(root: Path) -> int:
    current = current_worker(root)
    if current is None:
        raise LauncherError("no verified current worker")
    path, state = current
    print(f"Launching verified Structure Worker {state['worker_version']} sha256={state['sha256']}", flush=True)
    proc = subprocess.Popen([str(path)], shell=False)
    return int(proc.wait())


def self_test() -> int:
    failures: list[str] = []
    good = {
        "schema_version": SCHEMA_VERSION,
        "channel": CHANNEL,
        "capability": CAPABILITY,
        "release_tag": RELEASE_TAG,
        "asset_name": ASSET_NAME,
        "worker_version": "0.2.3-ai3d-structure-loaderfix",
        "sha256": "a" * 64,
        "size_bytes": 123456,
        "min_launcher_version": "0.1.0",
        "source_commit": "b" * 40,
    }
    try:
        validate_manifest(good)
    except Exception as exc:
        failures.append(f"valid manifest rejected: {exc}")

    bad_cases = [
        {**good, "asset_name": "evil.exe"},
        {**good, "capability": "arbitrary_shell"},
        {**good, "release_tag": "../other"},
        {**good, "sha256": "00"},
        {**good, "size_bytes": MAX_WORKER_BYTES + 1},
        {**good, "min_launcher_version": "99.0.0"},
        {**good, "url": "https://example.com/evil.exe"},
        {**good, "path": "C:\\Windows\\System32\\cmd.exe"},
        {**good, "command": "powershell"},
        {**good, "script": "print('x')"},
    ]
    for index, case in enumerate(bad_cases, 1):
        try:
            validate_manifest(case)
        except LauncherError:
            continue
        failures.append(f"bad manifest case {index} was accepted")

    fixed_prefix = f"https://github.com/{REPO}/releases/download/{RELEASE_TAG}/"
    if not CHANNEL_URL.startswith(fixed_prefix):
        failures.append("channel URL is not fixed to the approved GitHub release")
    if not WORKER_URL.startswith(fixed_prefix):
        failures.append("worker URL is not fixed to the approved GitHub release")

    result = {
        "schema_version": "never-tear-ai3d-structure-launcher-selftest-v1",
        "launcher_version": LAUNCHER_VERSION,
        "channel": CHANNEL,
        "capability": CAPABILITY,
        "release_tag": RELEASE_TAG,
        "fixed_channel_url": CHANNEL_URL,
        "fixed_worker_url": WORKER_URL,
        "remote_url_from_manifest_allowed": False,
        "remote_path_from_manifest_allowed": False,
        "remote_command_from_manifest_allowed": False,
        "arbitrary_shell": False,
        "side_by_side_releases": True,
        "atomic_current_switch": True,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0 if not failures else 23


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--no-update", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    try:
        root = app_root()
        seed_if_needed(root)
        if not args.no_update:
            try:
                print(update_if_available(root), flush=True)
            except Exception as exc:
                print(f"UPDATE HOLD: {exc}", file=sys.stderr, flush=True)
                if current_worker(root) is None:
                    raise
        return run_current(root)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"AI3D_STRUCTURE_LAUNCHER_ERROR: {exc}", file=sys.stderr, flush=True)
        return 23


if __name__ == "__main__":
    raise SystemExit(main())
