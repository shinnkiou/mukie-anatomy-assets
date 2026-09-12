"""SHA-pinned fixed Python execution for the isolated CSMC canary.

This module is intentionally not a generic Python runner. The cloud cannot
provide a path, source body, module name, argument, environment override, or
working directory. Exactly one packaged Python script is accepted and it is
executed in-process only after its SHA-256 matches the hash embedded by CI.
"""

from __future__ import annotations

import hashlib
import runpy
import sys
from pathlib import Path
from typing import Any

PYTHON_SCRIPT_BASENAME = "CSMC_AutoCycle_V01.py"
POLICY_VERSION = "csmc_fixed_exec_v1"


class CsmcPinnedExecutionError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def worker_binary_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def approved_python_path() -> Path:
    return worker_binary_dir() / PYTHON_SCRIPT_BASENAME


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def embedded_python_sha256() -> str:
    try:
        from . import embedded_release_csmc as embedded_release
    except ImportError:
        try:
            import embedded_release_csmc as embedded_release
        except ImportError as exc:
            raise CsmcPinnedExecutionError("PIN_UNAVAILABLE", "embedded CSMC release policy is unavailable") from exc
    value = str(getattr(embedded_release, "AUTO_CYCLE_PY_SHA256", "")).lower()
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise CsmcPinnedExecutionError("PIN_UNAVAILABLE", "embedded Python SHA-256 pin is invalid")
    return value


def run_approved_python_cycle(
    *,
    script: Path | None = None,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Execute the one approved CSMC Python script with no caller arguments."""
    path = (script or approved_python_path()).resolve()
    if not path.is_file() or path.name != PYTHON_SCRIPT_BASENAME:
        raise CsmcPinnedExecutionError("PYTHON_SCRIPT_MISSING", "fixed CSMC Python script is missing")

    expected = (expected_sha256 or embedded_python_sha256()).lower()
    actual = sha256_file(path)
    if actual != expected:
        raise CsmcPinnedExecutionError("PYTHON_SCRIPT_HASH_MISMATCH", "fixed CSMC Python script SHA-256 does not match embedded pin")

    # runpy executes the fixed source inside the already-packaged Python runtime.
    # No external python.exe, -c, module name, argv, or cloud-supplied argument is used.
    namespace = runpy.run_path(str(path), run_name="__csmc_approved__")
    entry = namespace.get("main_worker_cycle")
    if not callable(entry):
        raise CsmcPinnedExecutionError("PYTHON_ENTRY_MISSING", "approved Python script has no main_worker_cycle entrypoint")
    result = entry()
    if not isinstance(result, dict):
        raise CsmcPinnedExecutionError("PYTHON_RESULT_INVALID", "approved Python script must return a dictionary")

    return {
        **result,
        "python_script_sha256": actual,
        "python_execution": "PINNED_RUNPY_NO_ARGS",
        "execution_policy": POLICY_VERSION,
        "cloud_supplied_python_args": False,
    }
