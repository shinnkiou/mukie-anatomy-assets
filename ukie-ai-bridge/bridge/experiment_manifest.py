"""Validated experiment lineage manifests for BP3D/CSMC model research.

The purpose is to make large fixture factories reproducible: each experiment has
one immutable identity, a parent/root lineage, input hash, toolchain metadata and
normally exactly one controlled change. A control experiment has zero changes.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any


EXPERIMENT_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_\-]{3,79}$")
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
ALLOWED_PROJECTS = {"BP3D", "CSMC", "MODELER", "VRM", "BLENDER", "BRIDGE_TEST"}
ALLOWED_CHANGE_TYPES = {
    "vertex_position",
    "uv",
    "bone_rotation",
    "bone_translation",
    "weight",
    "material_scalar",
    "material_color",
    "shape_key",
    "object_transform",
    "metadata",
}
FORBIDDEN_KEYS = {
    "shell",
    "powershell",
    "command",
    "argv",
    "arguments",
    "exe",
    "registry",
    "delete_path",
    "script_body",
}


class ExperimentManifestError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedExperiment:
    experiment_id: str
    project: str
    source_model_id: str
    source_sha256: str
    parent_experiment_id: str | None
    root_experiment_id: str
    generation: int
    control_group: bool
    change_type: str | None
    manifest_sha256: str


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def manifest_sha256(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _scan_forbidden(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise ExperimentManifestError(f"forbidden execution field at {path}.{key}")
            _scan_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            _scan_forbidden(child, f"{path}[{i}]")


def _valid_id(value: Any, label: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not EXPERIMENT_ID_RE.fullmatch(value):
        raise ExperimentManifestError(f"invalid {label}")
    return value


def validate_experiment_manifest(payload: dict[str, Any]) -> ValidatedExperiment:
    if not isinstance(payload, dict):
        raise ExperimentManifestError("experiment manifest must be an object")
    _scan_forbidden(payload)

    if payload.get("schema_version") != "ukie_experiment_v1":
        raise ExperimentManifestError("unsupported schema_version")

    experiment_id = _valid_id(payload.get("experiment_id"), "experiment_id")
    project = payload.get("project")
    if project not in ALLOWED_PROJECTS:
        raise ExperimentManifestError("project is not allowlisted")

    source = payload.get("source")
    if not isinstance(source, dict):
        raise ExperimentManifestError("source must be an object")
    source_model_id = source.get("model_id")
    if not isinstance(source_model_id, str) or not source_model_id.strip():
        raise ExperimentManifestError("missing source.model_id")
    source_sha = source.get("sha256")
    if not isinstance(source_sha, str) or not SHA256_RE.fullmatch(source_sha):
        raise ExperimentManifestError("invalid source.sha256")

    parent_id = _valid_id(payload.get("parent_experiment_id"), "parent_experiment_id", optional=True)
    root_id = _valid_id(payload.get("root_experiment_id") or experiment_id, "root_experiment_id")
    generation = payload.get("generation", 0)
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0 or generation > 10000:
        raise ExperimentManifestError("invalid generation")
    if generation == 0 and parent_id is not None:
        raise ExperimentManifestError("generation 0 cannot have a parent")
    if generation > 0 and parent_id is None:
        raise ExperimentManifestError("non-root experiment requires parent_experiment_id")

    control_group = bool(payload.get("control_group", False))
    changes = payload.get("changes", [])
    if not isinstance(changes, list):
        raise ExperimentManifestError("changes must be an array")
    if control_group:
        if changes:
            raise ExperimentManifestError("control experiment must have zero changes")
        change_type = None
    else:
        if len(changes) != 1:
            raise ExperimentManifestError("non-control experiment must contain exactly one controlled change")
        change = changes[0]
        if not isinstance(change, dict):
            raise ExperimentManifestError("change must be an object")
        change_type = change.get("type")
        if change_type not in ALLOWED_CHANGE_TYPES:
            raise ExperimentManifestError("change type is not allowlisted")
        target = change.get("target")
        if not isinstance(target, dict) or not target:
            raise ExperimentManifestError("change target must be a non-empty object")
        if not any(k in change for k in ("before", "after", "delta")):
            raise ExperimentManifestError("change requires before/after/delta evidence")

    toolchain = payload.get("toolchain")
    if not isinstance(toolchain, dict) or not toolchain:
        raise ExperimentManifestError("toolchain metadata is required")
    if "bridge_version" not in toolchain:
        raise ExperimentManifestError("toolchain.bridge_version is required")

    return ValidatedExperiment(
        experiment_id=experiment_id,
        project=project,
        source_model_id=source_model_id,
        source_sha256=source_sha.lower(),
        parent_experiment_id=parent_id,
        root_experiment_id=root_id,
        generation=generation,
        control_group=control_group,
        change_type=change_type,
        manifest_sha256=manifest_sha256(payload),
    )
