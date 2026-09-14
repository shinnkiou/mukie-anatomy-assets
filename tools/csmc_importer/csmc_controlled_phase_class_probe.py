#!/usr/bin/env python3
"""Aggregate-only probe for CSMC 8-byte serializer phase-class candidates.

The probe may read authorized private CSMC files locally, but its result contains
only lengths, positions, match counts and ratios. It never emits qword values or
raw payload bytes.
"""
from __future__ import annotations

import argparse
import difflib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from csmc_core import extract_character_blob
from csmc_controlled_envelope import parse_character_blob

PAIR_SPECS = (
    ("DISCOVERY_MOD7_GEOMETRY", "CSMC_F02_QUAD", "CSMC_F04_CUBE_SUBDIV", "same_mod"),
    ("VALIDATE_MOD7_RIG", "CSMC_F02_QUAD", "CSMC_R01_CUBE_B1_W0", "same_mod"),
    ("VALIDATE_MOD5_UV_WEIGHT", "CSMC_F05_CUBE_UV", "CSMC_R02_CUBE_B1_W100", "same_mod"),
    ("VALIDATE_MOD1_OBJECT_MATERIAL", "CSMC_F06_CUBE_MAT2", "CSMC_F07_TWO_CUBES", "same_mod"),
    ("VALIDATE_MOD2_GEOMETRY_WEIGHT", "CSMC_F01_TRIANGLE", "CSMC_R05_CUBE_B2_MIX50", "same_mod"),
    ("VALIDATE_MOD1_RENDERPART_CROSSCHECK", "CSMC_F06_CUBE_MAT2", "CSMC_R03_CUBE_B2_W100", "same_mod"),
    ("NEG_MOD6_7_GEOMETRY", "CSMC_F03_CUBE", "CSMC_F04_CUBE_SUBDIV", "different_mod"),
    ("NEG_MOD6_5_UV", "CSMC_F03_CUBE", "CSMC_F05_CUBE_UV", "different_mod"),
    ("NEG_MOD3_2_WEIGHT", "CSMC_R04_CUBE_B2_SPLIT", "CSMC_R05_CUBE_B2_MIX50", "different_mod"),
    ("NEG_MOD1_3_RIG_CADENCE", "CSMC_R03_CUBE_B2_W100", "CSMC_R04_CUBE_B2_SPLIT", "different_mod"),
)


@dataclass(frozen=True)
class PairAggregate:
    pair_id: str
    fixture_a: str
    fixture_b: str
    expected_mod_relation: str
    logical_mod8_a: int
    logical_mod8_b: int
    same_logical_mod8: bool
    qword_count_a: int
    qword_count_b: int
    total_matching_qwords: int
    match_fraction_shorter: float
    longest_run_qwords: int
    longest_run_start_a: int
    longest_run_start_b: int
    trailing_qwords_after_longest_a: int
    trailing_qwords_after_longest_b: int
    raw_values_embedded: bool = False


def _split_qwords(payload: bytes) -> list[bytes]:
    if len(payload) % 8:
        raise ValueError("stored payload must be 8-byte aligned")
    return [payload[i:i + 8] for i in range(0, len(payload), 8)]


def compare_qword_sequences(
    pair_id: str,
    fixture_a: str,
    fixture_b: str,
    logical_a: int,
    logical_b: int,
    qwords_a: list[bytes],
    qwords_b: list[bytes],
    expected_mod_relation: str,
) -> PairAggregate:
    matcher = difflib.SequenceMatcher(a=qwords_a, b=qwords_b, autojunk=False)
    blocks = matcher.get_matching_blocks()
    real = [m for m in blocks if m.size > 0]
    if not real:
        longest = difflib.Match(0, 0, 0)
    else:
        longest = max(real, key=lambda m: m.size)
    total = sum(m.size for m in real)
    shorter = min(len(qwords_a), len(qwords_b))
    same_mod = logical_a % 8 == logical_b % 8

    if expected_mod_relation == "same_mod" and not same_mod:
        raise ValueError(f"{pair_id}: expected same logical mod8")
    if expected_mod_relation == "different_mod" and same_mod:
        raise ValueError(f"{pair_id}: expected different logical mod8")

    return PairAggregate(
        pair_id=pair_id,
        fixture_a=fixture_a,
        fixture_b=fixture_b,
        expected_mod_relation=expected_mod_relation,
        logical_mod8_a=logical_a % 8,
        logical_mod8_b=logical_b % 8,
        same_logical_mod8=same_mod,
        qword_count_a=len(qwords_a),
        qword_count_b=len(qwords_b),
        total_matching_qwords=total,
        match_fraction_shorter=(total / shorter if shorter else 0.0),
        longest_run_qwords=longest.size,
        longest_run_start_a=longest.a,
        longest_run_start_b=longest.b,
        trailing_qwords_after_longest_a=len(qwords_a) - (longest.a + longest.size),
        trailing_qwords_after_longest_b=len(qwords_b) - (longest.b + longest.size),
    )


def _read_fixture(path: Path) -> tuple[int, list[bytes]]:
    blob, table, column, outer_version = extract_character_blob(path)
    if table != "character" or column != "character" or outer_version is None:
        raise ValueError(f"{path.name}: unsupported controlled route")
    env = parse_character_blob(
        blob,
        file_sha256="0" * 64,
        outer_version=int(outer_version),
    )
    if not env.align8_plus8_holds:
        raise ValueError(f"{path.name}: frame rule rejected")
    payload = blob[env.payload_offset:env.payload_offset + env.stored_length]
    return env.logical_length, _split_qwords(payload)


def analyze_directory(root: Path) -> dict:
    cache: dict[str, tuple[int, list[bytes]]] = {}
    results: list[dict] = []
    for pair_id, a, b, relation in PAIR_SPECS:
        for fixture in (a, b):
            if fixture not in cache:
                p = root / f"{fixture}.csmc"
                if not p.exists():
                    raise FileNotFoundError(p)
                cache[fixture] = _read_fixture(p)
        la, qa = cache[a]
        lb, qb = cache[b]
        row = compare_qword_sequences(pair_id, a, b, la, lb, qa, qb, relation)
        results.append(asdict(row))

    same = [r for r in results if r["same_logical_mod8"]]
    different = [r for r in results if not r["same_logical_mod8"]]
    return {
        "schema_version": "csmc_controlled_phase_class_probe_v1",
        "pair_count": len(results),
        "same_mod_pair_count": len(same),
        "different_mod_pair_count": len(different),
        "same_mod_min_longest_run_qwords": min(r["longest_run_qwords"] for r in same),
        "same_mod_min_match_fraction_shorter": min(r["match_fraction_shorter"] for r in same),
        "different_mod_max_longest_run_qwords": max(r["longest_run_qwords"] for r in different),
        "different_mod_max_match_fraction_shorter": max(r["match_fraction_shorter"] for r in different),
        "interpretation": "STRUCTURAL_PHASE_CLASS_CANDIDATE_ONLY",
        "named_codec_or_cipher_claim": False,
        "semantic_promotion": False,
        "blender_emit_ready": False,
        "raw_values_embedded": False,
        "pairs": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("fixture_dir", type=Path)
    ap.add_argument("--json-out", type=Path)
    ns = ap.parse_args()
    out = analyze_directory(ns.fixture_dir)
    text = json.dumps(out, indent=2, sort_keys=True)
    if ns.json_out:
        ns.json_out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
