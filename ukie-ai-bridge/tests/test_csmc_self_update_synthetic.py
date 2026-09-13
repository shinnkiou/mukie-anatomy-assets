from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge import csmc_self_update as m


def make_package(tmp: Path, release_key: str) -> tuple[bytes, str, int, str]:
    src = tmp / "pkg"
    src.mkdir()
    worker = src / m.WORKER_EXE
    worker.write_bytes(b"synthetic-worker-v43")
    release = src / "RELEASE_INFO.json"
    release.write_text(json.dumps({"release_key": release_key, "bridge_version": "synthetic-v43"}), encoding="utf-8")
    files = []
    for p in (worker, release):
        files.append({"name": p.name, "size": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    manifest = {
        "schema_version": "ukie_csmc_canary_package_manifest_v2",
        "required_files": [m.WORKER_EXE, "RELEASE_INFO.json"],
        "files": files,
    }
    manifest_bytes = json.dumps(manifest, indent=2).encode()
    (src / m.PACKAGE_MANIFEST).write_bytes(manifest_bytes)
    (src / "README_FIRST.txt").write_text("synthetic", encoding="utf-8")
    zpath = tmp / "package.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for name in (m.WORKER_EXE, "RELEASE_INFO.json", m.PACKAGE_MANIFEST, "README_FIRST.txt"):
            z.write(src / name, arcname=name)
    raw = zpath.read_bytes()
    return raw, hashlib.sha256(raw).hexdigest(), len(raw), hashlib.sha256(manifest_bytes).hexdigest()


def manifest_for(release_key: str, package_sha: str, package_size: int, manifest_sha: str) -> dict:
    return {
        "ok": True,
        "schema_version": m.SCHEMA,
        "release_key": release_key,
        "canary_version": "synthetic-v43",
        "package_filename": "UKIE_AI_BRIDGE_CSMC_CANARY_SYNTHETIC_V43.zip",
        "package_size": package_size,
        "package_sha256": package_sha,
        "package_manifest_sha256": manifest_sha,
        "ci_success": True,
        "ci_run_id": 123,
        "github_head": "a" * 40,
        "drive_raw_readback_verified": True,
        "package_manifest_all_files_match": True,
        "promote": True,
        "bootstrap_protocol": m.PROTOCOL,
        "min_bootstrap_version": 1,
        "package_endpoint_mode": "same_fixed_endpoint_package",
        "arbitrary_url_present": False,
        "arbitrary_path_present": False,
    }


def setup_current(root: Path, key: str = "CSMC_CANARY_OLD_0001") -> None:
    current = root / m.CURRENT_NAME
    current.mkdir(parents=True)
    (current / m.WORKER_EXE).write_bytes(b"old-worker")
    (current / "RELEASE_INFO.json").write_text(json.dumps({"release_key": key}), encoding="utf-8")


def test_success() -> None:
    with tempfile.TemporaryDirectory() as td:
        os.environ["LOCALAPPDATA"] = td
        root = Path(td) / m.ROOT_SUBDIR
        setup_current(root)
        release_key = "CSMC_CANARY_SYNTHETIC_V43_0001"
        package, psha, psize, msha = make_package(Path(td), release_key)
        release_manifest = manifest_for(release_key, psha, psize, msha)
        m.load_credential = lambda: {"device_key": "device_key_test", "device_token": "x" * 64}
        m._request = lambda mode, credential, max_bytes: json.dumps(release_manifest).encode() if mode == "manifest" else package
        calls = []
        m._run_worker = lambda root, command, timeout=120: calls.append((root.name, command)) or {"returncode": 0, "json": {"status": "PASS"}}
        out = m.run_cycle()
        assert out["status"] == "UPDATED_VERIFIED"
        assert (root / m.CURRENT_NAME / "RELEASE_INFO.json").is_file()
        assert json.loads((root / m.CURRENT_NAME / "RELEASE_INFO.json").read_text())["release_key"] == release_key
        assert (root / m.PREVIOUS_NAME / "RELEASE_INFO.json").is_file()
        assert calls == [("release_" + release_key, "self-test"), (m.CURRENT_NAME, "heartbeat-only")]


def test_rollback() -> None:
    with tempfile.TemporaryDirectory() as td:
        os.environ["LOCALAPPDATA"] = td
        root = Path(td) / m.ROOT_SUBDIR
        old_key = "CSMC_CANARY_OLD_0002"
        setup_current(root, old_key)
        release_key = "CSMC_CANARY_SYNTHETIC_V43_0002"
        package, psha, psize, msha = make_package(Path(td), release_key)
        release_manifest = manifest_for(release_key, psha, psize, msha)
        m.load_credential = lambda: {"device_key": "device_key_test", "device_token": "x" * 64}
        m._request = lambda mode, credential, max_bytes: json.dumps(release_manifest).encode() if mode == "manifest" else package
        def fake_run(root: Path, command: str, timeout: int = 120):
            if root.name == m.CURRENT_NAME and command == "heartbeat-only" and json.loads((root / "RELEASE_INFO.json").read_text())["release_key"] == release_key:
                raise m.CsmcSelfUpdateError("SYNTHETIC_HEARTBEAT_FAIL", "synthetic")
            return {"returncode": 0}
        m._run_worker = fake_run
        try:
            m.run_cycle()
            raise AssertionError("expected failure")
        except m.CsmcSelfUpdateError as exc:
            assert exc.code == "SYNTHETIC_HEARTBEAT_FAIL"
        restored = json.loads((root / m.CURRENT_NAME / "RELEASE_INFO.json").read_text())
        assert restored["release_key"] == old_key


if __name__ == "__main__":
    test_success()
    test_rollback()
    print("CSMC self-update synthetic tests PASS")
