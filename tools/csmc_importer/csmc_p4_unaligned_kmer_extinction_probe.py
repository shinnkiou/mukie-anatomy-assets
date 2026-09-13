#!/usr/bin/env python3
"""Public-safe unaligned k-mer extinction probe for CSMC P4 structure work.

The probe compares a bounded byte range from one serialization against the
entire opposite payload at *every byte phase*. It emits aggregate counts only:
no matched k-mer value, payload byte, mesh byte, texture byte, or proprietary
content is printed or written.

This is a structural correspondence test. It does not infer encryption,
compression, DRM, geometry semantics, or any protection mechanism.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable


def _read_range(path: Path, start: int, end: int) -> bytes:
    if start < 0 or end <= start:
        raise ValueError("invalid byte range")
    size = path.stat().st_size
    if end > size:
        raise ValueError(f"range {start}:{end} exceeds file size {size}")
    with path.open("rb") as handle:
        handle.seek(start)
        data = handle.read(end - start)
    if len(data) != end - start:
        raise IOError("short bounded read")
    return data


def _kmers_as_ints(data: bytes, k: int) -> set[int]:
    if k < 1 or k > 8:
        raise ValueError("k must be in [1, 8]")
    if len(data) < k:
        return set()
    value = int.from_bytes(data[:k], "little")
    shift = 8 * (k - 1)
    mask = (1 << (8 * k)) - 1
    out = {value}
    for pos in range(k, len(data)):
        value = ((value >> 8) | (data[pos] << shift)) & mask
        out.add(value)
    return out


def _scan_python(path: Path, targets: set[int], k: int, chunk_bytes: int) -> tuple[int, int]:
    """Small-input fallback. Counts matching windows and distinct matched values."""
    if not targets:
        return 0, 0
    matched_occurrences = 0
    matched_values: set[int] = set()
    carry = b""
    shift = 8 * (k - 1)
    mask = (1 << (8 * k)) - 1
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_bytes)
            if not chunk:
                break
            data = carry + chunk
            if len(data) >= k:
                value = int.from_bytes(data[:k], "little")
                if value in targets:
                    matched_occurrences += 1
                    matched_values.add(value)
                for pos in range(k, len(data)):
                    value = ((value >> 8) | (data[pos] << shift)) & mask
                    if value in targets:
                        matched_occurrences += 1
                        matched_values.add(value)
            carry = data[-(k - 1):] if k > 1 else b""
    return matched_occurrences, len(matched_values)


def _scan_numpy(path: Path, targets: set[int], k: int, chunk_bytes: int) -> tuple[int, int]:
    import numpy as np  # optional fast path

    if not targets:
        return 0, 0
    sorted_targets = np.array(sorted(targets), dtype=np.uint64)
    matched_occurrences = 0
    matched_values: set[int] = set()
    carry = b""
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_bytes)
            if not chunk:
                break
            data = carry + chunk
            if len(data) >= k:
                raw = np.frombuffer(data, dtype=np.uint8)
                window_count = len(raw) - k + 1
                values = np.zeros(window_count, dtype=np.uint64)
                for offset in range(k):
                    values |= raw[offset:offset + window_count].astype(np.uint64) << np.uint64(8 * offset)
                idx = np.searchsorted(sorted_targets, values)
                in_bounds = idx < len(sorted_targets)
                mask = np.zeros(window_count, dtype=bool)
                if in_bounds.any():
                    mask[in_bounds] = sorted_targets[idx[in_bounds]] == values[in_bounds]
                count = int(mask.sum())
                if count:
                    matched_occurrences += count
                    matched_values.update(map(int, np.unique(values[mask])))
            carry = data[-(k - 1):] if k > 1 else b""
    return matched_occurrences, len(matched_values)


def _scan(path: Path, targets: set[int], k: int, chunk_bytes: int, engine: str) -> tuple[int, int, str]:
    if engine not in {"auto", "numpy", "python"}:
        raise ValueError("engine must be auto, numpy, or python")
    if engine in {"auto", "numpy"}:
        try:
            result = _scan_numpy(path, targets, k, chunk_bytes)
            return result[0], result[1], "numpy"
        except ImportError:
            if engine == "numpy":
                raise
    result = _scan_python(path, targets, k, chunk_bytes)
    return result[0], result[1], "python"


def _poisson_tail_at_least(observed: int, lam: float) -> float:
    if observed <= 0:
        return 1.0
    if lam <= 0:
        return 0.0
    term = math.exp(-lam)
    cumulative = term
    for value in range(1, observed):
        term *= lam / value
        cumulative += term
    return max(0.0, min(1.0, 1.0 - cumulative))


def _direction(source_range: bytes, haystack: Path, k: int, chunk_bytes: int, engine: str) -> dict[str, object]:
    targets = _kmers_as_ints(source_range, k)
    haystack_windows = max(0, haystack.stat().st_size - k + 1)
    matched_occurrences, matched_distinct, used_engine = _scan(haystack, targets, k, chunk_bytes, engine)
    expected = len(targets) * haystack_windows / float(256 ** k)
    return {
        "k_bytes": k,
        "source_windows": max(0, len(source_range) - k + 1),
        "source_distinct_kmers": len(targets),
        "haystack_windows": haystack_windows,
        "matched_occurrences": matched_occurrences,
        "matched_distinct_kmers": matched_distinct,
        "uniform_random_expected_occurrences": expected,
        "poisson_p_at_least_observed": _poisson_tail_at_least(matched_occurrences, expected),
        "engine": used_engine,
    }


def analyze(
    clip_path: Path,
    csmc_path: Path,
    clip_start: int,
    clip_end: int,
    csmc_start: int,
    csmc_end: int,
    k_values: Iterable[int],
    chunk_bytes: int,
    engine: str,
) -> dict[str, object]:
    clip_range = _read_range(clip_path, clip_start, clip_end)
    csmc_range = _read_range(csmc_path, csmc_start, csmc_end)
    rows = []
    for k in k_values:
        clip_targets = _kmers_as_ints(clip_range, k)
        csmc_targets = _kmers_as_ints(csmc_range, k)
        rows.append({
            "k_bytes": k,
            "local_cross_range_shared_distinct_kmers": len(clip_targets & csmc_targets),
            "clip_range_to_full_csmc": _direction(clip_range, csmc_path, k, chunk_bytes, engine),
            "csmc_range_to_full_clip": _direction(csmc_range, clip_path, k, chunk_bytes, engine),
        })
    return {
        "schema_version": "csmc_p4_unaligned_kmer_extinction_v1",
        "scope": "aggregate_only_public_safe",
        "clip_file_size": clip_path.stat().st_size,
        "csmc_file_size": csmc_path.stat().st_size,
        "clip_range": {"start": clip_start, "end": clip_end, "size": len(clip_range)},
        "csmc_range": {"start": csmc_start, "end": csmc_end, "size": len(csmc_range)},
        "results": rows,
        "guardrails": {
            "raw_kmers_emitted": False,
            "raw_payload_bytes_emitted": False,
            "geometry_semantics_claimed": False,
            "codec_or_protection_mechanism_claimed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clip", required=True, type=Path)
    parser.add_argument("--csmc", required=True, type=Path)
    parser.add_argument("--clip-start", required=True, type=int)
    parser.add_argument("--clip-end", required=True, type=int)
    parser.add_argument("--csmc-start", required=True, type=int)
    parser.add_argument("--csmc-end", required=True, type=int)
    parser.add_argument("--k", nargs="+", type=int, default=[5, 6, 7, 8])
    parser.add_argument("--chunk-bytes", type=int, default=2 * 1024 * 1024)
    parser.add_argument("--engine", choices=["auto", "numpy", "python"], default="auto")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.chunk_bytes < 1024:
        raise SystemExit("--chunk-bytes must be >= 1024")
    result = analyze(args.clip, args.csmc, args.clip_start, args.clip_end, args.csmc_start, args.csmc_end, args.k, args.chunk_bytes, args.engine)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
