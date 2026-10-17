"""Validation primitives for one-click Tool Scout approvals.

An approval manifest is an authorization envelope, not an installer script.
It records what the user approved. It intentionally cannot carry shell commands,
arbitrary executable paths, registry edits, or other general-purpose execution.

The Bridge may later resolve approved tools to exact versions/downloads, but only
if the resolved source remains within the hard-coded tool policy below. Adding a
new executable tool therefore requires a reviewed Bridge update, even if AI can
add it to the Base44 candidate list for consideration.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

BATCH_KEY_RE = re.compile(r"^[A-Z0-9_\-]{4,100}$")
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
MAX_TOOLS_PER_BATCH = 64
ALLOWED_SOURCE_TYPES = {
    "winget",
    "official_portable",
    "official_installer",
    "existing_only",
    "manual",
}
FORBIDDEN_KEYS = {
    "shell",
    "powershell",
    "command",
    "arguments",
    "argv",
    "registry",
    "delete_path",
    "arbitrary_exe",
    "script_body",
}

# Execution policy, intentionally narrower than the Base44 candidate catalog.
# AI may suggest other tools in Base44; the Windows Bridge will not resolve or
# install them until this policy is deliberately extended in a reviewed build.
TOOL_POLICY: dict[str, dict[str, Any]] = {
    "blender_bp3d_4_2_23": {
        "domains": {"blender.org", "www.blender.org", "download.blender.org"},
        "source_types": {"official_portable"},
    },
    "python_research": {
        "domains": {"python.org", "www.python.org", "pythonhosted.org", "github.com", "astral.sh"},
        "source_types": {"official_portable"},
    },
    "sqlite_tools": {
        "domains": {"sqlite.org", "www.sqlite.org"},
        "source_types": {"official_portable"},
    },
    "sevenzip": {
        "domains": {"7-zip.org", "www.7-zip.org"},
        "source_types": {"winget", "official_portable"},
        "package_ids": {"7zip.7zip"},
    },
    "git": {
        "domains": {"git-scm.com", "github.com"},
        "source_types": {"winget", "official_installer", "official_portable"},
        "package_ids": {"Git.Git"},
    },
    "everything": {
        "domains": {"voidtools.com", "www.voidtools.com"},
        "source_types": {"official_portable", "official_installer"},
    },
    "ffmpeg": {
        "domains": {"ffmpeg.org", "www.ffmpeg.org"},
        "source_types": {"official_portable"},
    },
    "sysinternals": {
        "domains": {"learn.microsoft.com", "download.sysinternals.com"},
        "source_types": {"official_portable"},
    },
    "x64dbg": {
        "domains": {"x64dbg.com", "www.x64dbg.com", "github.com"},
        "source_types": {"official_portable"},
    },
    "ghidra": {
        "domains": {"github.com", "ghidra-sre.org"},
        "source_types": {"official_portable"},
    },
    "renderdoc": {
        "domains": {"renderdoc.org", "www.renderdoc.org", "github.com"},
        "source_types": {"official_installer", "official_portable"},
    },
}


class InstallManifestError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedApprovalManifest:
    batch_key: str
    approved_at: str
    tool_keys: tuple[str, ...]
    manifest_sha256: str
    requires_uac: bool
    requires_driver: bool


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _scan_forbidden(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise InstallManifestError(f"forbidden execution field at {path}.{key}")
            _scan_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            _scan_forbidden(child, f"{path}[{idx}]")


def _https_host(url: str) -> str:
    if not isinstance(url, str) or not url:
        raise InstallManifestError("official_url is required")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise InstallManifestError("official_url must be an https URL")
    return parsed.hostname.lower()


def validate_approval_manifest(payload: dict[str, Any]) -> ValidatedApprovalManifest:
    if not isinstance(payload, dict):
        raise InstallManifestError("manifest root must be an object")
    _scan_forbidden(payload)

    if payload.get("schema_version") != "ukie_install_approval_v1":
        raise InstallManifestError("unsupported schema_version")

    batch_key = payload.get("batch_key")
    if not isinstance(batch_key, str) or not BATCH_KEY_RE.fullmatch(batch_key):
        raise InstallManifestError("invalid batch_key")

    approved_at = payload.get("approved_at")
    if not isinstance(approved_at, str) or not approved_at:
        raise InstallManifestError("approved_at is required")

    tools = payload.get("tools")
    if not isinstance(tools, list) or not tools or len(tools) > MAX_TOOLS_PER_BATCH:
        raise InstallManifestError("tools must be a non-empty bounded list")

    seen: set[str] = set()
    requires_uac = False
    requires_driver = False
    for tool in tools:
        if not isinstance(tool, dict):
            raise InstallManifestError("each tool must be an object")
        tool_key = tool.get("tool_key")
        if not isinstance(tool_key, str) or tool_key not in TOOL_POLICY:
            raise InstallManifestError(f"tool is not Bridge-allowlisted: {tool_key!r}")
        if tool_key in seen:
            raise InstallManifestError(f"duplicate tool_key: {tool_key}")
        seen.add(tool_key)

        policy = TOOL_POLICY[tool_key]
        source_type = tool.get("source_type")
        if source_type not in ALLOWED_SOURCE_TYPES or source_type not in policy["source_types"]:
            raise InstallManifestError(f"source_type not allowed for {tool_key}")

        host = _https_host(tool.get("official_url"))
        if host not in policy["domains"]:
            raise InstallManifestError(f"official_url host not allowlisted for {tool_key}: {host}")

        package_id = tool.get("package_id")
        if source_type == "winget":
            allowed_ids = policy.get("package_ids", set())
            if not isinstance(package_id, str) or package_id not in allowed_ids:
                raise InstallManifestError(f"winget package_id not allowlisted for {tool_key}")

        if not isinstance(tool.get("version_policy"), str) or not tool["version_policy"]:
            raise InstallManifestError(f"version_policy missing for {tool_key}")
        if not isinstance(tool.get("recommended_version"), str) or not tool["recommended_version"]:
            raise InstallManifestError(f"recommended_version missing for {tool_key}")

        requires_uac = requires_uac or bool(tool.get("requires_admin"))
        requires_driver = requires_driver or bool(tool.get("requires_driver"))

    digest = sha256_json(payload)
    return ValidatedApprovalManifest(
        batch_key=batch_key,
        approved_at=approved_at,
        tool_keys=tuple(tool["tool_key"] for tool in tools),
        manifest_sha256=digest,
        requires_uac=requires_uac,
        requires_driver=requires_driver,
    )


def validate_resolved_manifest(
    payload: dict[str, Any],
    approval_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Validate a future resolver result against the user's frozen approval.

    This still performs no installation. Portable/installer downloads require an
    exact SHA-256. Winget entries require an exact allowlisted package ID/version.
    Any source escalation outside the frozen approval is rejected.
    """
    approval = validate_approval_manifest(approval_manifest)
    if not isinstance(payload, dict):
        raise InstallManifestError("resolved manifest root must be an object")
    _scan_forbidden(payload)
    if payload.get("schema_version") != "ukie_install_resolution_v1":
        raise InstallManifestError("unsupported resolved schema_version")
    if payload.get("approval_manifest_sha256") != approval.manifest_sha256:
        raise InstallManifestError("resolved manifest is not bound to frozen approval")

    approved_tools = {t["tool_key"]: t for t in approval_manifest["tools"]}
    resolved_tools = payload.get("tools")
    if not isinstance(resolved_tools, list) or len(resolved_tools) != len(approved_tools):
        raise InstallManifestError("resolved tool set differs from approval")

    for tool in resolved_tools:
        if not isinstance(tool, dict):
            raise InstallManifestError("each resolved tool must be an object")
        key = tool.get("tool_key")
        if key not in approved_tools:
            raise InstallManifestError(f"resolved tool was not approved: {key!r}")
        approved = approved_tools[key]
        if tool.get("source_type") != approved.get("source_type"):
            raise InstallManifestError(f"source_type escalation for {key}")
        if not isinstance(tool.get("version"), str) or not tool["version"]:
            raise InstallManifestError(f"exact version missing for {key}")

        policy = TOOL_POLICY[key]
        if tool["source_type"] == "winget":
            package_id = tool.get("package_id")
            if package_id != approved.get("package_id") or package_id not in policy.get("package_ids", set()):
                raise InstallManifestError(f"resolved winget package mismatch for {key}")
        elif tool["source_type"] in {"official_portable", "official_installer"}:
            download_url = tool.get("download_url")
            host = _https_host(download_url)
            if host not in policy["domains"]:
                raise InstallManifestError(f"resolved download host not allowlisted for {key}: {host}")
            digest = tool.get("sha256")
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                raise InstallManifestError(f"exact SHA-256 missing for {key}")

    return {
        "status": "VALID",
        "approval_manifest_sha256": approval.manifest_sha256,
        "resolved_manifest_sha256": sha256_json(payload),
        "tool_count": len(resolved_tools),
    }
