"""Explicit retry contract for UKIE AI BRIDGE.

Transport replay and intentional retry are different operations. A transport
replay keeps the same job_id and MUST NOT execute again. An intentional retry
creates a NEW job_id linked to a parent job, with an incremented attempt number.
This preserves provenance and keeps the exact-once guarantee simple.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

JOB_ID_RE = re.compile(r"^[A-Z0-9_\-]{4,80}$")
ALLOWED_REASONS = {
    "HUMAN_RETRY",
    "RECOVERY_POLICY",
    "RESOURCE_RETRY",
    "COMPATIBILITY_RETRY",
    "FIXED_SCRIPT_RETRY",
}


class RetryContractError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedRetry:
    parent_job_id: str
    new_job_id: str
    attempt_no: int
    reason: str
    approved_by: str


def validate_retry_contract(payload: dict[str, Any]) -> ValidatedRetry:
    if not isinstance(payload, dict):
        raise RetryContractError("retry root must be an object")
    if payload.get("schema_version") != "ukie_retry_v1":
        raise RetryContractError("unsupported retry schema_version")

    parent = payload.get("parent_job_id")
    new_job = payload.get("new_job_id")
    if not isinstance(parent, str) or not JOB_ID_RE.fullmatch(parent):
        raise RetryContractError("invalid parent_job_id")
    if not isinstance(new_job, str) or not JOB_ID_RE.fullmatch(new_job):
        raise RetryContractError("invalid new_job_id")
    if new_job == parent:
        raise RetryContractError("intentional retry must use a new job_id")

    attempt_no = payload.get("attempt_no")
    if not isinstance(attempt_no, int) or isinstance(attempt_no, bool) or not (1 <= attempt_no <= 99):
        raise RetryContractError("attempt_no must be 1..99")

    reason = payload.get("reason")
    if reason not in ALLOWED_REASONS:
        raise RetryContractError("retry reason is not allowlisted")

    approved_by = payload.get("approved_by")
    if not isinstance(approved_by, str) or not approved_by.strip():
        raise RetryContractError("approved_by is required")

    # A retry contract cannot smuggle executable content.
    forbidden = {"shell", "powershell", "command", "exe", "arguments", "argv", "script_body", "delete_path", "registry"}
    if forbidden.intersection(str(k).lower() for k in payload.keys()):
        raise RetryContractError("forbidden execution field present")

    return ValidatedRetry(
        parent_job_id=parent,
        new_job_id=new_job,
        attempt_no=attempt_no,
        reason=reason,
        approved_by=approved_by.strip(),
    )
