#!/usr/bin/env python3
"""Fail-closed validator for Companion C C-065 targeted simple-96 rejection.

Validates only the public-safe aggregate emitted by the targeted mainline resume.
No private CSMC bytes are consumed here.
"""

EXPECTED_FIXTURES = ["CSMC_F06_CUBE_MAT2", "CSMC_F07_TWO_CUBES"]
EXPECTED_SCOPES = {
    "FULL_PRE_COMMON": {"hits": 0},
    "TRAILING_2048_PLUS_INSERTION": {"hits": 0, "shorter_bytes": 2048, "longer_bytes": 2144},
}


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    if record.get("pipeline_stage") != "STRUCTURAL_ONLY":
        errors.append("pipeline must remain STRUCTURAL_ONLY")
    if record.get("semantic_promotion_count") != 0:
        errors.append("semantic promotion forbidden")
    if record.get("blender_emit_ready") is not False:
        errors.append("Blender emit must remain blocked")
    if record.get("runtime_dispatch") is not False:
        errors.append("runtime dispatch must remain false")
    if record.get("raw_private_bytes_published") is not False:
        errors.append("raw/private publication forbidden")

    test = record.get("targeted_test", {})
    if test.get("classification") != "TARGETED_SIMPLE_96B_INSERTION_FAMILY_REJECTED":
        errors.append("targeted classification mismatch")
    if test.get("family") != "SIMPLE_96B_SINGLE_INSERTION_BEFORE_COMMON_BLOCK":
        errors.append("family mismatch")
    if test.get("fixtures") != EXPECTED_FIXTURES:
        errors.append("fixture pair mismatch")
    if test.get("delete_from") != "F07_PRE_COMMON":
        errors.append("delete source mismatch")
    if test.get("delete_length_bytes") != 96:
        errors.append("delete length must remain exactly 96")
    if test.get("exact_equality_required") is not True or test.get("tolerance") != 0:
        errors.append("test must remain exact with zero tolerance")
    if test.get("multi_delete_allowed") is not False:
        errors.append("multiple deletions were not preregistered")

    scopes = {x.get("scope"): x for x in test.get("scopes", []) if isinstance(x, dict)}
    if set(scopes) != set(EXPECTED_SCOPES):
        errors.append("scope set mismatch")
    else:
        for name, expected in EXPECTED_SCOPES.items():
            for key, value in expected.items():
                if scopes[name].get(key) != value:
                    errors.append(f"{name}.{key} mismatch")

    source = record.get("preserved_source", {})
    if source.get("triple_common_exact_bytes") != 7392:
        errors.append("source triple-common extent mismatch")
    shifts = source.get("pre_common_shift_bytes", {})
    if shifts != {"F06_minus_F03": 88, "F07_minus_F03": 184, "F07_minus_F06": 96}:
        errors.append("source shift evidence mismatch")
    if source.get("render_part_residual_candidate") != "LEVEL_4_REFINED_NOT_PROMOTED":
        errors.append("Level-4 candidate must remain unpromoted")

    if record.get("frontier_decision") != "RETURN_TO_PAUSED_WAITING_NEW_INDEPENDENT_EVIDENCE":
        errors.append("frontier must return to paused state")

    unresolved = record.get("semantic_state", {})
    for key in ("geometry", "index_topology", "serializer_field_read", "controlled_fixture_to_consumer_match"):
        if unresolved.get(key) != "UNRESOLVED":
            errors.append(f"{key} must remain UNRESOLVED")
    return errors


def assert_valid(record: dict) -> None:
    errors = validate(record)
    if errors:
        raise ValueError("; ".join(errors))
