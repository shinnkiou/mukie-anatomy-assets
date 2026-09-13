#!/usr/bin/env python3
"""C-047: fail-closed transport contract for the six unresolved I2 signatures.

This module consumes only public-safe q24/q27 cross-serialization equality bits.
It does not read payload bytes and it does not replace the full C-040 I2 validator.
Its only job is to decide whether the residual six-row signature gap can be closed
and handed to the existing 22-row I2 assembly/validation stage.
"""
from __future__ import annotations

from collections import Counter
import json
import re
from typing import Any

AMBIGUOUS_INDICES = (2, 3, 8, 14, 15, 21)
SIG_A = "0000111"
SIG_B = "0001110"
TRUSTED_QUOTA = {SIG_A: 3, SIG_B: 3}
SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$")
FORBIDDEN_KEYS = {
    "raw_bytes", "payload_bytes", "file_bytes", "binary_blob",
    "private_payload", "absolute_offset", "hex",
}


def _all_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def _signature_from_observation(position: Any, equal_bit: Any) -> str:
    if isinstance(equal_bit, bool) or equal_bit not in (0, 1):
        raise ValueError("equal_bit must be integer 0 or 1")
    if position == "q24":
        return SIG_A if equal_bit == 0 else SIG_B
    if position == "q27":
        return SIG_A if equal_bit == 1 else SIG_B
    raise ValueError("position must be q24 or q27")


def validate_residual_patch(manifest: dict) -> dict:
    reasons: list[str] = []

    if manifest.get("side_lane_isolated") is not True:
        reasons.append("not_side_lane_isolated")
    if not _valid_hash(manifest.get("provenance_hash")):
        reasons.append("invalid_provenance_hash")
    leaked = sorted(set(_all_keys(manifest)) & FORBIDDEN_KEYS)
    if leaked:
        reasons.append("forbidden_raw_fields:" + ",".join(leaked))
    if manifest.get("auto_semantic_promotion") is not False:
        reasons.append("auto_semantic_promotion_must_be_false")
    if manifest.get("auto_blender_emit") is not False:
        reasons.append("auto_blender_emit_must_be_false")
    if manifest.get("corpus_id") in (None, ""):
        reasons.append("missing_corpus_id")
    if manifest.get("container_route") != "character":
        reasons.append("wrong_container_route")
    if manifest.get("regime_id") != "plus965":
        reasons.append("wrong_regime_id")

    observations = manifest.get("observations")
    resolved: dict[int, str] = {}
    if not isinstance(observations, list) or len(observations) not in (5, 6):
        reasons.append("residual_patch_requires_exactly_5_or_6_observations")
    else:
        for n, observation in enumerate(observations):
            if not isinstance(observation, dict):
                reasons.append(f"observation_{n}_not_object")
                continue
            index = observation.get("record_index")
            if index not in AMBIGUOUS_INDICES:
                reasons.append(f"observation_{n}_record_not_in_residual_set")
                continue
            if index in resolved:
                reasons.append(f"observation_{n}_duplicate_record_index")
                continue
            try:
                signature = _signature_from_observation(
                    observation.get("position"), observation.get("equal_bit")
                )
            except ValueError:
                reasons.append(f"observation_{n}_invalid_equality_observation")
                continue
            resolved[index] = signature

    if reasons:
        return _result(False, reasons, resolved)

    counts = Counter(resolved.values())
    if any(counts[signature] > required for signature, required in TRUSTED_QUOTA.items()):
        return _result(False, ["observations_conflict_with_trusted_3_3_quota"], resolved)

    derived_index = None
    derived_signature = None
    if len(resolved) == 5:
        if manifest.get("use_trusted_quota_assist") is not True:
            return _result(False, ["five_observations_require_trusted_quota_assist"], resolved)
        if manifest.get("trusted_signature_quota") != TRUSTED_QUOTA:
            return _result(False, ["trusted_signature_quota_mismatch"], resolved)
        if not _valid_hash(manifest.get("quota_provenance_hash")):
            return _result(False, ["invalid_quota_provenance_hash"], resolved)

        missing = set(AMBIGUOUS_INDICES) - set(resolved)
        if len(missing) != 1:
            return _result(False, ["residual_index_set_mismatch"], resolved)
        remaining = {
            signature: TRUSTED_QUOTA[signature] - counts[signature]
            for signature in TRUSTED_QUOTA
        }
        candidates = [signature for signature, needed in remaining.items() if needed == 1]
        if sum(remaining.values()) != 1 or len(candidates) != 1:
            return _result(False, ["quota_does_not_force_unique_sixth_signature"], resolved)
        derived_index = missing.pop()
        derived_signature = candidates[0]
        resolved[derived_index] = derived_signature
    else:
        final_counts = Counter(resolved.values())
        if any(final_counts[s] != n for s, n in TRUSTED_QUOTA.items()):
            return _result(False, ["six_observations_conflict_with_trusted_3_3_quota"], resolved)

    return _result(
        True,
        [],
        resolved,
        derived_index=derived_index,
        derived_signature=derived_signature,
    )


def _result(
    accepted: bool,
    reasons: list[str],
    resolved: dict[int, str],
    *,
    derived_index: int | None = None,
    derived_signature: str | None = None,
) -> dict:
    complete = accepted and set(resolved) == set(AMBIGUOUS_INDICES)
    return {
        "schema_version": "csmc_analysis_c_i2_residual_patch_v1",
        "accepted": accepted,
        "residual_gap_closed": complete,
        "full_i2_assembly_ready": complete,
        "resolved_signatures": {str(k): v for k, v in sorted(resolved.items())},
        "quota_derived_record_index": derived_index,
        "quota_derived_signature": derived_signature,
        "reasons": reasons,
        "requires_existing_c040_baseline": True,
        "semantic_promotion_allowed": False,
        "blender_emit_allowed": False,
        "runtime_dispatch_requested": False,
    }


if __name__ == "__main__":
    print(json.dumps({
        "schema_version": "csmc_analysis_c_i2_residual_patch_v1",
        "ambiguous_record_indices": list(AMBIGUOUS_INDICES),
        "candidate_signatures": [SIG_A, SIG_B],
        "trusted_signature_quota": TRUSTED_QUOTA,
        "recommended_observations": 6,
        "quota_assisted_minimum": 5,
        "positions": ["q24", "q27"],
        "semantic_promotion_allowed": False,
        "runtime_dispatch_requested": False,
    }, indent=2, sort_keys=True))
