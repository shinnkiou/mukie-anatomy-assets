#!/usr/bin/env python3
"""Public-safe structural cadence detector for authorized CSMC payloads.

The detector does not embed or publish any private qword values. It tests only
whether qwords at a fixed lag are exactly equal, groups consecutive equality
runs, and returns positions/counts. The result is structural metadata only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from csmc_core import extract_character_blob
from csmc_controlled_envelope import parse_character_blob

SCHEMA_VERSION = "csmc_public_safe_cadence_detector_v0_1"
DEFAULT_LAG_QWORDS = 307
DEFAULT_MIN_EQUAL_RUN_QWORDS = 10
DEFAULT_MAX_CLUSTER_START_GAP_QWORDS = 250


@dataclass(frozen=True)
class EqualRun:
    start_qword: int
    end_qword: int
    length_qwords: int


@dataclass(frozen=True)
class CadenceDetection:
    schema_version: str
    detected: bool
    lag_qwords: int
    period_bytes: int
    min_equal_run_qwords: int
    max_cluster_start_gap_qwords: int
    cluster_run_count: int
    cadence_count_candidate: int | None
    cluster_start_qword: int | None
    cluster_end_qword: int | None
    run_lengths_qwords: tuple[int, ...]
    raw_values_embedded: bool = False
    semantic_promotion: bool = False

    def to_public_dict(self) -> dict:
        return asdict(self)


def split_qwords(payload: bytes) -> list[bytes]:
    if len(payload) % 8:
        raise ValueError("stored payload is not qword aligned")
    return [payload[i:i + 8] for i in range(0, len(payload), 8)]


def find_equal_runs(qwords: list[bytes], *, lag_qwords: int, min_run_qwords: int) -> list[EqualRun]:
    if lag_qwords <= 0:
        raise ValueError("lag_qwords must be positive")
    if min_run_qwords <= 0:
        raise ValueError("min_run_qwords must be positive")
    limit = len(qwords) - lag_qwords
    if limit <= 0:
        return []

    out: list[EqualRun] = []
    start: int | None = None
    for i in range(limit):
        equal = qwords[i] == qwords[i + lag_qwords]
        if equal and start is None:
            start = i
        elif not equal and start is not None:
            if i - start >= min_run_qwords:
                out.append(EqualRun(start, i, i - start))
            start = None
    if start is not None and limit - start >= min_run_qwords:
        out.append(EqualRun(start, limit, limit - start))
    return out


def cluster_runs(runs: list[EqualRun], *, max_start_gap_qwords: int) -> list[list[EqualRun]]:
    if max_start_gap_qwords <= 0:
        raise ValueError("max_start_gap_qwords must be positive")
    clusters: list[list[EqualRun]] = []
    current: list[EqualRun] = []
    for run in runs:
        if not current or run.start_qword - current[-1].start_qword <= max_start_gap_qwords:
            current.append(run)
        else:
            clusters.append(current)
            current = [run]
    if current:
        clusters.append(current)
    return clusters


def detect_cadence_qwords(
    qwords: list[bytes],
    *,
    lag_qwords: int = DEFAULT_LAG_QWORDS,
    min_equal_run_qwords: int = DEFAULT_MIN_EQUAL_RUN_QWORDS,
    max_cluster_start_gap_qwords: int = DEFAULT_MAX_CLUSTER_START_GAP_QWORDS,
) -> CadenceDetection:
    runs = find_equal_runs(qwords, lag_qwords=lag_qwords, min_run_qwords=min_equal_run_qwords)
    clusters = cluster_runs(runs, max_start_gap_qwords=max_cluster_start_gap_qwords)
    eligible = [c for c in clusters if len(c) >= 4 and len(c) % 2 == 0]
    if not eligible:
        return CadenceDetection(
            schema_version=SCHEMA_VERSION,
            detected=False,
            lag_qwords=lag_qwords,
            period_bytes=lag_qwords * 8,
            min_equal_run_qwords=min_equal_run_qwords,
            max_cluster_start_gap_qwords=max_cluster_start_gap_qwords,
            cluster_run_count=0,
            cadence_count_candidate=None,
            cluster_start_qword=None,
            cluster_end_qword=None,
            run_lengths_qwords=(),
        )

    # Prefer the largest dense cluster. If tied, use the rightmost cluster so
    # isolated earlier repeats cannot shadow a later candidate region.
    best = max(eligible, key=lambda c: (len(c), c[-1].start_qword))
    return CadenceDetection(
        schema_version=SCHEMA_VERSION,
        detected=True,
        lag_qwords=lag_qwords,
        period_bytes=lag_qwords * 8,
        min_equal_run_qwords=min_equal_run_qwords,
        max_cluster_start_gap_qwords=max_cluster_start_gap_qwords,
        cluster_run_count=len(best),
        cadence_count_candidate=len(best) // 2 + 1,
        cluster_start_qword=best[0].start_qword,
        cluster_end_qword=best[-1].end_qword,
        run_lengths_qwords=tuple(r.length_qwords for r in best),
    )


def inspect_csmc_cadence(path: str | Path, **kwargs) -> CadenceDetection:
    blob, table, column, outer_version = extract_character_blob(Path(path))
    if table != "character" or column != "character" or outer_version is None:
        raise ValueError("unsupported CSMC character route")
    env = parse_character_blob(blob, file_sha256="0" * 64, outer_version=int(outer_version))
    if not env.align8_plus8_holds:
        raise ValueError("validated outer frame rule does not hold")
    payload = blob[env.payload_offset:env.payload_offset + env.stored_length]
    return detect_cadence_qwords(split_qwords(payload), **kwargs)
