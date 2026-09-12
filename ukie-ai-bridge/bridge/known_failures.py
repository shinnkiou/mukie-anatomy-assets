"""Runtime failure knowledge primitives for UKIE AI BRIDGE.

The full human-readable knowledge base is persisted in the Base44 control plane.
This module carries the small deterministic subset needed by the packaged Bridge
so safety does not depend on network availability.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


KNOWN_DEBUGGER_NOISE = {
    "E06D7363": "NOISE_X64_CPP_FIRST_CHANCE",
    "04242420": "NOISE_X64_CLR",
}

CRITICAL_FAILURE_CODES = {
    "ERROR_X64_001",
    "ERROR_ARTIFACT_001",
    "ERROR_ARTIFACT_002",
}


@dataclass(frozen=True)
class FailureMatch:
    error_code: str
    status: str
    confidence: float
    detail: str


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_debugger_line(line: str) -> FailureMatch | None:
    upper = line.upper()
    for marker, code in KNOWN_DEBUGGER_NOISE.items():
        if marker in upper:
            return FailureMatch(
                error_code=code,
                status="NOISE",
                confidence=1.0,
                detail=f"Known non-terminal debugger noise marker {marker}",
            )
    if "ACCESS VIOLATION" in upper or "EXCEPTION_ACCESS_VIOLATION" in upper:
        return FailureMatch(
            error_code="ERROR_X64_UNEXPECTED_ACCESS_VIOLATION",
            status="UNKNOWN",
            confidence=0.9,
            detail="Unexpected access violation must remain visible and stop automatic confirmation.",
        )
    return None


def validate_target_identity(
    *,
    observer_pid: int,
    target_pid: int,
    target_exe_name: str,
    expected_exe_name: str = "CLIPStudioModeler.exe",
    target_path: str | None = None,
    target_sha256: str | None = None,
) -> dict[str, Any]:
    """Fail closed on the historical self-attach / loose-name failure mode."""
    failures: list[str] = []
    if observer_pid == target_pid:
        failures.append("ERROR_X64_001")
    if target_exe_name.lower() != expected_exe_name.lower():
        failures.append("ERROR_X64_001")
    if not target_path:
        failures.append("ERROR_X64_001")
    if target_sha256 is not None:
        digest = target_sha256.lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            failures.append("ERROR_X64_001")

    return {
        "status": "PASS" if not failures else "FAIL",
        "error_codes": sorted(set(failures)),
        "observer_pid": observer_pid,
        "target_pid": target_pid,
        "target_exe_name": target_exe_name,
        "target_path": target_path,
        "target_sha256": target_sha256,
    }


def validate_batch_bytes(data: bytes) -> dict[str, Any]:
    """Validate the deterministic ASCII/no-BOM/CRLF batch-file policy."""
    errors: list[str] = []
    if data.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")):
        errors.append("ERROR_CMD_001")
    try:
        data.decode("ascii")
    except UnicodeDecodeError:
        errors.append("ERROR_CMD_001")
    # A non-empty batch file must use CRLF only; lone LF means unstable encoding/output.
    if data and b"\n" in data.replace(b"\r\n", b""):
        errors.append("ERROR_CMD_001")
    return {
        "status": "PASS" if not errors else "FAIL",
        "error_codes": sorted(set(errors)),
        "ascii_only": not any(b >= 0x80 for b in data),
        "bom_present": data.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")),
        "crlf_only": b"\n" not in data.replace(b"\r\n", b""),
    }


def classify_memory_hit(*, memory_type: str, writable: bool, changed_across_phases: bool) -> dict[str, Any]:
    """Prevent static MEM_IMAGE/GUID hits from being promoted to semantic evidence."""
    if memory_type.upper() == "MEM_IMAGE" and not changed_across_phases:
        return {
            "status": "OBSERVED",
            "confirmed": False,
            "error_code": "ERROR_X64_002",
            "reason": "Static image-backed hit without dynamic change is not semantic evidence.",
        }
    if not writable and not changed_across_phases:
        return {
            "status": "OBSERVED",
            "confirmed": False,
            "error_code": "ERROR_X64_004",
            "reason": "Single-pass/non-writable change is insufficient for confirmation.",
        }
    return {
        "status": "CANDIDATE",
        "confirmed": False,
        "error_code": None,
        "reason": "Candidate requires control-change-control-restore or data-flow evidence.",
    }
