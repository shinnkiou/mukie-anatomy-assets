from __future__ import annotations

from typing import Any, Dict, Mapping


class PublicClipPriorReconciliationRejected(ValueError):
    pass


EXPECTED_SCHEMA = "csmc_public_clip_3d_architecture_prior_v1"
EXPECTED_LANE = "PUBLIC_EXTERNAL_ARCHITECTURE_CORROBORATION"
EXPECTED_STATUS = "PUBLIC_PRIOR_NOT_CSMC_PROOF"
EXPECTED_SOURCES = {
    "Aodaruma/clipfile-rs": ("bd88467fa80e63ad48c6c713fbfb5a8a116d798a", "MIT"),
    "youichi-uda/clip-clai": ("76edfbf393868687107c2cdfdb750a70ca9ba7fe", "MIT"),
    "LavenderSnek/clipdecode": ("e5347a65202bc399bdd730d13187bc32aabdd4fa", "LGPL-2.1"),
}
REQUIRED_NAMES = {
    "ExternalChunk", "ExternalTableAndColumnName", "Canvas3DModelBank",
    "Canvas3DModelLoader", "ModelData3D", "Manager3DOd",
}


def reconcile_public_clip_prior(
    prior: Mapping[str, Any],
    *,
    blind_result_sealed: bool = False,
    blind_result: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    if prior.get("schema") != EXPECTED_SCHEMA or prior.get("lane") != EXPECTED_LANE:
        raise PublicClipPriorReconciliationRejected("wrong prior schema/lane")
    if prior.get("status") != EXPECTED_STATUS:
        raise PublicClipPriorReconciliationRejected("wrong prior status")
    if prior.get("observed_format") != ".clip" or prior.get("target_format") != ".csmc":
        raise PublicClipPriorReconciliationRejected("format boundary changed")
    for key in (
        "direct_csmc_evidence", "may_guide_blind_preregistration",
        "may_close_static_evidence_gate", "semantic_promotion",
        "blender_emit", "runtime_dispatch",
    ):
        if prior.get(key) is not False:
            raise PublicClipPriorReconciliationRejected(f"{key} must remain false")

    sources = prior.get("sources")
    if not isinstance(sources, list) or len(sources) != 3:
        raise PublicClipPriorReconciliationRejected("expected exact three-source public prior")
    seen = {}
    for source in sources:
        if not isinstance(source, Mapping):
            raise PublicClipPriorReconciliationRejected("source row must be object")
        repo = source.get("repo")
        seen[repo] = (source.get("commit"), source.get("license"))
    if seen != EXPECTED_SOURCES:
        raise PublicClipPriorReconciliationRejected("source pin/license set mismatch")

    architecture = prior.get("public_architecture_prior")
    if not isinstance(architecture, Mapping):
        raise PublicClipPriorReconciliationRejected("missing architecture prior")
    if architecture.get("candidate_name_usage") != "POST_BLIND_NON_PROOF_CORROBORATION_ONLY":
        raise PublicClipPriorReconciliationRejected("public names must remain post-blind only")
    names = set(architecture.get("candidate_public_names") or [])
    if not REQUIRED_NAMES.issubset(names):
        raise PublicClipPriorReconciliationRejected("required corroboration names missing")

    next_use = prior.get("next_use")
    if not isinstance(next_use, Mapping) or next_use.get("blind_lane") != "UNCHANGED_AND_SEALED":
        raise PublicClipPriorReconciliationRejected("blind preregistration must remain sealed")
    warning = prior.get("source_dependency_warning")
    if not isinstance(warning, str) or not warning.strip():
        raise PublicClipPriorReconciliationRejected("source dependency warning required")

    matched_names = []
    state = "PUBLIC_PRIOR_ADMITTED_QUARANTINED_PENDING_BLIND_RESULT"
    if blind_result_sealed:
        if not isinstance(blind_result, Mapping):
            raise PublicClipPriorReconciliationRejected("sealed blind result summary required")
        if blind_result.get("schema_version") != "csmc_blind_static_result_summary_v1":
            raise PublicClipPriorReconciliationRejected("wrong blind result schema")
        if blind_result.get("sealed") is not True or blind_result.get("discovery_basis") != "BLIND_DIRECT_DATA_FLOW":
            raise PublicClipPriorReconciliationRejected("blind result must be independently sealed direct-data-flow output")
        if blind_result.get("used_public_prior_during_discovery") is not False:
            raise PublicClipPriorReconciliationRejected("blind result contaminated by public prior")
        path_tokens = set(blind_result.get("path_tokens") or [])
        matched_names = sorted(path_tokens & names)
        state = (
            "POST_BLIND_NON_PROOF_CORROBORATION_MATCH_AVAILABLE"
            if matched_names
            else "POST_BLIND_NO_PUBLIC_PRIOR_MATCH_DO_NOT_FORCE"
        )

    return {
        "schema_version": "csmc_analysis_c_public_clip_prior_reconciliation_c067_v1",
        "classification": state,
        "source_count": 3,
        "candidate_public_name_count": len(names),
        "matched_public_names": matched_names,
        "blind_result_sealed": blind_result_sealed,
        "blind_discovery_may_use_public_prior": False,
        "post_blind_corroboration_only": True,
        "direct_csmc_evidence": False,
        "proof_grade": False,
        "static_evidence_gate_closed": False,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "mainline_mutation": False,
        "rio26_mutation": False,
    }
