#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping


class PublicPriorRejected(ValueError):
    pass


EXPECTED_SCHEMAS = {
    "csmc_public_clip_3d_architecture_prior_v1",
    "csmc_public_clip_3d_architecture_prior_v2",
}
EXPECTED_LANE = "PUBLIC_EXTERNAL_ARCHITECTURE_CORROBORATION"
EXPECTED_STATUS = "PUBLIC_PRIOR_NOT_CSMC_PROOF"
EXPECTED_OBSERVED_FORMAT = ".clip"
EXPECTED_TARGET_FORMAT = ".csmc"

REQUIRED_CANDIDATE_NAMES = {
    "ExternalChunk",
    "ExternalTableAndColumnName",
    "Canvas3DModelBank",
    "Canvas3DModelLoader",
    "ModelData3D",
    "Manager3DOd",
}

V2_REQUIRED_NEGATIVE_CONTROLS = {
    "DECLARED_EXTERNAL_NAME_NOT_INSTANCE_PRESENCE",
    "TYPED_VIEW_NOT_INDEPENDENT_REPLICATION",
}


def _must_be_false(document: Mapping[str, Any], key: str) -> None:
    if document.get(key) is not False:
        raise PublicPriorRejected(f"{key} must be false")


def _source_repos(sources: Iterable[Mapping[str, Any]]) -> set[str]:
    repos = set()
    for source in sources:
        repo = source.get("repo")
        commit = source.get("commit")
        license_name = source.get("license")
        if not isinstance(repo, str) or "/" not in repo:
            raise PublicPriorRejected("every source requires repo owner/name")
        if not isinstance(commit, str) or len(commit) != 40:
            raise PublicPriorRejected(f"{repo}: commit must be a 40-char SHA")
        if not isinstance(license_name, str) or not license_name:
            raise PublicPriorRejected(f"{repo}: license required")
        repos.add(repo)
    return repos


def _validate_v2(document: Mapping[str, Any], sources: list[Mapping[str, Any]]) -> int:
    if document.get("independence_not_assumed") is not True:
        raise PublicPriorRejected("v2 requires independence_not_assumed=true")
    if len(sources) < 4:
        raise PublicPriorRejected("v2 requires at least four pinned public sources")

    controls = document.get("public_negative_controls")
    if not isinstance(controls, list) or not controls:
        raise PublicPriorRejected("v2 requires public_negative_controls")
    control_ids = {
        item.get("id")
        for item in controls
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    missing = sorted(V2_REQUIRED_NEGATIVE_CONTROLS - control_ids)
    if missing:
        raise PublicPriorRejected(f"v2 negative controls missing: {missing}")

    roles = {source.get("role") for source in sources}
    if "INDEPENDENT_REDERIVATION_WITH_MEASURED_NEGATIVE_CONTROL" not in roles:
        raise PublicPriorRejected("v2 requires a measured negative-control source")
    if "DEPENDENT_TYPED_SCHEMA_CORROBORATION" not in roles:
        raise PublicPriorRejected("v2 requires dependency-tagged typed corroboration")

    dependent = [
        source for source in sources if source.get("role") == "DEPENDENT_TYPED_SCHEMA_CORROBORATION"
    ]
    if any(not str(source.get("dependency_note") or "").strip() for source in dependent):
        raise PublicPriorRejected("dependency-tagged sources require dependency_note")

    return len(control_ids)


def validate_public_prior(document: Mapping[str, Any]) -> Dict[str, Any]:
    schema = document.get("schema")
    if schema not in EXPECTED_SCHEMAS:
        raise PublicPriorRejected("unexpected schema")
    if document.get("lane") != EXPECTED_LANE:
        raise PublicPriorRejected("unexpected lane")
    if document.get("status") != EXPECTED_STATUS:
        raise PublicPriorRejected("unexpected status")
    if document.get("observed_format") != EXPECTED_OBSERVED_FORMAT:
        raise PublicPriorRejected("observed_format must remain .clip")
    if document.get("target_format") != EXPECTED_TARGET_FORMAT:
        raise PublicPriorRejected("target_format must remain .csmc")

    for key in (
        "direct_csmc_evidence",
        "may_guide_blind_preregistration",
        "may_close_static_evidence_gate",
        "semantic_promotion",
        "blender_emit",
        "runtime_dispatch",
    ):
        _must_be_false(document, key)

    sources = document.get("sources")
    if not isinstance(sources, list) or len(sources) < 2:
        raise PublicPriorRejected("at least two public sources are required")
    repos = _source_repos(sources)

    prior = document.get("public_architecture_prior")
    if not isinstance(prior, dict):
        raise PublicPriorRejected("public_architecture_prior required")
    names = set(prior.get("candidate_public_names") or [])
    missing = sorted(REQUIRED_CANDIDATE_NAMES - names)
    if missing:
        raise PublicPriorRejected(f"candidate public-name set missing: {missing}")
    if prior.get("candidate_name_usage") != "POST_BLIND_NON_PROOF_CORROBORATION_ONLY":
        raise PublicPriorRejected("candidate names may only be used post-blind as non-proof corroboration")

    next_use = document.get("next_use")
    if not isinstance(next_use, dict) or next_use.get("blind_lane") != "UNCHANGED_AND_SEALED":
        raise PublicPriorRejected("blind lane must remain unchanged and sealed")

    dependency_warning = document.get("source_dependency_warning")
    if not isinstance(dependency_warning, str) or not dependency_warning.strip():
        raise PublicPriorRejected("source dependency warning required")

    negative_control_count = 0
    if schema == "csmc_public_clip_3d_architecture_prior_v2":
        negative_control_count = _validate_v2(document, sources)

    return {
        "schema": schema,
        "classification": "PUBLIC_CLIP_3D_ARCHITECTURE_PRIOR_VALID_NON_PROOF",
        "source_count": len(sources),
        "unique_repo_count": len(repos),
        "candidate_name_count": len(names),
        "negative_control_count": negative_control_count,
        "direct_csmc_evidence": False,
        "blind_preregistration_unchanged": True,
        "proof_grade": False,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate that public .clip architecture research remains a non-proof prior for CSMC."
    )
    ap.add_argument("manifest", type=Path)
    args = ap.parse_args()
    document = json.loads(args.manifest.read_text(encoding="utf-8"))
    print(json.dumps(validate_public_prior(document), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
