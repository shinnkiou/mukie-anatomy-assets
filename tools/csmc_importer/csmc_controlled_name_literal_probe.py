#!/usr/bin/env python3
"""Exact source-identifier literal probe for controlled CSMC fixtures.

Searches only preregistered teacher identifiers in ASCII / UTF-16LE / UTF-16BE.
Outputs hit counts only; never emits raw CSMC bytes or arbitrary extracted strings.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

KNOWN = {
    "CSMC_F01_TRIANGLE": ["CSMC_F01_TRIANGLE", "CSMC_F01_TRIANGLE_MESH"],
    "CSMC_F02_QUAD": ["CSMC_F02_QUAD", "CSMC_F02_QUAD_MESH"],
    "CSMC_F03_CUBE": ["CSMC_F03_CUBE", "CSMC_F03_CUBE_MESH"],
    "CSMC_F04_CUBE_SUBDIV": ["CSMC_F04_CUBE_SUBDIV", "CSMC_F04_CUBE_SUBDIV_MESH"],
    "CSMC_F05_CUBE_UV": ["CSMC_F05_CUBE_UV", "CSMC_F05_CUBE_UV_MESH", "UV_MAIN"],
    "CSMC_F06_CUBE_MAT2": ["CSMC_F06_CUBE_MAT2", "CSMC_F06_CUBE_MAT2_MESH", "MAT_A", "MAT_B"],
    "CSMC_F07_TWO_CUBES": [
        "CSMC_F07_TWO_CUBES", "CSMC_F07_TWO_CUBES_A", "CSMC_F07_TWO_CUBES_B",
        "CSMC_F07_TWO_CUBES_A_MESH", "CSMC_F07_TWO_CUBES_B_MESH",
    ],
    "CSMC_R01_CUBE_B1_W0": [
        "CSMC_R01_CUBE_B1_W0", "CSMC_R01_CUBE_B1_W0_MESH",
        "CSMC_R01_CUBE_B1_W0_ARM", "CSMC_R01_CUBE_B1_W0_ARM_DATA",
        "ARMATURE", "BONE_001",
    ],
    "CSMC_R02_CUBE_B1_W100": [
        "CSMC_R02_CUBE_B1_W100", "CSMC_R02_CUBE_B1_W100_MESH",
        "CSMC_R02_CUBE_B1_W100_ARM", "CSMC_R02_CUBE_B1_W100_ARM_DATA",
        "ARMATURE", "BONE_001",
    ],
    "CSMC_R03_CUBE_B2_W100": [
        "CSMC_R03_CUBE_B2_W100", "CSMC_R03_CUBE_B2_W100_MESH",
        "CSMC_R03_CUBE_B2_W100_ARM", "CSMC_R03_CUBE_B2_W100_ARM_DATA",
        "ARMATURE", "BONE_001", "BONE_002",
    ],
    "CSMC_R04_CUBE_B2_SPLIT": [
        "CSMC_R04_CUBE_B2_SPLIT", "CSMC_R04_CUBE_B2_SPLIT_MESH",
        "CSMC_R04_CUBE_B2_SPLIT_ARM", "CSMC_R04_CUBE_B2_SPLIT_ARM_DATA",
        "ARMATURE", "BONE_001", "BONE_002",
    ],
    "CSMC_R05_CUBE_B2_MIX50": [
        "CSMC_R05_CUBE_B2_MIX50", "CSMC_R05_CUBE_B2_MIX50_MESH",
        "CSMC_R05_CUBE_B2_MIX50_ARM", "CSMC_R05_CUBE_B2_MIX50_ARM_DATA",
        "ARMATURE", "BONE_001", "BONE_002",
    ],
}

ENCODINGS = ("ascii", "utf-16le", "utf-16be")


def _character_blob(path: Path) -> bytes:
    con = sqlite3.connect(path)
    try:
        row = con.execute('select character from character').fetchone()
    finally:
        con.close()
    if row is None or row[0] is None:
        raise ValueError(f"{path.name}: character blob missing")
    return bytes(row[0])


def count_literal_hits(data: bytes, identifiers: list[str]) -> dict:
    by_encoding = {enc: 0 for enc in ENCODINGS}
    identifier_hit_count = 0
    for text in identifiers:
        hit = False
        for enc in ENCODINGS:
            n = data.count(text.encode(enc))
            by_encoding[enc] += n
            hit = hit or n > 0
        identifier_hit_count += int(hit)
    return {
        "identifier_count": len(identifiers),
        "identifiers_with_any_hit": identifier_hit_count,
        "literal_occurrences_by_encoding": by_encoding,
        "literal_occurrences_total": sum(by_encoding.values()),
    }


def analyze_directory(root: Path) -> dict:
    rows = []
    total_identifiers = 0
    raw_hits = 0
    blob_hits = 0
    for fixture, identifiers in KNOWN.items():
        path = root / f"{fixture}.csmc"
        if not path.exists():
            raise FileNotFoundError(path)
        raw = path.read_bytes()
        blob = _character_blob(path)
        raw_result = count_literal_hits(raw, identifiers)
        blob_result = count_literal_hits(blob, identifiers)
        total_identifiers += len(identifiers)
        raw_hits += raw_result["literal_occurrences_total"]
        blob_hits += blob_result["literal_occurrences_total"]
        rows.append({
            "fixture_id": fixture,
            "teacher_identifier_count": len(identifiers),
            "sqlite_file_literal_occurrences": raw_result["literal_occurrences_total"],
            "character_blob_literal_occurrences": blob_result["literal_occurrences_total"],
        })
    return {
        "schema_version": "csmc_controlled_name_literal_probe_v1",
        "fixture_count": len(KNOWN),
        "teacher_identifier_count": total_identifiers,
        "encodings": list(ENCODINGS),
        "search_surfaces": ["sqlite_file_bytes", "character_blob_bytes"],
        "sqlite_file_literal_occurrences_total": raw_hits,
        "character_blob_literal_occurrences_total": blob_hits,
        "interpretation": "SOURCE_IDENTIFIER_PLAINTEXT_ASCII_UTF16_NOT_OBSERVED" if raw_hits == 0 and blob_hits == 0 else "LITERAL_IDENTIFIER_HIT_REQUIRES_REVIEW",
        "semantic_promotion": False,
        "name_metadata_region_confirmed": False,
        "raw_values_embedded": False,
        "fixtures": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("fixture_dir", type=Path)
    ap.add_argument("--json-out", type=Path)
    ns = ap.parse_args()
    result = analyze_directory(ns.fixture_dir)
    text = json.dumps(result, indent=2, sort_keys=True)
    if ns.json_out:
        ns.json_out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
