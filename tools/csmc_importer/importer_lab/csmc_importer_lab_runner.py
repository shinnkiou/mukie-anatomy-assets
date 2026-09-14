#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import math
import struct
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping

from csmc_importer_lab_manifest import HypothesisManifest

SCHEMA_VERSION = "csmc_importer_lab_runner_v0_1"
MAX_BATCH = 50
MAX_CONCURRENCY = 2
FROZEN_SCORE_WEIGHTS = {
    "train_relationship": 35.0,
    "validation_generalization": 25.0,
    "negative_control_resistance": 20.0,
    "cross_fixture_stability": 10.0,
    "parsimony": 10.0,
}


class RunnerError(ValueError):
    pass


def _decode_numeric(region: bytes, m: HypothesisManifest) -> list[float | int]:
    if m.relative_offset > len(region):
        return []
    data = region[m.relative_offset:]
    if m.element_type in {"bytes", "opaque"}:
        return list(data[::m.stride])
    fmts = {
        ("u16", "be"): ">H",
        ("u16", "le"): "<H",
        ("u32", "be"): ">I",
        ("u32", "le"): "<I",
        ("f32", "be"): ">f",
        ("f32", "le"): "<f",
        ("f64", "be"): ">d",
        ("f64", "le"): "<d",
    }
    fmt = fmts[(m.element_type, m.endianness)]
    size = struct.calcsize(fmt)
    out: list[float | int] = []
    for base in range(0, len(data) - m.stride + 1, m.stride):
        for component in range(m.components):
            pos = base + component * size
            if pos + size <= base + m.stride and pos + size <= len(data):
                value = struct.unpack_from(fmt, data, pos)[0]
                if isinstance(value, float) and not math.isfinite(value):
                    continue
                out.append(value)
    return out


def _relationship_match(
    values: list[float | int],
    label: float | int | None,
    m: HypothesisManifest,
) -> bool:
    if m.relationship == "NULL_DECOY":
        return False
    if label is None:
        return False
    if m.relationship == "COUNT_EQUALS_LABEL":
        return len(values) == int(label)
    if m.relationship == "COUNT_LINEAR_LABEL":
        return len(values) in {int(label), int(label) * 2, int(label) * 3, int(label) * 4}
    if m.relationship in {"MAX_LT_LABEL", "REFERENCE_DOMAIN"}:
        return bool(values) and min(values) >= 0 and max(values) < int(label)
    if m.relationship == "FIXED_RECORD_REPEAT":
        return len(values) > 1 and len(set(values)) < len(values)
    if m.relationship == "MONOTONIC_WITH_LABEL":
        return len(values) == int(label)
    return False


def _evaluate_one(m: HypothesisManifest, fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    if m.synthetic_fault == "CRASH":
        raise RuntimeError("synthetic crash injection")
    if m.synthetic_fault and m.synthetic_fault.startswith("SLEEP:"):
        time.sleep(float(m.synthetic_fault.split(":", 1)[1]))

    results: list[dict[str, Any]] = []
    for fixture in fixtures:
        region_hex = fixture.get("regions", {}).get(m.region_id)
        if region_hex is None:
            results.append(
                {
                    "fixture_id": fixture["fixture_id"],
                    "split": fixture["split"],
                    "parse_valid": False,
                    "match": False,
                }
            )
            continue
        try:
            values = _decode_numeric(bytes.fromhex(region_hex), m)
            label = fixture.get("labels", {}).get(fixture.get("target_label", "target"))
            match = _relationship_match(values, label, m)
            results.append(
                {
                    "fixture_id": fixture["fixture_id"],
                    "split": fixture["split"],
                    "parse_valid": True,
                    "match": match,
                    "sample_count": len(values),
                }
            )
        except Exception:
            results.append(
                {
                    "fixture_id": fixture["fixture_id"],
                    "split": fixture["split"],
                    "parse_valid": False,
                    "match": False,
                }
            )

    if not results or not all(r["parse_valid"] for r in results if r["split"] != "HOLDOUT"):
        return {
            "status": "PARSE_REJECTED",
            "score": 0.0,
            "components": {},
            "fixture_results": results,
        }

    def ratio(split: str, desired: bool = True) -> float:
        rows = [r for r in results if r["split"] == split]
        if not rows:
            return 1.0
        return sum(r["match"] is desired for r in rows) / len(rows)

    train = ratio("TRAIN", True)
    validation = ratio("VALIDATION", True)
    negative = ratio("NEGATIVE", False)
    non_holdout = [r for r in results if r["split"] != "HOLDOUT"]
    stability = sum(1 for r in non_holdout if r["parse_valid"]) / max(1, len(non_holdout))
    complexity = min(
        1.0,
        (m.stride + m.components + (1 if m.relative_offset else 0)) / 40.0,
    )
    parsimony = 1.0 - complexity
    components = {
        "train_relationship": train,
        "validation_generalization": validation,
        "negative_control_resistance": negative,
        "cross_fixture_stability": stability,
        "parsimony": parsimony,
    }
    score = sum(FROZEN_SCORE_WEIGHTS[key] * components[key] for key in FROZEN_SCORE_WEIGHTS)
    return {
        "status": "EVALUATED",
        "score": round(score, 6),
        "components": components,
        "fixture_results": results,
    }


def _worker_main(manifest_path: str, fixtures_path: str, output_path: str) -> int:
    manifest = HypothesisManifest.from_mapping(json.loads(Path(manifest_path).read_text()))
    fixtures = json.loads(Path(fixtures_path).read_text())
    result = _evaluate_one(manifest, fixtures)
    Path(output_path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


def _run_subprocess(
    manifest: HypothesisManifest,
    fixtures: list[dict[str, Any]],
    timeout_seconds: float,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="csmc_lab_") as tmp:
        root = Path(tmp)
        manifest_path = root / "manifest.json"
        fixtures_path = root / "fixtures.json"
        output_path = root / "out.json"
        row = manifest.__dict__.copy()
        row["negative_control_set"] = list(manifest.negative_control_set)
        manifest_path.write_text(json.dumps(row))
        fixtures_path.write_text(json.dumps(fixtures))
        command = [sys.executable, __file__, "--worker", str(manifest_path), str(fixtures_path), str(output_path)]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT_ISOLATED",
                "score": 0.0,
                "components": {},
                "fixture_results": [],
            }
        if completed.returncode != 0:
            return {
                "status": "CRASH_ISOLATED",
                "score": 0.0,
                "components": {},
                "fixture_results": [],
                "error": completed.stderr[-4000:],
            }
        try:
            return json.loads(output_path.read_text())
        except Exception as exc:
            return {
                "status": "CRASH_ISOLATED",
                "score": 0.0,
                "components": {},
                "fixture_results": [],
                "error": f"bad worker output: {exc}",
            }


def run_batch(
    manifest_rows: Iterable[Mapping[str, Any]],
    fixtures: list[dict[str, Any]],
    *,
    concurrency: int = 1,
    timeout_seconds: float = 2.0,
    allow_holdout_audit: bool = False,
) -> dict[str, Any]:
    manifests = [HypothesisManifest.from_mapping(row) for row in manifest_rows]
    if len(manifests) > MAX_BATCH:
        raise RunnerError("logical batch exceeds 50 candidates")
    if concurrency not in {1, 2}:
        raise RunnerError("concurrency must be 1 or 2")

    seen: dict[str, str] = {}
    unique: list[HypothesisManifest] = []
    duplicates: list[dict[str, str]] = []
    for manifest in manifests:
        key = manifest.canonical_key()
        if key in seen:
            duplicates.append(
                {
                    "hypothesis_id": manifest.hypothesis_id,
                    "duplicate_of": seen[key],
                    "canonical_key": key,
                }
            )
        else:
            seen[key] = manifest.hypothesis_id
            unique.append(manifest)

    unique = sorted(unique, key=lambda m: (m.canonical_key(), m.hypothesis_id))

    def task(manifest: HypothesisManifest):
        result = _run_subprocess(manifest, fixtures, timeout_seconds)
        if not allow_holdout_audit and result.get("fixture_results"):
            result["fixture_results"] = [
                row for row in result["fixture_results"] if row["split"] != "HOLDOUT"
            ]
        return manifest, result

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(task, manifest) for manifest in unique]
        for future in as_completed(futures):
            manifest, result = future.result()
            results.append(
                {
                    "hypothesis_id": manifest.hypothesis_id,
                    "manifest_hash": manifest.manifest_hash(),
                    "canonical_key": manifest.canonical_key(),
                    **result,
                    "semantic_promotion": False,
                    "diagnostic_only": True,
                    "blender_emit": False,
                }
            )

    results = sorted(results, key=lambda row: row["canonical_key"])
    public = {
        "schema_version": SCHEMA_VERSION,
        "mode": (
            "SYNTHETIC_M1"
            if all(m.engine_mode == "SYNTHETIC_ONLY" for m in unique)
            else "PRIVATE_EVALUATOR_BOUNDARY"
        ),
        "candidate_count_input": len(manifests),
        "candidate_count_unique": len(unique),
        "duplicates": duplicates,
        "concurrency": concurrency,
        "timeout_seconds": timeout_seconds,
        "score_weights": FROZEN_SCORE_WEIGHTS,
        "parse_success_points": 0,
        "holdout_used_for_selection": False,
        "holdout_audit_exposed": bool(allow_holdout_audit),
        "semantic_promotion": False,
        "blender_emit": False,
        "results": results,
    }
    encoded = json.dumps(public, sort_keys=True, separators=(",", ":")).encode()
    public["deterministic_replay_sha256"] = sha256(encoded).hexdigest()
    return public


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("manifest", nargs="?")
    parser.add_argument("fixtures", nargs="?")
    parser.add_argument("out", nargs="?")
    args = parser.parse_args()
    if args.worker:
        return _worker_main(args.manifest, args.fixtures, args.out)
    parser.error("CLI currently exposes worker mode only; public batch API is run_batch()")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
