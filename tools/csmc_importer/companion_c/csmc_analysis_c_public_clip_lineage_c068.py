from __future__ import annotations

from typing import Any, Dict, Mapping


class PublicClipSourceLineageRejected(ValueError):
    pass


EXPECTED_SOURCES = {
    "Aodaruma/clipfile-rs": "bd88467fa80e63ad48c6c713fbfb5a8a116d798a",
    "youichi-uda/clip-clai": "76edfbf393868687107c2cdfdb750a70ca9ba7fe",
    "LavenderSnek/clipdecode": "e5347a65202bc399bdd730d13187bc32aabdd4fa",
    "wamsoft/clipparse": "322a273c0e059d1dee9132af78289efa12a59522",
    "al3ks1s/clip-tools": "e1d3d7ed4701ac84e9220127daa73c2cf90dd803",
}

KNOWN_DEPENDENT = {
    "youichi-uda/clip-clai",
    "wamsoft/clipparse",
    "al3ks1s/clip-tools",
}
UNKNOWN_INDEPENDENCE = {
    "Aodaruma/clipfile-rs",
    "LavenderSnek/clipdecode",
}
EMPIRICALLY_REVALIDATED = {
    "Aodaruma/clipfile-rs",
    "youichi-uda/clip-clai",
    "wamsoft/clipparse",
}


def reconcile_public_clip_source_lineage(record: Mapping[str, Any]) -> Dict[str, Any]:
    if record.get("schema_version") != "csmc_analysis_c_public_clip_source_lineage_c068_record_v1":
        raise PublicClipSourceLineageRejected("wrong schema")
    if record.get("run_id") != "C-068" or record.get("status") != "COMPLETED":
        raise PublicClipSourceLineageRejected("wrong run identity/state")

    sources = record.get("pinned_sources")
    if not isinstance(sources, list) or len(sources) != 5:
        raise PublicClipSourceLineageRejected("exact five pinned public sources required")

    seen: Dict[str, Mapping[str, Any]] = {}
    for source in sources:
        if not isinstance(source, Mapping):
            raise PublicClipSourceLineageRejected("source must be an object")
        repo = source.get("repo")
        if repo in seen:
            raise PublicClipSourceLineageRejected("duplicate source")
        seen[str(repo)] = source

    if set(seen) != set(EXPECTED_SOURCES):
        raise PublicClipSourceLineageRejected("source set changed")
    for repo, commit in EXPECTED_SOURCES.items():
        if seen[repo].get("commit") != commit:
            raise PublicClipSourceLineageRejected(f"source pin changed: {repo}")

    for repo in KNOWN_DEPENDENT:
        if seen[repo].get("origin_independence") != "KNOWN_DERIVED_NOT_COUNTED":
            raise PublicClipSourceLineageRejected(f"known dependency misclassified: {repo}")
    for repo in UNKNOWN_INDEPENDENCE:
        if seen[repo].get("origin_independence") != "UNKNOWN_NOT_COUNTED":
            raise PublicClipSourceLineageRejected(f"unknown lineage must not be promoted: {repo}")
    for repo in EMPIRICALLY_REVALIDATED:
        if seen[repo].get("empirical_revalidation") is not True:
            raise PublicClipSourceLineageRejected(f"empirical revalidation lost: {repo}")

    wamsoft = seen["wamsoft/clipparse"]
    if "animeops/clip-tools" not in set(wamsoft.get("upstream_sources") or []):
        raise PublicClipSourceLineageRejected("wamsoft starting-point dependency missing")
    if wamsoft.get("corrected_role") != "DEPENDENT_STARTING_POINT_WITH_INDEPENDENT_REAL_FILE_REVALIDATION":
        raise PublicClipSourceLineageRejected("wamsoft role correction missing")

    clai = seen["youichi-uda/clip-clai"]
    if len(clai.get("upstream_sources") or []) < 4:
        raise PublicClipSourceLineageRejected("clip-clai community-source lineage incomplete")

    accounting = record.get("independence_accounting")
    if not isinstance(accounting, Mapping):
        raise PublicClipSourceLineageRejected("missing independence accounting")
    expected_counts = {
        "pinned_source_count": 5,
        "guaranteed_origin_independent_source_count": 0,
        "known_origin_dependent_source_count": 3,
        "origin_independence_unknown_source_count": 2,
        "empirical_revalidation_source_count": 3,
    }
    for key, value in expected_counts.items():
        if accounting.get(key) != value:
            raise PublicClipSourceLineageRejected(f"bad independence count: {key}")

    effect = record.get("prior_effect")
    if not isinstance(effect, Mapping):
        raise PublicClipSourceLineageRejected("missing prior effect")
    if effect.get("external_id_indirection_for_clip") != "STRONG_CORROBORATED_STRUCTURAL_PRIOR_RETAINED":
        raise PublicClipSourceLineageRejected("structural prior changed unexpectedly")
    if effect.get("candidate_name_usage") != "POST_BLIND_NON_PROOF_CORROBORATION_ONLY":
        raise PublicClipSourceLineageRejected("public-name quarantine changed")
    for key in ("direct_csmc_evidence", "proof_grade", "static_evidence_gate_closed", "blender_emit_ready"):
        if effect.get(key) is not False:
            raise PublicClipSourceLineageRejected(f"{key} must remain false")
    if effect.get("semantic_promotion_count") != 0:
        raise PublicClipSourceLineageRejected("semantic promotion forbidden")
    if effect.get("physical_f02_oracle_observations") != 0 or effect.get("physical_f02_oracle_total") != 30:
        raise PublicClipSourceLineageRejected("physical oracle state changed without observation")

    isolation = record.get("isolation")
    if not isinstance(isolation, Mapping):
        raise PublicClipSourceLineageRejected("missing isolation")
    if isolation.get("blind_preregistration_unchanged") is not True:
        raise PublicClipSourceLineageRejected("blind preregistration changed")
    forbidden_true = (
        "public_names_may_guide_blind_discovery",
        "public_names_may_score_blind_result",
        "runtime_dispatch",
        "modeler_execution",
        "save_or_serialization_trigger",
        "mainline_mutation",
        "rio26_mutation",
        "worker_canary_control_gate_mutation",
        "production_stable_mutation",
        "raw_private_publication",
    )
    for key in forbidden_true:
        if isolation.get(key) is not False:
            raise PublicClipSourceLineageRejected(f"isolation violation: {key}")

    return {
        "schema_version": "csmc_analysis_c_public_clip_source_lineage_c068_result_v1",
        "classification": "PUBLIC_CLIP_SOURCE_LINEAGE_RECONCILED_INDEPENDENCE_DOWNGRADED_NON_PROOF",
        "pinned_source_count": 5,
        "guaranteed_origin_independent_source_count": 0,
        "known_origin_dependent_source_count": 3,
        "origin_independence_unknown_source_count": 2,
        "empirical_revalidation_source_count": 3,
        "structural_prior_retained": True,
        "source_count_may_be_used_as_independent_vote_count": False,
        "direct_csmc_evidence": False,
        "proof_grade": False,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "mainline_mutation": False,
        "rio26_mutation": False,
    }
