"""Cloud-side discovery/intake contract for UKIE AI BRIDGE acceptance evidence.

This module does not talk to Google Drive directly. It validates metadata returned by
a cloud connector and the three downloaded files produced by the local handoff:

  <acceptance>.zip
  <acceptance>.zip.sha256
  <acceptance>.zip.handoff.json

Discovery itself is non-mutating and idempotent. A complete triplet is only eligible
for readback verification when each basename is unique, no .partial file is used,
and all handoff/release/SHA claims agree. Release promotion is always a later gate.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from .acceptance_verifier import AcceptanceVerificationError, verify_acceptance_bundle
    from .validator import sha256_file
except ImportError:
    from acceptance_verifier import AcceptanceVerificationError, verify_acceptance_bundle
    from validator import sha256_file


HANDOFF_SCHEMA = "ukie_acceptance_handoff_v1"
INTAKE_SCHEMA = "ukie_cloud_intake_v1"
DISCOVERY_SCHEMA = "ukie_cloud_discovery_v1"
PREFIX = "UKIE_PHYSICAL_ACCEPTANCE__"
HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
SAFE_FILENAME = re.compile(r"^UKIE_PHYSICAL_ACCEPTANCE__[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+\.zip$")


class CloudIntakeError(ValueError):
    pass


@dataclass(frozen=True)
class Candidate:
    file_id: str
    name: str
    size: int | None = None
    modified_time: str | None = None


def _as_candidate(value: Any) -> Candidate | None:
    if not isinstance(value, dict):
        return None
    file_id = str(value.get("id") or value.get("file_id") or "").strip()
    name = str(value.get("name") or value.get("file_name") or value.get("title") or "").strip()
    if not file_id or not name:
        return None
    size_value = value.get("size") if value.get("size") is not None else value.get("file_size_bytes")
    size = int(size_value) if isinstance(size_value, int) and not isinstance(size_value, bool) and size_value >= 0 else None
    modified = value.get("modifiedTime") or value.get("modified_time")
    return Candidate(file_id=file_id, name=name, size=size, modified_time=str(modified) if modified else None)


def _base_from_name(name: str) -> tuple[str | None, str | None]:
    if name.endswith(".partial") or ".partial." in name:
        return None, "PARTIAL_IGNORED"
    if name.endswith(".zip.handoff.json"):
        return name[: -len(".handoff.json")], "handoff"
    if name.endswith(".zip.sha256"):
        return name[: -len(".sha256")], "sha256"
    if name.endswith(".zip"):
        return name, "zip"
    return None, None


def classify_discovery(files: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Group Drive metadata into complete/incomplete/ambiguous acceptance triplets."""
    groups: dict[str, dict[str, list[Candidate]]] = {}
    ignored: list[dict[str, str]] = []

    for raw in files:
        item = _as_candidate(raw)
        if item is None:
            continue
        base, kind = _base_from_name(item.name)
        if kind == "PARTIAL_IGNORED":
            ignored.append({"file_id": item.file_id, "name": item.name, "reason": kind})
            continue
        if base is None or kind is None or not base.startswith(PREFIX):
            continue
        if not SAFE_FILENAME.fullmatch(base):
            ignored.append({"file_id": item.file_id, "name": item.name, "reason": "UNSAFE_OR_UNEXPECTED_NAME"})
            continue
        bucket = groups.setdefault(base, {"zip": [], "sha256": [], "handoff": []})
        bucket[kind].append(item)

    complete: list[dict[str, Any]] = []
    incomplete: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []

    for base in sorted(groups):
        bucket = groups[base]
        counts = {kind: len(bucket[kind]) for kind in ("zip", "sha256", "handoff")}
        row = {
            "base_name": base,
            "counts": counts,
            "file_ids": {kind: [x.file_id for x in bucket[kind]] for kind in bucket},
        }
        if any(counts[k] > 1 for k in counts):
            row["status"] = "AMBIGUOUS"
            ambiguous.append(row)
        elif all(counts[k] == 1 for k in counts):
            row["status"] = "COMPLETE"
            row["triplet"] = {kind: bucket[kind][0].__dict__ for kind in bucket}
            complete.append(row)
        else:
            row["status"] = "INCOMPLETE"
            row["missing"] = [kind for kind, count in counts.items() if count == 0]
            incomplete.append(row)

    status = "WAITING_FOR_SYNC" if not groups else "DISCOVERED"
    return {
        "schema_version": DISCOVERY_SCHEMA,
        "status": status,
        "complete": complete,
        "incomplete": incomplete,
        "ambiguous": ambiguous,
        "ignored": ignored,
        "complete_count": len(complete),
        "incomplete_count": len(incomplete),
        "ambiguous_count": len(ambiguous),
        "ready_for_ai": False,
        "promotion_performed": False,
    }


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CloudIntakeError(f"{label} is unreadable: {exc}") from exc
    if not isinstance(value, dict):
        raise CloudIntakeError(f"{label} must contain a JSON object")
    return value


def _parse_sha_sidecar(path: Path) -> tuple[str, str]:
    try:
        text = path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeDecodeError) as exc:
        raise CloudIntakeError(f"SHA sidecar is unreadable: {exc}") from exc
    match = re.fullmatch(r"([0-9a-fA-F]{64})  ([A-Za-z0-9_.-]+\.zip)", text)
    if not match:
        raise CloudIntakeError("SHA sidecar format is invalid")
    return match.group(1).lower(), match.group(2)


def _provider_metadata(value: Any) -> dict[str, Any]:
    data = value if isinstance(value, dict) else {}
    provider = str(data.get("provider") or "").upper()
    file_ids = data.get("file_ids") if isinstance(data.get("file_ids"), dict) else {}
    required = {"zip", "sha256", "handoff"}
    if provider != "GOOGLE_DRIVE":
        raise CloudIntakeError("provider metadata must explicitly identify GOOGLE_DRIVE")
    if any(not isinstance(file_ids.get(k), str) or not file_ids.get(k).strip() for k in required):
        raise CloudIntakeError("provider metadata is missing one or more Drive file IDs")
    if len(set(file_ids[k] for k in required)) != 3:
        raise CloudIntakeError("provider metadata Drive file IDs must be distinct")
    return {"provider": provider, "file_ids": {k: file_ids[k] for k in sorted(required)}, "fetched_at": data.get("fetched_at")}


def verify_cloud_intake(
    bundle: str | Path,
    sha_sidecar: str | Path,
    handoff_json: str | Path,
    *,
    provider_metadata: dict[str, Any] | None = None,
    expected_release_key: str | None = None,
    allow_synthetic_test_fixture: bool = False,
) -> dict[str, Any]:
    """Validate one downloaded triplet. No release or Base44 mutation occurs here."""
    bundle_path = Path(bundle)
    sha_path = Path(sha_sidecar)
    handoff_path = Path(handoff_json)
    for path, label in ((bundle_path, "acceptance ZIP"), (sha_path, "SHA sidecar"), (handoff_path, "handoff JSON")):
        if not path.is_file():
            raise CloudIntakeError(f"{label} is missing: {path}")

    if not SAFE_FILENAME.fullmatch(bundle_path.name):
        raise CloudIntakeError("acceptance ZIP filename is outside the handoff naming contract")
    if sha_path.name != bundle_path.name + ".sha256":
        raise CloudIntakeError("SHA sidecar filename does not match acceptance ZIP")
    if handoff_path.name != bundle_path.name + ".handoff.json":
        raise CloudIntakeError("handoff JSON filename does not match acceptance ZIP")

    receipt = _load_json(handoff_path, "handoff JSON")
    if receipt.get("schema_version") != HANDOFF_SCHEMA:
        raise CloudIntakeError("handoff schema is unsupported")
    if receipt.get("status") != "LOCAL_HANDOFF_COMPLETE":
        raise CloudIntakeError("handoff did not finish locally")
    if receipt.get("file_name") != bundle_path.name:
        raise CloudIntakeError("handoff file_name does not match downloaded ZIP")
    if receipt.get("sync_folder_copy_proven") is not True:
        raise CloudIntakeError("handoff does not prove the local sync-folder copy")
    for field in ("drive_cloud_presence_proven", "drive_readback_proven", "ready_for_ai", "promotion_performed"):
        if receipt.get(field) is not False:
            raise CloudIntakeError(f"local handoff illegally pre-claims {field}")

    release_key = receipt.get("release_key")
    acceptance_id = receipt.get("acceptance_id")
    bridge_version = receipt.get("bridge_version")
    commit_sha = receipt.get("commit_sha")
    workflow_run_id = receipt.get("workflow_run_id")
    if not isinstance(release_key, str) or not release_key.startswith("BRIDGE_P"):
        raise CloudIntakeError("handoff release_key is invalid")
    if expected_release_key is not None and release_key != expected_release_key:
        raise CloudIntakeError("handoff release_key does not match expected release")
    if not isinstance(acceptance_id, str) or not acceptance_id.startswith("PHYSICAL_ACCEPTANCE_"):
        raise CloudIntakeError("handoff acceptance_id is invalid")
    if not isinstance(bridge_version, str) or not bridge_version.strip():
        raise CloudIntakeError("handoff bridge_version is missing")
    if not isinstance(commit_sha, str) or not HEX40.fullmatch(commit_sha):
        raise CloudIntakeError("handoff commit_sha is invalid")
    if not isinstance(workflow_run_id, int) or isinstance(workflow_run_id, bool) or workflow_run_id <= 0:
        raise CloudIntakeError("handoff workflow_run_id is invalid")

    sidecar_sha, sidecar_name = _parse_sha_sidecar(sha_path)
    if sidecar_name != bundle_path.name:
        raise CloudIntakeError("SHA sidecar targets a different ZIP")
    receipt_sha = receipt.get("sha256")
    receipt_size = receipt.get("byte_size")
    if not isinstance(receipt_sha, str) or not HEX64.fullmatch(receipt_sha):
        raise CloudIntakeError("handoff SHA-256 is invalid")
    if not isinstance(receipt_size, int) or isinstance(receipt_size, bool) or receipt_size <= 0:
        raise CloudIntakeError("handoff byte_size is invalid")
    actual_sha = sha256_file(bundle_path).lower()
    actual_size = bundle_path.stat().st_size
    if len({sidecar_sha, receipt_sha.lower(), actual_sha}) != 1:
        raise CloudIntakeError("Drive readback SHA does not agree with handoff/sidecar")
    if actual_size != receipt_size:
        raise CloudIntakeError("Drive readback size does not agree with handoff")

    try:
        acceptance = verify_acceptance_bundle(
            bundle_path,
            expected_sha256=actual_sha,
            expected_release_key=release_key,
            allow_synthetic_test_fixture=allow_synthetic_test_fixture,
        )
    except AcceptanceVerificationError as exc:
        raise CloudIntakeError(f"acceptance evidence verification failed: {exc}") from exc

    if acceptance.get("acceptance_id") != acceptance_id:
        raise CloudIntakeError("handoff and Acceptance ZIP acceptance_id disagree")
    release = acceptance.get("release") if isinstance(acceptance.get("release"), dict) else {}
    if release.get("release_key") != release_key:
        raise CloudIntakeError("handoff and Acceptance ZIP release_key disagree")
    if release.get("bridge_version") != bridge_version:
        raise CloudIntakeError("handoff and Acceptance ZIP bridge_version disagree")
    if release.get("commit_sha") != commit_sha:
        raise CloudIntakeError("handoff and Acceptance ZIP commit_sha disagree")
    if release.get("workflow_run_id") != workflow_run_id:
        raise CloudIntakeError("handoff and Acceptance ZIP workflow_run_id disagree")

    provider = None
    drive_readback = False
    if provider_metadata is not None:
        provider = _provider_metadata(provider_metadata)
        drive_readback = True

    return {
        "schema_version": INTAKE_SCHEMA,
        "status": "DRIVE_READBACK_VERIFIED" if drive_readback else "CLOUD_INTAKE_LOCAL_VALID",
        "acceptance_id": acceptance_id,
        "release_key": release_key,
        "bridge_version": bridge_version,
        "commit_sha": commit_sha,
        "workflow_run_id": workflow_run_id,
        "file_name": bundle_path.name,
        "byte_size": actual_size,
        "sha256": actual_sha,
        "triplet_verified": True,
        "acceptance_evidence_status": acceptance.get("status"),
        "local_core_ready": receipt.get("local_core_ready") is True,
        "local_gpu_render_ready": receipt.get("local_gpu_render_ready") is True,
        "cloud_presence_proven": drive_readback,
        "drive_readback_proven": drive_readback,
        "provider": provider,
        "physical_provenance": acceptance.get("physical_provenance") is True,
        "ready_for_ai": False,
        "promotion_performed": False,
        "next_gate": "REGISTER_CLOUD_INTAKE_THEN_RELEASE_PROMOTION_EVALUATION" if drive_readback else "BIND_PROVIDER_READBACK_METADATA",
    }
