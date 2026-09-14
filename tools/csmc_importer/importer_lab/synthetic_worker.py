from __future__ import annotations

import hashlib
import json
import sys
import time


def stable_int(value: object, modulus: int) -> int:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:12], 16) % modulus


def main() -> int:
    request = json.load(sys.stdin)
    manifest = request["manifest"]
    behavior = request.get("behavior", "PASS")

    if behavior == "RAISE":
        raise RuntimeError("synthetic crash requested")
    if behavior == "SLEEP":
        time.sleep(5.0)
    if behavior not in {"PASS", "INVALID", "RAISE", "SLEEP"}:
        raise ValueError("unknown synthetic behavior")

    base = stable_int(manifest, 17)
    if behavior == "INVALID":
        metrics = {"parse_valid": False, "hard_constraints_pass": True}
    else:
        metrics = {
            "parse_valid": True,
            "hard_constraints_pass": True,
            "controlled_differential": (base % 5) / 4,
            "withheld_validation": ((base + 1) % 5) / 4,
            "negative_controls": ((base + 2) % 5) / 4,
            "structural_consistency": ((base + 3) % 5) / 4,
            "consumer_evidence": 0.0,
            "simplicity": 1.0 if manifest.get("stride_bytes", 0) in {0, 2, 4, 8} else 0.5,
            "visual_similarity": 1.0,
            "generic_numeric_plausibility": 1.0,
        }

    observation = {
        "schema_version": "csmc_importer_lab_synthetic_observation_v0_1",
        "candidate_id": manifest["candidate_id"],
        "parsed_ranges": [[base, base + 8]],
        "element_counts": {"synthetic": base + 1},
        "relationship_outcomes": {manifest["relationship"]: behavior == "PASS"},
        "metrics": metrics,
        "diagnostic_only": True,
        "not_semantic_proof": True,
        "not_import_result": True,
        "private_csmc_used": False,
    }
    json.dump(observation, sys.stdout, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
