"""Atomic local durability state for UKIE AI BRIDGE.

The cloud control plane is not trusted to deliver exactly once. This store makes
job execution idempotent on the Windows worker: replaying the same job envelope
returns the existing receipt; reusing a job ID with different immutable inputs is
rejected as a conflict.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .validator import ValidatedJob

STATE_SCHEMA = "ukie_bridge_state_v1"


class StateConflictError(RuntimeError):
    pass


def default_state_root() -> Path:
    override = os.environ.get("UKIE_BRIDGE_HOME")
    if override:
        return Path(override)
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "UKIE_AI_BRIDGE"
    return Path.home() / ".ukie_ai_bridge"


class BridgeStateStore:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root is not None else default_state_root()
        self.path = self.root / "bridge_state.json"

    def _empty(self) -> dict[str, Any]:
        return {
            "schema_version": STATE_SCHEMA,
            "jobs": {},
            "install_batches": {},
            "tool_registry": {},
        }

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return self._empty()
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise StateConflictError(f"local state is unreadable: {exc}") from exc
        if not isinstance(data, dict) or data.get("schema_version") != STATE_SCHEMA:
            raise StateConflictError("unsupported local state schema")
        for key in ("jobs", "install_batches", "tool_registry"):
            if not isinstance(data.get(key), dict):
                raise StateConflictError(f"local state field {key} is invalid")
        return data

    def save(self, data: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        fd, temp_name = tempfile.mkstemp(prefix="bridge_state_", suffix=".tmp", dir=self.root)
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    @staticmethod
    def _identity(job: ValidatedJob) -> dict[str, Any]:
        return {
            "job_id": job.job_id,
            "action": job.action,
            "project": job.project,
            "input_sha256": job.input_sha256,
            "drive_file_id": job.drive_file_id,
            "original_filename": job.original_filename,
        }

    def register_job(self, job: ValidatedJob) -> dict[str, Any]:
        state = self.load()
        jobs = state["jobs"]
        identity = self._identity(job)
        existing = jobs.get(job.job_id)
        if existing:
            existing_identity = existing.get("identity")
            if existing_identity != identity:
                raise StateConflictError(
                    f"job_id {job.job_id} was reused with different immutable inputs"
                )
            return {
                "decision": "REPLAY_EXISTING",
                "job_id": job.job_id,
                "receipt": existing,
            }

        receipt = {
            "identity": identity,
            "status": "REGISTERED",
            "attempt_count": 0,
            "last_result": None,
        }
        jobs[job.job_id] = receipt
        self.save(state)
        return {"decision": "NEW_JOB", "job_id": job.job_id, "receipt": receipt}

    def mark_started(self, job: ValidatedJob) -> dict[str, Any]:
        self.register_job(job)
        state = self.load()
        receipt = state["jobs"][job.job_id]
        if receipt.get("status") == "COMPLETED":
            return {"decision": "ALREADY_COMPLETED", "receipt": receipt}
        receipt["status"] = "RUNNING"
        receipt["attempt_count"] = int(receipt.get("attempt_count", 0)) + 1
        self.save(state)
        return {"decision": "START", "receipt": receipt}

    def mark_completed(self, job: ValidatedJob, result: dict[str, Any]) -> dict[str, Any]:
        self.register_job(job)
        state = self.load()
        receipt = state["jobs"][job.job_id]
        receipt["status"] = "COMPLETED"
        receipt["last_result"] = result
        self.save(state)
        return receipt

    def mark_failed(self, job: ValidatedJob, result: dict[str, Any]) -> dict[str, Any]:
        self.register_job(job)
        state = self.load()
        receipt = state["jobs"][job.job_id]
        receipt["status"] = "FAILED"
        receipt["last_result"] = result
        self.save(state)
        return receipt

    def snapshot(self) -> dict[str, Any]:
        return self.load()
