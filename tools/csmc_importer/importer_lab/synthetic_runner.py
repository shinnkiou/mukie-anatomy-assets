from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

try:
    from .lab_core import dedupe_manifests, genotype_hash, score_candidate
except ImportError:
    from lab_core import dedupe_manifests, genotype_hash, score_candidate

WORKER = Path(__file__).with_name("synthetic_worker.py")


def _result_digest(result: Mapping[str, Any]) -> str:
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evaluate_synthetic_candidate(
    manifest: Mapping[str, Any],
    behavior: str = "PASS",
    timeout_s: float = 1.0,
) -> Dict[str, Any]:
    request = {"manifest": dict(manifest), "behavior": behavior}
    try:
        completed = subprocess.run(
            [sys.executable, str(WORKER)],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "candidate_id": manifest["candidate_id"],
            "genotype_hash": genotype_hash(manifest),
            "status": "TIMEOUT",
            "diagnostic_only": True,
            "semantic_promotion": False,
            "blender_emit": False,
        }

    if completed.returncode != 0:
        return {
            "candidate_id": manifest["candidate_id"],
            "genotype_hash": genotype_hash(manifest),
            "status": "CRASH_ISOLATED",
            "worker_returncode": completed.returncode,
            "stderr_class": "SYNTHETIC_WORKER_ERROR",
            "diagnostic_only": True,
            "semantic_promotion": False,
            "blender_emit": False,
        }

    try:
        observation = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "candidate_id": manifest["candidate_id"],
            "genotype_hash": genotype_hash(manifest),
            "status": "INVALID_WORKER_OUTPUT",
            "diagnostic_only": True,
            "semantic_promotion": False,
            "blender_emit": False,
        }

    metrics = observation.get("metrics", {})
    priority = score_candidate(metrics)
    result: Dict[str, Any] = {
        "candidate_id": manifest["candidate_id"],
        "genotype_hash": genotype_hash(manifest),
        "status": "OK",
        "observation": observation,
        "priority": priority,
        "diagnostic_only": True,
        "semantic_promotion": False,
        "blender_emit": False,
    }
    result["result_sha256"] = _result_digest(result)
    return result


def run_synthetic_batch(
    manifests: Sequence[Mapping[str, Any]],
    behaviors: Mapping[str, str] | None = None,
    concurrency: int = 1,
    timeout_s: float = 1.0,
) -> Dict[str, Any]:
    if concurrency not in (1, 2):
        raise ValueError("M1 concurrency is intentionally limited to 1 or 2")
    unique, duplicate_ids = dedupe_manifests(manifests)
    behavior_map = dict(behaviors or {})

    def job(manifest: Mapping[str, Any]) -> Dict[str, Any]:
        return evaluate_synthetic_candidate(
            manifest,
            behavior=behavior_map.get(str(manifest["candidate_id"]), "PASS"),
            timeout_s=timeout_s,
        )

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(job, unique))
    results.sort(key=lambda item: item["candidate_id"])

    replay_fingerprint = _result_digest(
        {
            "candidate_ids": [item["candidate_id"] for item in results],
            "result_hashes": [item.get("result_sha256") for item in results],
            "statuses": [item["status"] for item in results],
        }
    )
    return {
        "schema_version": "csmc_importer_lab_synthetic_batch_v0_1",
        "logical_input_count": len(manifests),
        "unique_candidate_count": len(unique),
        "duplicate_candidate_ids": duplicate_ids,
        "concurrency": concurrency,
        "results": results,
        "replay_fingerprint": replay_fingerprint,
        "private_csmc_used": False,
        "factory_semantic_decision": False,
        "semantic_promotion": False,
        "blender_emit": False,
    }
