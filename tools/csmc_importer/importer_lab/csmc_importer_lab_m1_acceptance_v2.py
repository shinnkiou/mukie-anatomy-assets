#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import tempfile
from typing import Any, Callable

import csmc_importer_lab_runner as runner_module
from csmc_importer_lab_manifest import HypothesisManifest, ManifestError
from csmc_importer_lab_policy import FROZEN_SCORE_SPEC, HARD_CONSTRAINTS, REJECTED_FAMILIES
from csmc_importer_lab_runner import RunnerError, run_batch

SCHEMA_VERSION = "csmc_importer_lab_m1_acceptance_v2"
EXPECTED_CHECK_IDS = (
    "logical_batch_le_50",
    "manifest_validation",
    "canonical_dedupe",
    "genotype_hash",
    "phenotype_hash",
    "hard_constraint_registry",
    "rejected_family_registry",
    "holdout_ledger",
    "frozen_scoring_spec",
    "semantic_promotion_firewall",
    "private_evaluator_boundary",
    "timeout_isolation",
    "crash_isolation",
    "forbidden_shell_rejection",
    "forbidden_script_rejection",
    "forbidden_path_url_rejection",
    "artifact_sha_readback",
    "generation_checkpoint",
    "deterministic_replay",
    "production_queue_isolation",
)


class ArtifactIntegrityError(RuntimeError):
    pass


def _manifest_row(**updates: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "hypothesis_id": "M1V2_BASE",
        "generation": 0,
        "engine_mode": "SYNTHETIC_ONLY",
        "candidate_family": "LOCAL_COUNTED_NUMERIC_BLOCK",
        "region_class": "SYNTHETIC_REGION",
        "region_id": "R0",
        "anchor_id": "R0_START",
        "relative_offset": 0,
        "count_source": "TARGET_LABEL",
        "count_type": "u16",
        "endianness": "be",
        "element_type": "u16",
        "stride": 2,
        "components": 1,
        "grouping": "SCALAR",
        "relationship": "COUNT_EQUALS_LABEL",
        "candidate_semantic": "STRUCTURAL_ONLY",
        "preprocess": "NONE",
        "parent_hypothesis_id": None,
        "preregistered_prediction": "synthetic acceptance only",
        "negative_control_set": ["N1"],
        "semantic_promotion": False,
        "diagnostic_only": True,
        "blender_emit": False,
        "synthetic_fault": None,
    }
    row.update(updates)
    return row


def _fixtures() -> list[dict[str, Any]]:
    common = "000100020003"
    return [
        {"fixture_id": "T1", "split": "TRAIN", "regions": {"R0": common}, "labels": {"target": 3}, "target_label": "target"},
        {"fixture_id": "V1", "split": "VALIDATION", "regions": {"R0": common}, "labels": {"target": 3}, "target_label": "target"},
        {"fixture_id": "N1", "split": "NEGATIVE", "regions": {"R0": common}, "labels": {"target": 2}, "target_label": "target"},
        {"fixture_id": "H1", "split": "HOLDOUT", "regions": {"R0": common}, "labels": {"target": 3}, "target_label": "target"},
        {"fixture_id": "E1", "split": "EXTERNAL_BENCHMARK", "regions": {"R0": common}, "labels": {"target": 3}, "target_label": "target"},
    ]


def _canonical_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def verify_public_artifact(path: Path, expected_sha256: str) -> None:
    actual = sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ArtifactIntegrityError(f"readback SHA mismatch: expected={expected_sha256} actual={actual}")


def write_public_generation_checkpoint(root: Path, file_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not file_name.endswith(".json") or Path(file_name).name != file_name or "://" in file_name or "/" in file_name or "\\" in file_name:
        raise ValueError("checkpoint file_name must be a local basename ending in .json")
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / file_name).resolve()
    target.relative_to(root)
    raw = _canonical_bytes(payload)
    expected = sha256(raw).hexdigest()
    target.write_bytes(raw)
    verify_public_artifact(target, expected)
    readback = json.loads(target.read_text(encoding="utf-8"))
    if readback != payload:
        raise ArtifactIntegrityError("generation checkpoint semantic readback mismatch")
    return {
        "file_name": file_name,
        "sha256": expected,
        "size_bytes": len(raw),
        "readback_verified": True,
    }


def _rejects_extra_field(field: str, value: Any) -> tuple[bool, str]:
    row = _manifest_row()
    row[field] = value
    try:
        HypothesisManifest.from_mapping(row)
    except ManifestError as exc:
        return True, str(exc)
    return False, "accepted unexpectedly"


def _one_result(public: dict[str, Any], hypothesis_id: str) -> dict[str, Any]:
    return next(row for row in public["results"] if row["hypothesis_id"] == hypothesis_id)


def _run_check(check_id: str, fn: Callable[[], tuple[bool, dict[str, Any]]]) -> dict[str, Any]:
    try:
        passed, evidence = fn()
        return {"id": check_id, "status": "PASS" if passed else "FAIL", "evidence": evidence}
    except Exception as exc:
        return {
            "id": check_id,
            "status": "FAIL",
            "evidence": {"exception": type(exc).__name__, "detail": str(exc)},
        }


def run_acceptance() -> dict[str, Any]:
    fixtures = _fixtures()

    def logical_batch() -> tuple[bool, dict[str, Any]]:
        fifty = [_manifest_row(hypothesis_id=f"M1V2_B{i:02d}") for i in range(50)]
        accepted = run_batch(fifty, fixtures, concurrency=1)
        rejected_51 = False
        try:
            run_batch(fifty + [_manifest_row(hypothesis_id="M1V2_B50")], fixtures, concurrency=1)
        except RunnerError:
            rejected_51 = True
        return accepted["candidate_count_input"] == 50 and rejected_51, {
            "accepted_logical_batch": accepted["candidate_count_input"],
            "candidate_count_unique_after_dedupe": accepted["candidate_count_unique"],
            "batch_51_rejected": rejected_51,
        }

    def manifest_validation() -> tuple[bool, dict[str, Any]]:
        valid = HypothesisManifest.from_mapping(_manifest_row())
        bad, detail = _rejects_extra_field("unknown_candidate_override", True)
        return valid.hypothesis_id == "M1V2_BASE" and bad, {"valid_manifest": True, "unknown_field_rejected": bad, "detail": detail}

    def canonical_dedupe() -> tuple[bool, dict[str, Any]]:
        public = run_batch([_manifest_row(hypothesis_id="D1"), _manifest_row(hypothesis_id="D2")], fixtures)
        return public["candidate_count_unique"] == 1 and len(public["duplicates"]) == 1, {
            "input": public["candidate_count_input"], "unique": public["candidate_count_unique"], "duplicates": len(public["duplicates"])
        }

    def genotype_hash() -> tuple[bool, dict[str, Any]]:
        a = HypothesisManifest.from_mapping(_manifest_row(hypothesis_id="G_A"))
        b = HypothesisManifest.from_mapping(_manifest_row(hypothesis_id="G_B"))
        different = a.manifest_hash() != b.manifest_hash()
        return different, {"role": "full typed manifest hash", "a": a.manifest_hash(), "b": b.manifest_hash(), "different": different}

    def phenotype_hash() -> tuple[bool, dict[str, Any]]:
        a = HypothesisManifest.from_mapping(_manifest_row(hypothesis_id="P_A", preregistered_prediction="a"))
        b = HypothesisManifest.from_mapping(_manifest_row(hypothesis_id="P_B", preregistered_prediction="b"))
        same = a.canonical_key() == b.canonical_key()
        return same, {"role": "canonical behavior/parameter hash", "a": a.canonical_key(), "b": b.canonical_key(), "same": same}

    def hard_registry() -> tuple[bool, dict[str, Any]]:
        expected = {
            "max_logical_batch": 50,
            "semantic_promotion": False,
            "diagnostic_only": True,
            "blender_emit": False,
            "holdout_used_for_selection": False,
        }
        passed = all(HARD_CONSTRAINTS.get(k) == v for k, v in expected.items()) and HARD_CONSTRAINTS.get("allowed_concurrency") == [1, 2]
        return passed, {"expected": expected, "actual": HARD_CONSTRAINTS}

    def rejected_registry() -> tuple[bool, dict[str, Any]]:
        family = "WHOLE_PAYLOAD_SIMPLE_FIXED_STRIDE"
        registered = family in REJECTED_FAMILIES
        row = _manifest_row(candidate_family=family)
        rejected = False
        detail = ""
        try:
            HypothesisManifest.from_mapping(row)
        except ManifestError as exc:
            rejected = True
            detail = str(exc)
        return registered and rejected, {"family": family, "registered": registered, "rejected": rejected, "detail": detail}

    def holdout_ledger() -> tuple[bool, dict[str, Any]]:
        public = run_batch([_manifest_row(hypothesis_id="HOLDOUT")], fixtures, allow_holdout_audit=False)
        splits = {r["split"] for r in public["results"][0]["fixture_results"]}
        ledger = public["holdout_ledger"]["entries"]
        sealed_absent = "HOLDOUT" not in splits and "EXTERNAL_BENCHMARK" not in splits
        untouched = all(ledger[k]["exposure_count"] == 0 and not ledger[k]["used_for_selection"] for k in ("H1", "E1"))
        return sealed_absent and untouched and not public["holdout_used_for_selection"], {
            "evaluated_splits": sorted(splits), "sealed_exposure_counts": {k: ledger[k]["exposure_count"] for k in ("H1", "E1")}, "used_for_selection": public["holdout_used_for_selection"]
        }

    def frozen_scoring() -> tuple[bool, dict[str, Any]]:
        public = run_batch([_manifest_row(hypothesis_id="SCORE")], fixtures)
        expected = {k: float(v) for k, v in FROZEN_SCORE_SPEC.items() if k not in {"parse_success_points", "visual_similarity_points"}}
        passed = public["score_weights"] == expected and public["parse_success_points"] == 0.0 and public["visual_similarity_points"] == 0.0
        return passed, {"score_weights": public["score_weights"], "parse_success_points": public["parse_success_points"], "visual_similarity_points": public["visual_similarity_points"]}

    def semantic_firewall() -> tuple[bool, dict[str, Any]]:
        rejected = False
        try:
            HypothesisManifest.from_mapping(_manifest_row(semantic_promotion=True))
        except ManifestError:
            rejected = True
        public = run_batch([_manifest_row(hypothesis_id="FIREWALL")], fixtures)
        all_false = public["semantic_promotion"] is False and all(r["semantic_promotion"] is False and r["blender_emit"] is False for r in public["results"])
        return rejected and all_false, {"promotion_request_rejected": rejected, "public_semantic_promotion": public["semantic_promotion"], "result_true_count": sum(bool(r["semantic_promotion"]) for r in public["results"])}

    def private_boundary() -> tuple[bool, dict[str, Any]]:
        raw_hex = fixtures[0]["regions"]["R0"]
        public = run_batch([_manifest_row(hypothesis_id="PRIVATE", engine_mode="PRIVATE_EVALUATOR")], fixtures)
        encoded = json.dumps(public, sort_keys=True)
        path_rejected, _ = _rejects_extra_field("private_fixture_path", "/private/input.csmc")
        url_rejected, _ = _rejects_extra_field("private_input_url", "https://example.invalid/input.csmc")
        passed = public["mode"] == "PRIVATE_EVALUATOR_BOUNDARY" and raw_hex not in encoded and path_rejected and url_rejected
        return passed, {"mode": public["mode"], "raw_fixture_material_in_public_result": raw_hex in encoded, "private_path_rejected": path_rejected, "private_url_rejected": url_rejected}

    def timeout_isolation() -> tuple[bool, dict[str, Any]]:
        rows = [
            _manifest_row(hypothesis_id="TIMEOUT_BAD", synthetic_fault="SLEEP:0.20", relative_offset=0),
            _manifest_row(hypothesis_id="TIMEOUT_GOOD", relative_offset=2),
        ]
        public = run_batch(rows, fixtures, concurrency=2, timeout_seconds=0.05)
        bad = _one_result(public, "TIMEOUT_BAD")["status"]
        good = _one_result(public, "TIMEOUT_GOOD")["status"]
        return bad == "TIMEOUT_ISOLATED" and good == "EVALUATED", {"TIMEOUT_BAD": bad, "TIMEOUT_GOOD": good}

    def crash_isolation() -> tuple[bool, dict[str, Any]]:
        rows = [
            _manifest_row(hypothesis_id="CRASH_BAD", synthetic_fault="CRASH", relative_offset=0),
            _manifest_row(hypothesis_id="CRASH_GOOD", relative_offset=2),
        ]
        public = run_batch(rows, fixtures, concurrency=2)
        bad = _one_result(public, "CRASH_BAD")["status"]
        good = _one_result(public, "CRASH_GOOD")["status"]
        return bad == "CRASH_ISOLATED" and good == "EVALUATED", {"CRASH_BAD": bad, "CRASH_GOOD": good}

    def forbidden_shell() -> tuple[bool, dict[str, Any]]:
        passed, detail = _rejects_extra_field("shell", "echo forbidden")
        return passed, {"rejected": passed, "detail": detail}

    def forbidden_script() -> tuple[bool, dict[str, Any]]:
        passed, detail = _rejects_extra_field("script", "print('forbidden')")
        return passed, {"rejected": passed, "detail": detail}

    def forbidden_path_url() -> tuple[bool, dict[str, Any]]:
        path_rejected, path_detail = _rejects_extra_field("filesystem_path", "/tmp/private.csmc")
        url_rejected, url_detail = _rejects_extra_field("network_url", "https://example.invalid/private.csmc")
        return path_rejected and url_rejected, {"path_rejected": path_rejected, "url_rejected": url_rejected, "path_detail": path_detail, "url_detail": url_detail}

    def artifact_integrity() -> tuple[bool, dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix="csmc_m1v2_artifact_") as td:
            root = Path(td)
            info = write_public_generation_checkpoint(root, "M1_INTEGRITY_PROBE.json", {"public_safe": True, "semantic_promotion": False})
            target = root / info["file_name"]
            target.write_bytes(target.read_bytes() + b"CORRUPT")
            caught = False
            try:
                verify_public_artifact(target, info["sha256"])
            except ArtifactIntegrityError:
                caught = True
            return caught, {"initial_readback_verified": info["readback_verified"], "corruption_rejected": caught, "sha256": info["sha256"]}

    def generation_checkpoint() -> tuple[bool, dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix="csmc_m1v2_checkpoint_") as td:
            payload = {"schema_version": "csmc_importer_lab_generation_checkpoint_v0_1", "generation": 0, "status": "SYNTHETIC_ACCEPTANCE", "semantic_promotion": False, "blender_emit": False}
            info = write_public_generation_checkpoint(Path(td), "M1_GENERATION_0000.json", payload)
            readback = json.loads((Path(td) / info["file_name"]).read_text(encoding="utf-8"))
            passed = info["readback_verified"] and readback == payload and info["size_bytes"] > 0
            return passed, {**info, "generation": readback["generation"], "status": readback["status"]}

    def deterministic_replay() -> tuple[bool, dict[str, Any]]:
        rows = [_manifest_row(hypothesis_id="REPLAY_A", relative_offset=0), _manifest_row(hypothesis_id="REPLAY_B", relative_offset=2)]
        first = run_batch(rows, fixtures, concurrency=2)
        second = run_batch(list(reversed(rows)), fixtures, concurrency=1)
        same = first["deterministic_result_sha256"] == second["deterministic_result_sha256"]
        return same, {"first": first["deterministic_result_sha256"], "second": second["deterministic_result_sha256"], "same": same}

    def production_isolation() -> tuple[bool, dict[str, Any]]:
        source = inspect.getsource(runner_module)
        forbidden_runtime_tokens = (
            "ai3d_worker_jobs", "ukie_bridge_jobs", "csmc_canary_heartbeat_evidence",
            "supabase", "requests.", "httpx", "urllib.request", "socket.",
        )
        found = [token for token in forbidden_runtime_tokens if token in source]
        local_self_worker = "sys.executable, __file__, \"--worker\"" in source
        public = run_batch([_manifest_row(hypothesis_id="PROD_ISO")], fixtures)
        no_queue_fields = not any(key in public for key in ("queue", "job_key", "dispatch", "production_queue"))
        passed = not found and local_self_worker and no_queue_fields and public["semantic_promotion"] is False and public["blender_emit"] is False
        return passed, {"forbidden_runtime_tokens_found": found, "local_self_worker_only": local_self_worker, "production_queue_fields_present": not no_queue_fields}

    checks = [
        _run_check("logical_batch_le_50", logical_batch),
        _run_check("manifest_validation", manifest_validation),
        _run_check("canonical_dedupe", canonical_dedupe),
        _run_check("genotype_hash", genotype_hash),
        _run_check("phenotype_hash", phenotype_hash),
        _run_check("hard_constraint_registry", hard_registry),
        _run_check("rejected_family_registry", rejected_registry),
        _run_check("holdout_ledger", holdout_ledger),
        _run_check("frozen_scoring_spec", frozen_scoring),
        _run_check("semantic_promotion_firewall", semantic_firewall),
        _run_check("private_evaluator_boundary", private_boundary),
        _run_check("timeout_isolation", timeout_isolation),
        _run_check("crash_isolation", crash_isolation),
        _run_check("forbidden_shell_rejection", forbidden_shell),
        _run_check("forbidden_script_rejection", forbidden_script),
        _run_check("forbidden_path_url_rejection", forbidden_path_url),
        _run_check("artifact_sha_readback", artifact_integrity),
        _run_check("generation_checkpoint", generation_checkpoint),
        _run_check("deterministic_replay", deterministic_replay),
        _run_check("production_queue_isolation", production_isolation),
    ]
    passed = sum(row["status"] == "PASS" for row in checks)
    report = {
        "schema_version": SCHEMA_VERSION,
        "execution_plane": "SYNTHETIC_PUBLIC_SAFE_ONLY",
        "check_count": len(checks),
        "passed": passed,
        "failed": len(checks) - passed,
        "m1_acceptance_v2_status": "PASS" if passed == len(EXPECTED_CHECK_IDS) else "FAIL",
        "private_gen0_eligible": passed == len(EXPECTED_CHECK_IDS),
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_dispatch": False,
        "checks": checks,
    }
    report["report_sha256"] = sha256(json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return report


def main() -> int:
    report = run_acceptance()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if report["m1_acceptance_v2_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
