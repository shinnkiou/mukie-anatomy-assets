"""Pre-flight engine for UKIE AI BRIDGE research jobs.

The engine is intentionally local and fail-closed. It performs deterministic
checks before Blender/debugger/analyzer processes are allowed to start. It never
installs software and never mutates the original input file.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


ALLOWED_PYTHON_ROLES = {"BLENDER_INTERNAL", "ANALYSIS"}
DANGEROUS_IMPORTS = {"subprocess", "winreg", "ctypes"}
DANGEROUS_CALL_SUFFIXES = {
    "os.remove",
    "os.unlink",
    "os.rmdir",
    "os.removedirs",
    "os.system",
    "os.popen",
    "shutil.rmtree",
    "pathlib.Path.unlink",
    "pathlib.Path.rmdir",
    "bpy.ops.wm.save_mainfile",
    "bpy.ops.wm.save_as_mainfile",
}


@dataclass(frozen=True)
class CheckResult:
    check_key: str
    status: str
    blocker: bool
    observed: dict[str, Any]
    error_code: str | None = None
    auto_fixed: bool = False
    duration_ms: int = 0


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _dotted_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    cur: ast.AST | None = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def inspect_python_script(path: Path, *, mode: str = "ANALYZE_ONLY") -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return {
            "status": "FAIL",
            "error_code": "ERROR_SCRIPT_SYNTAX",
            "syntax_error": f"{exc.msg} at line {exc.lineno}:{exc.offset}",
            "dangerous_imports": [],
            "dangerous_calls": [],
        }

    dangerous_imports: set[str] = set()
    dangerous_calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in DANGEROUS_IMPORTS:
                    dangerous_imports.add(root)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in DANGEROUS_IMPORTS:
                dangerous_imports.add(root)
        elif isinstance(node, ast.Call):
            name = _dotted_name(node.func)
            if name and name in DANGEROUS_CALL_SUFFIXES:
                dangerous_calls.add(name)

    # ANALYZE_ONLY is not allowed to save the Blender source under any name.
    if mode != "ANALYZE_ONLY":
        dangerous_calls.discard("bpy.ops.wm.save_mainfile")
        dangerous_calls.discard("bpy.ops.wm.save_as_mainfile")

    status = "PASS" if not dangerous_imports and not dangerous_calls else "FAIL"
    return {
        "status": status,
        "error_code": None if status == "PASS" else "ERROR_SCRIPT_GUARD",
        "mode": mode,
        "dangerous_imports": sorted(dangerous_imports),
        "dangerous_calls": sorted(dangerous_calls),
        "syntax_ok": True,
    }


def check_workspace(workspace: Path, *, required_free_bytes: int = 0) -> CheckResult:
    started = time.monotonic()
    try:
        resolved = workspace.expanduser().resolve(strict=False)
        resolved.mkdir(parents=True, exist_ok=True)
        probe = None
        try:
            fd, probe_name = tempfile.mkstemp(prefix="ukie_preflight_", suffix=".tmp", dir=resolved)
            os.close(fd)
            probe = Path(probe_name)
            probe.write_bytes(b"UKIE")
            writable = probe.read_bytes() == b"UKIE"
        finally:
            if probe and probe.exists():
                probe.unlink()
        usage = shutil.disk_usage(resolved)
        enough = usage.free >= required_free_bytes
        status = "PASS" if writable and enough else "FAIL"
        return CheckResult(
            check_key="PREFLIGHT_RESEARCH_DRIVE_WRITABLE",
            status=status,
            blocker=True,
            observed={
                "workspace": str(resolved),
                "writable": writable,
                "free_bytes": int(usage.free),
                "required_free_bytes": int(required_free_bytes),
                "enough_space": enough,
            },
            error_code=None if status == "PASS" else "ERROR_PREFLIGHT_STORAGE",
            duration_ms=int((time.monotonic() - started) * 1000),
        )
    except Exception as exc:
        return CheckResult(
            check_key="PREFLIGHT_RESEARCH_DRIVE_WRITABLE",
            status="FAIL",
            blocker=True,
            observed={"workspace": str(workspace), "error": str(exc)},
            error_code="ERROR_PREFLIGHT_STORAGE",
            duration_ms=int((time.monotonic() - started) * 1000),
        )


def check_input(path: Path, *, expected_sha256: str | None = None) -> CheckResult:
    started = time.monotonic()
    try:
        if not path.is_file():
            raise FileNotFoundError(path)
        stat_before = path.stat()
        digest = _sha256_file(path)
        stat_after = path.stat()
        stable = stat_before.st_size == stat_after.st_size and stat_before.st_mtime_ns == stat_after.st_mtime_ns
        hash_ok = expected_sha256 is None or digest.lower() == expected_sha256.lower()
        status = "PASS" if stable and hash_ok else "FAIL"
        return CheckResult(
            check_key="PREFLIGHT_INPUT_HASH",
            status=status,
            blocker=True,
            observed={
                "path_basename": path.name,
                "byte_size": int(stat_after.st_size),
                "sha256": digest,
                "stable_during_hash": stable,
                "expected_sha256_match": hash_ok,
                "unicode_original_name": not path.name.isascii(),
                "staging_basename": f"input{path.suffix.lower()}",
                "staging_ascii": f"input{path.suffix.lower()}".isascii(),
            },
            error_code=None if status == "PASS" else "ERROR_INPUT_HASH_MISMATCH",
            auto_fixed=not path.name.isascii(),
            duration_ms=int((time.monotonic() - started) * 1000),
        )
    except Exception as exc:
        return CheckResult(
            check_key="PREFLIGHT_INPUT_HASH",
            status="FAIL",
            blocker=True,
            observed={"path_basename": path.name, "error": str(exc)},
            error_code="ERROR_INPUT_UNREADABLE",
            duration_ms=int((time.monotonic() - started) * 1000),
        )


def check_script(path: Path, *, mode: str, python_role: str) -> CheckResult:
    started = time.monotonic()
    if python_role not in ALLOWED_PYTHON_ROLES:
        return CheckResult(
            check_key="PREFLIGHT_PYTHON_ROLE",
            status="FAIL",
            blocker=True,
            observed={"python_role": python_role, "allowed": sorted(ALLOWED_PYTHON_ROLES)},
            error_code="ERROR_PY_001",
            duration_ms=int((time.monotonic() - started) * 1000),
        )
    if not path.is_file():
        return CheckResult(
            check_key="PREFLIGHT_SCRIPT_SYNTAX",
            status="FAIL",
            blocker=True,
            observed={"script": str(path), "exists": False},
            error_code="ERROR_SCRIPT_MISSING",
            duration_ms=int((time.monotonic() - started) * 1000),
        )
    inspected = inspect_python_script(path, mode=mode)
    return CheckResult(
        check_key="PREFLIGHT_SCRIPT_SYNTAX",
        status=inspected["status"],
        blocker=True,
        observed={"script_basename": path.name, "python_role": python_role, **inspected},
        error_code=inspected.get("error_code"),
        duration_ms=int((time.monotonic() - started) * 1000),
    )


def run_foundation_preflight(
    *,
    workspace: Path,
    input_file: Path | None = None,
    expected_sha256: str | None = None,
    script_file: Path | None = None,
    script_mode: str = "ANALYZE_ONLY",
    python_role: str = "BLENDER_INTERNAL",
    required_free_bytes: int = 0,
) -> dict[str, Any]:
    results: list[CheckResult] = [check_workspace(workspace, required_free_bytes=required_free_bytes)]
    if input_file is not None:
        results.append(check_input(input_file, expected_sha256=expected_sha256))
    if script_file is not None:
        results.append(check_script(script_file, mode=script_mode, python_role=python_role))

    blockers = [r for r in results if r.blocker and r.status == "FAIL"]
    return {
        "schema_version": "ukie_preflight_report_v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "checks": [asdict(r) for r in results],
        "summary": {
            "total": len(results),
            "pass": sum(1 for r in results if r.status == "PASS"),
            "warn": sum(1 for r in results if r.status == "WARN"),
            "fail": sum(1 for r in results if r.status == "FAIL"),
            "blockers": len(blockers),
        },
    }


def write_preflight_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
