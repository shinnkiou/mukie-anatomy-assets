#!/usr/bin/env python3
"""Public-safe phase-prefix evidence probe for authorized controlled CSMC fixtures.

Reads private fixtures locally but emits only lengths, positions and match counts.
It never emits qword values or raw payload bytes and never assigns mesh/rig semantics.
"""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
import struct
from dataclasses import asdict, dataclass
from pathlib import Path

PAYLOAD_OFFSET = 65

# Existing exact-invariant intervals are fixed from the already-published mainline
# phase-class aggregate. They are validated here, not rediscovered.
PRIOR_PAIR_SPECS = (
    ("F02_F04", "CSMC_F02_QUAD", "CSMC_F04_CUBE_SUBDIV", 402, 510, 1809, 1),
    ("F02_R01", "CSMC_F02_QUAD", "CSMC_R01_CUBE_B1_W0", 402, 423, 1809, 1),
    ("F05_R02", "CSMC_F05_CUBE_UV", "CSMC_R02_CUBE_B1_W100", 441, 456, 1808, 2),
    ("F01_R05", "CSMC_F01_TRIANGLE", "CSMC_R05_CUBE_B2_MIX50", 401, 471, 1808, 2),
    ("F06_F07", "CSMC_F06_CUBE_MAT2", "CSMC_F07_TWO_CUBES", 445, 457, 2118, 1),
    ("F06_R03", "CSMC_F06_CUBE_MAT2", "CSMC_R03_CUBE_B2_W100", 762, 473, 1801, 1),
)

# Holdout: mod-3 was not present in the prior same-phase selected set.
HOLDOUT = ("R04_V01", "CSMC_R04_CUBE_B2_SPLIT", "CSMC_V01_VROID_BODY_BASE")
HOLDOUT_TRAILING_BUDGETS = (1, 2)


@dataclass(frozen=True)
class PrefixOverlapRow:
    pair_id: str
    fixture_a: str
    fixture_b: str
    logical_mod8: int
    qword_count_a: int
    qword_count_b: int
    invariant_start_a: int
    invariant_start_b: int
    invariant_length_qwords: int
    trailing_qwords_each: int
    prefix_qwords_a: int
    prefix_qwords_b: int
    distinct_exact_qwords_shared_in_prefix: int
    multiset_exact_qword_overlap_in_prefix: int
    raw_values_embedded: bool = False


def _read_payload(path: Path) -> tuple[int, list[bytes]]:
    con = sqlite3.connect(path)
    try:
        rows = con.execute("SELECT version, character FROM character").fetchall()
    finally:
        con.close()
    if len(rows) != 1 or not isinstance(rows[0][1], (bytes, bytearray)):
        raise ValueError(f"{path.name}: expected one character BLOB")
    blob = bytes(rows[0][1])
    if len(blob) < PAYLOAD_OFFSET:
        raise ValueError(f"{path.name}: truncated envelope")
    logical = struct.unpack_from("<I", blob, 57)[0]
    stored = struct.unpack_from("<I", blob, 61)[0]
    expected = ((logical + 7) & ~7) + 8
    if stored != expected or len(blob) != PAYLOAD_OFFSET + stored:
        raise ValueError(f"{path.name}: controlled frame rule rejected")
    payload = blob[PAYLOAD_OFFSET:]
    if len(payload) % 8:
        raise ValueError(f"{path.name}: stored payload not qword-aligned")
    return logical, [payload[i:i + 8] for i in range(0, len(payload), 8)]


def _prefix_overlap(a: list[bytes], b: list[bytes]) -> tuple[int, int]:
    ca = collections.Counter(a)
    cb = collections.Counter(b)
    shared = ca.keys() & cb.keys()
    return len(shared), sum(min(ca[x], cb[x]) for x in shared)


def _validate_fixed_core(
    pair_id: str,
    a: str,
    b: str,
    logical_a: int,
    logical_b: int,
    qa: list[bytes],
    qb: list[bytes],
    start_a: int,
    start_b: int,
    length: int,
    trailing: int,
) -> PrefixOverlapRow:
    if logical_a % 8 != logical_b % 8:
        raise ValueError(f"{pair_id}: expected same logical mod8")
    if start_a + length + trailing != len(qa):
        raise ValueError(f"{pair_id}: A bounds do not close at payload end")
    if start_b + length + trailing != len(qb):
        raise ValueError(f"{pair_id}: B bounds do not close at payload end")
    if qa[start_a:start_a + length] != qb[start_b:start_b + length]:
        raise ValueError(f"{pair_id}: published invariant core no longer exact")
    distinct, multiset = _prefix_overlap(qa[:start_a], qb[:start_b])
    return PrefixOverlapRow(
        pair_id=pair_id,
        fixture_a=a,
        fixture_b=b,
        logical_mod8=logical_a % 8,
        qword_count_a=len(qa),
        qword_count_b=len(qb),
        invariant_start_a=start_a,
        invariant_start_b=start_b,
        invariant_length_qwords=length,
        trailing_qwords_each=trailing,
        prefix_qwords_a=start_a,
        prefix_qwords_b=start_b,
        distinct_exact_qwords_shared_in_prefix=distinct,
        multiset_exact_qword_overlap_in_prefix=multiset,
    )


def _discover_holdout_core(
    pair_id: str,
    a: str,
    b: str,
    logical_a: int,
    logical_b: int,
    qa: list[bytes],
    qb: list[bytes],
) -> PrefixOverlapRow:
    if logical_a % 8 != logical_b % 8:
        raise ValueError(f"{pair_id}: holdout must be same logical mod8")
    best = None
    for trailing in HOLDOUT_TRAILING_BUDGETS:
        ia = len(qa) - 1 - trailing
        ib = len(qb) - 1 - trailing
        length = 0
        while ia - length >= 0 and ib - length >= 0 and qa[ia - length] == qb[ib - length]:
            length += 1
        start_a = len(qa) - trailing - length
        start_b = len(qb) - trailing - length
        candidate = (length, trailing, start_a, start_b)
        if best is None or candidate[0] > best[0]:
            best = candidate
    assert best is not None
    length, trailing, start_a, start_b = best
    if length <= 0:
        raise ValueError(f"{pair_id}: no holdout suffix core found")
    distinct, multiset = _prefix_overlap(qa[:start_a], qb[:start_b])
    return PrefixOverlapRow(
        pair_id=pair_id,
        fixture_a=a,
        fixture_b=b,
        logical_mod8=logical_a % 8,
        qword_count_a=len(qa),
        qword_count_b=len(qb),
        invariant_start_a=start_a,
        invariant_start_b=start_b,
        invariant_length_qwords=length,
        trailing_qwords_each=trailing,
        prefix_qwords_a=start_a,
        prefix_qwords_b=start_b,
        distinct_exact_qwords_shared_in_prefix=distinct,
        multiset_exact_qword_overlap_in_prefix=multiset,
    )


def analyze_directory(root: Path) -> dict:
    cache: dict[str, tuple[int, list[bytes]]] = {}

    def get(fixture: str) -> tuple[int, list[bytes]]:
        if fixture not in cache:
            path = root / f"{fixture}.csmc"
            if not path.exists():
                raise FileNotFoundError(path)
            cache[fixture] = _read_payload(path)
        return cache[fixture]

    rows: list[PrefixOverlapRow] = []
    for spec in PRIOR_PAIR_SPECS:
        pair_id, a, b, sa, sb, length, trailing = spec
        la, qa = get(a)
        lb, qb = get(b)
        rows.append(_validate_fixed_core(pair_id, a, b, la, lb, qa, qb, sa, sb, length, trailing))

    pair_id, a, b = HOLDOUT
    la, qa = get(a)
    lb, qb = get(b)
    holdout = _discover_holdout_core(pair_id, a, b, la, lb, qa, qb)
    rows.append(holdout)

    return {
        "schema_version": "csmc_controlled_prefix_extinction_probe_v1",
        "prior_pair_count": len(PRIOR_PAIR_SPECS),
        "holdout_pair_count": 1,
        "pair_count": len(rows),
        "all_pairs_same_logical_mod8": True,
        "all_prefix_distinct_exact_qword_overlap_zero": all(
            r.distinct_exact_qwords_shared_in_prefix == 0 for r in rows
        ),
        "all_prefix_multiset_exact_qword_overlap_zero": all(
            r.multiset_exact_qword_overlap_in_prefix == 0 for r in rows
        ),
        "holdout_classification": "PHASE3_VROID_HOLDOUT_INVARIANT_SUFFIX_VALIDATION",
        "prefix_classification": "PHASE_NORMALIZED_PREFIX_EXACT_QWORD_REUSE_NOT_OBSERVED",
        "semantic_promotion": False,
        "blender_emit_ready": False,
        "named_codec_or_cipher_claim": False,
        "raw_values_embedded": False,
        "pairs": [asdict(r) for r in rows],
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
