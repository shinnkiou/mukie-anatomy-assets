#!/usr/bin/env python3
"""Companion C C-066 fail-closed reconciliation for hardened F02 oracle intake.

This validator covers infrastructure/provenance only. It must not be used to infer
serializer or mesh semantics, and it deliberately requires zero physical oracle
observations for this C-066 state snapshot.
"""

SOURCE_BATCH_ID = "CSMC_F02_SINGLE_BYTE_XOR01_30_20260914"
SOURCE_MANIFEST_SHA256 = "751f05dfff9d5308dfd96421d5bce43e6785de2cb385fb28a8c97c565c6cc891"
EXPECTED_VARIANT_COUNT = 30


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    if record.get("pipeline_stage") != "STRUCTURAL_ONLY":
        errors.append("pipeline must remain STRUCTURAL_ONLY")
    if record.get("source_batch_id") != SOURCE_BATCH_ID:
        errors.append("source batch mismatch")
    if record.get("source_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256:
        errors.append("source manifest raw SHA mismatch")
    if record.get("source_manifest_raw_sha_bound") is not True:
        errors.append("raw manifest SHA binding required")
    if record.get("verify_raw_sha_before_json_parse") is not True:
        errors.append("raw SHA must be verified before JSON parsing")
    if record.get("expected_variant_count") != EXPECTED_VARIANT_COUNT:
        errors.append("variant count must remain exactly 30")
    if record.get("existing_observation_contract_preserved") is not True:
        errors.append("existing observation contract must be preserved")
    if record.get("fail_closed_cli") is not True:
        errors.append("fail-closed CLI required")
    if record.get("physical_observations_acquired") != 0:
        errors.append("C-066 snapshot must not claim physical observations")
    if record.get("physical_oracle_status") != "PENDING_MANUAL_ORACLE":
        errors.append("physical oracle must remain pending")

    for key in (
        "launch_modeler",
        "generate_mutations",
        "save_allowed",
        "serialization_trigger_allowed",
        "semantic_promotion",
        "blender_emit",
        "runtime_dispatch",
        "mainline_mutation",
        "rio26_mutation",
        "raw_private_bytes_published",
    ):
        if record.get(key) is not False:
            errors.append(f"{key} must be false")

    semantic_state = record.get("semantic_state", {})
    for key in (
        "geometry",
        "index_topology",
        "explicit_serializer_field_read",
        "controlled_fixture_to_consumer_match",
    ):
        if semantic_state.get(key) != "UNRESOLVED":
            errors.append(f"{key} must remain UNRESOLVED")

    receipt = record.get("receipt_contract", {})
    if receipt.get("schema_version") != "csmc_f02_mutation_oracle_intake_receipt_v1":
        errors.append("receipt schema mismatch")
    for key in (
        "source_manifest_raw_sha256",
        "observation_raw_sha256",
        "public_projection_canonical_sha256",
    ):
        if receipt.get(key) is not True:
            errors.append(f"receipt must include {key}")
    if receipt.get("diagnostic_only") is not True:
        errors.append("receipt must remain diagnostic-only")
    if receipt.get("semantic_promotion") is not False or receipt.get("blender_emit") is not False:
        errors.append("receipt may not promote semantics or Blender emit")
    return errors


def assert_valid(record: dict) -> None:
    errors = validate(record)
    if errors:
        raise ValueError("; ".join(errors))
