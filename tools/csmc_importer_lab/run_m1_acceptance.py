#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lab import (
    ArtifactIntegrityError,
    FrozenContextDrift,
    FrozenEnvelope,
    GenerationRunner,
    LAB_CAPABILITY,
    LAB_QUEUE,
    PRODUCTION_QUEUE_DENYLIST,
    generate_synthetic_candidates,
    genotype_hash,
    public_result_contains_private_material,
    validate_manifest,
    verify_artifact,
    write_artifact,
)

def record(rows, ident, passed, evidence):
    rows.append({"id": ident, "status": "PASS" if passed else "FAIL", "evidence": evidence})
    return passed

def run_acceptance(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    checks = []
    base = generate_synthetic_candidates(50)
    env = FrozenEnvelope()

    r2 = GenerationRunner(env, physical_concurrency=2)
    results50 = r2.run(base)
    record(checks, "M1-01", len(results50) == 50,
           {"logical_manifests":50, "results":len(results50), "statuses":{s:sum(x.status==s for x in results50) for s in sorted({x.status for x in results50})}})

    canary = GenerationRunner(env, physical_concurrency=1).run([base[0]])
    record(checks, "M1-02", len(canary)==1 and canary[0].status=="EXECUTION_PASS",
           {"physical_concurrency":1, "status":canary[0].status})

    mvp = GenerationRunner(env, physical_concurrency=2).run(base[:10])
    record(checks, "M1-03", len(mvp)==10 and any(x.status=="EXECUTION_PASS" for x in mvp),
           {"physical_concurrency":2, "results":len(mvp)})

    dup = copy.deepcopy(base[0])
    dup["candidate_id"] = "HYP_9000"
    dedupe_results = GenerationRunner(env, physical_concurrency=1).run([base[0], dup])
    dup_rejects = [x for x in dedupe_results if "duplicate" in " ".join(x.reject_reasons).lower()]
    record(checks, "M1-04", len(dedupe_results)==2 and len(dup_rejects)==1,
           {"genotype":genotype_hash(base[0]), "duplicate_rejects":len(dup_rejects)})

    bad = copy.deepcopy(base[0])
    bad["candidate_id"] = "HYP_9001"
    bad["shell"] = "echo forbidden"
    errors = validate_manifest(bad)
    record(checks, "M1-05", any("forbidden" in e for e in errors),
           {"validator_errors":errors})

    hang_batch = [copy.deepcopy(base[i]) for i in range(3)]
    hang_batch[0]["candidate_id"]="HYP_9010"
    hang_batch[1]["candidate_id"]="HYP_9011"
    hang_batch[2]["candidate_id"]="HYP_9012"
    hang_results = GenerationRunner(env, physical_concurrency=2).run(hang_batch, test_behaviors={"HYP_9010":"HANG"})
    statuses = {x.candidate_id:x.status for x in hang_results}
    record(checks, "M1-06", statuses.get("HYP_9010")=="TIMEOUT" and all(statuses.get(cid)=="EXECUTION_PASS" for cid in ("HYP_9011","HYP_9012")), statuses)

    crash_batch = [copy.deepcopy(base[i]) for i in range(3,6)]
    for n,row in enumerate(crash_batch, start=9020):
        row["candidate_id"]=f"HYP_{n}"
    crash_results = GenerationRunner(env, physical_concurrency=2).run(crash_batch, test_behaviors={"HYP_9020":"CRASH"})
    cstatuses = {x.candidate_id:x.status for x in crash_results}
    record(checks, "M1-07", cstatuses.get("HYP_9020")=="CRASH" and all(cstatuses.get(cid)=="EXECUTION_PASS" for cid in ("HYP_9021","HYP_9022")), cstatuses)

    neg = next(x for x in base if x["candidate_family"]=="FALSIFICATION_CONTROLS")
    neg_result = GenerationRunner(env, physical_concurrency=1).run([neg])[0]
    record(checks, "M1-08", neg_result.status=="NEGATIVE_CONTROL_REJECT",
           {"candidate_id":neg_result.candidate_id,"status":neg_result.status})

    artifact = out_dir/"integrity_probe.json"
    sha = write_artifact(artifact, {"public_safe":True,"semantic_promotion":False})
    artifact.write_text(artifact.read_text(encoding="utf-8") + "CORRUPTED", encoding="utf-8")
    corruption_caught = False
    try:
        verify_artifact(artifact, sha)
    except ArtifactIntegrityError:
        corruption_caught = True
    record(checks, "M1-09", corruption_caught, {"expected_sha256":sha,"corruption_rejected":corruption_caught})
    artifact.unlink(missing_ok=True)

    runner = GenerationRunner(env, physical_concurrency=1)
    drifted = FrozenEnvelope(evaluator_sha256="9"*64)
    drift_caught = False
    try:
        runner.assert_frozen(drifted)
    except FrozenContextDrift:
        drift_caught = True
    record(checks, "M1-10", drift_caught, {"frozen_context_digest":runner.frozen_digest,"drift_rejected":drift_caught})

    replay_candidate = base[7]
    fingerprints = []
    for _ in range(3):
        rr = GenerationRunner(env, physical_concurrency=1).run([replay_candidate])[0]
        fingerprints.append(rr.public_safe_result_fingerprint)
    record(checks, "M1-11", len(set(fingerprints))==1 and None not in fingerprints,
           {"replays":3,"fingerprints":fingerprints})

    public_dicts = [x.public_dict() for x in results50]
    no_private = all(not public_result_contains_private_material(x) for x in public_dicts)
    record(checks, "M1-12", no_private, {"public_results_checked":len(public_dicts),"private_material_detected":not no_private})

    record(checks, "M1-13", all(x.semantic_promotion is False for x in results50),
           {"semantic_promotion_true_count":sum(bool(x.semantic_promotion) for x in results50)})

    record(checks, "M1-14", all(x.blender_emit is False for x in results50),
           {"blender_emit_true_count":sum(bool(x.blender_emit) for x in results50)})

    record(checks, "M1-15", r2.production_queue_jobs==0 and LAB_QUEUE not in PRODUCTION_QUEUE_DENYLIST,
           {"lab_queue":LAB_QUEUE,"production_queue_jobs":r2.production_queue_jobs})

    record(checks, "M1-16", r2.production_artifact_mutations==0,
           {"production_artifact_mutations":r2.production_artifact_mutations})

    passed = sum(x["status"]=="PASS" for x in checks)
    report = {
        "schema_version":"csmc_importer_lab_m1_acceptance_v0_1",
        "project_key":"csmc_importer_lab",
        "worker_capability":LAB_CAPABILITY,
        "execution_plane":"SYNTHETIC_PUBLIC_SAFE_ONLY",
        "checks":checks,
        "passed":passed,
        "failed":len(checks)-passed,
        "m1_status":"PASS" if passed==16 else "FAIL",
        "m2_eligible":passed==16,
        "m2_started":False,
        "m2_start_blocker":"PRIVATE_CONTROLLED_CSMC_NOT_PRESENT_IN_THIS_SYNTHETIC_EXECUTION_CONTEXT" if passed==16 else "M1_NOT_FULL_PASS",
        "semantic_promotion":False,
        "blender_emit":False,
        "production_queue_jobs":0,
        "production_artifact_mutations":0,
    }
    report["report_sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",",":")).encode()).hexdigest()
    write_artifact(out_dir/"M1_ACCEPTANCE_REPORT.json", report)
    return report

def main():
    out = HERE/"artifacts/M1_SYNTHETIC_20260914"
    report = run_acceptance(out)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["m1_status"]=="PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
