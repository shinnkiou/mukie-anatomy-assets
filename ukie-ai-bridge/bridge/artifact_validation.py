"""Artifact contract validation for UKIE AI BRIDGE.

A process exit code is never sufficient for SUCCESS. This module validates the
presence and minimum semantic content of expected artifacts before a job can
advance to LOCAL_SAVED / HASHED / UPLOADING.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ArtifactValidationError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_has_path(value: Any, dotted: str) -> bool:
    cur = value
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False
    return True


def validate_artifact_contract(job_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(contract, dict):
        raise ArtifactValidationError("artifact contract must be an object")
    files = contract.get("files")
    if not isinstance(files, list) or not files:
        raise ArtifactValidationError("artifact contract must declare a non-empty files list")

    root = job_dir.resolve()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for spec in files:
        if not isinstance(spec, dict):
            raise ArtifactValidationError("artifact file spec must be an object")
        name = spec.get("name")
        if not isinstance(name, str) or not name or Path(name).name != name:
            raise ArtifactValidationError("artifact name must be a simple basename")
        path = (root / name).resolve()
        if root not in path.parents:
            raise ArtifactValidationError("artifact path escaped job directory")

        exists = path.is_file()
        byte_size = path.stat().st_size if exists else 0
        min_bytes = int(spec.get("min_bytes", 1))
        item = {
            "name": name,
            "exists": exists,
            "byte_size": int(byte_size),
            "min_bytes": min_bytes,
            "sha256": sha256_file(path) if exists else None,
            "json_valid": None,
            "required_json_paths": spec.get("required_json_paths", []),
            "missing_json_paths": [],
            "status": "PASS",
        }
        if not exists or byte_size < min_bytes:
            item["status"] = "FAIL"

        if exists and spec.get("json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                item["json_valid"] = True
                missing = [p for p in item["required_json_paths"] if not _json_has_path(data, p)]
                item["missing_json_paths"] = missing
                if missing:
                    item["status"] = "FAIL"
            except (UnicodeDecodeError, json.JSONDecodeError):
                item["json_valid"] = False
                item["status"] = "FAIL"

        results.append(item)
        if item["status"] != "PASS":
            failures.append(item)

    return {
        "schema_version": "ukie_artifact_validation_v1",
        "status": "PASS" if not failures else "FAIL",
        "error_code": None if not failures else "ERROR_ARTIFACT_001",
        "job_dir": str(root),
        "files": results,
        "summary": {
            "expected": len(results),
            "passed": sum(1 for r in results if r["status"] == "PASS"),
            "failed": len(failures),
        },
    }


def analyze_only_contract() -> dict[str, Any]:
    return {
        "files": [
            {
                "name": "scene_before.json",
                "min_bytes": 32,
                "json": True,
                "required_json_paths": [
                    "schema_version",
                    "mode",
                    "blender_version",
                    "python_version",
                    "objects",
                ],
            },
            {"name": "stdout.log", "min_bytes": 1},
            {"name": "working.blend", "min_bytes": 64},
            {"name": "input.blend", "min_bytes": 64},
        ]
    }
