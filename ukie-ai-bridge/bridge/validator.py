"""Fail-closed validator for UKIE AI BRIDGE jobs.

This module intentionally does NOT execute shell commands or arbitrary programs.
It validates a small allowlisted protocol before any execution adapter sees it.
Tool installation uses a separate frozen approval-manifest validator after the
manifest artifact itself has passed this job-envelope validation.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOWED_ACTIONS = {
    "device_status",
    "analyze_blend",
    "upload_results",
    "install_batch",
}
ALLOWED_PROJECTS = {"BP3D", "CSMC", "BRIDGE_TEST", "VIRTUAL_BROWSER"}
JOB_ID_RE = re.compile(r"^[A-Z0-9_\-]{4,80}$")
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
DEFAULT_TIMEOUT = 300
MAX_TIMEOUT = 1800


class JobValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedJob:
    job_id: str
    action: str
    project: str
    timeout_seconds: int
    drive_file_id: str
    input_sha256: str
    original_filename: str


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise JobValidationError(f"{label} must be an object")
    return value


def validate_job(payload: dict[str, Any]) -> ValidatedJob:
    if payload.get("schema_version") != "ukie_job_v1":
        raise JobValidationError("unsupported schema_version")

    job_id = payload.get("job_id")
    if not isinstance(job_id, str) or not JOB_ID_RE.fullmatch(job_id):
        raise JobValidationError("invalid job_id")

    action = payload.get("action")
    if action not in ALLOWED_ACTIONS:
        raise JobValidationError("action is not allowlisted")

    project = payload.get("project")
    if project not in ALLOWED_PROJECTS:
        raise JobValidationError("project is not allowlisted")

    timeout = payload.get("timeout_seconds", DEFAULT_TIMEOUT)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or not (10 <= timeout <= MAX_TIMEOUT):
        raise JobValidationError("timeout_seconds outside safe range")

    input_obj = _require_object(payload.get("input"), "input")
    drive_file_id = input_obj.get("drive_file_id")
    sha256 = input_obj.get("sha256")
    original_filename = input_obj.get("original_filename")

    if not isinstance(drive_file_id, str) or not drive_file_id.strip():
        raise JobValidationError("missing drive_file_id")
    if not isinstance(sha256, str) or not SHA256_RE.fullmatch(sha256):
        raise JobValidationError("invalid input sha256")
    if not isinstance(original_filename, str) or not original_filename:
        raise JobValidationError("missing original_filename")

    if action == "analyze_blend" and not original_filename.lower().endswith(".blend"):
        raise JobValidationError("analyze_blend requires a .blend artifact")
    if action == "install_batch" and not original_filename.lower().endswith(".json"):
        raise JobValidationError("install_batch requires a frozen JSON approval manifest")

    # Explicitly reject fields that would turn the protocol into arbitrary code execution.
    forbidden = {"shell", "powershell", "exe", "command", "registry", "delete_path", "arguments", "argv"}
    if forbidden.intersection(payload.keys()):
        raise JobValidationError("forbidden execution field present")

    return ValidatedJob(
        job_id=job_id,
        action=action,
        project=project,
        timeout_seconds=timeout,
        drive_file_id=drive_file_id,
        input_sha256=sha256.lower(),
        original_filename=original_filename,
    )


def load_and_validate(path: str | Path) -> ValidatedJob:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return validate_job(_require_object(payload, "root"))


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
