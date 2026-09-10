"""Build a synthetic cloud-discovery triplet for P0.11 CI only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from fixtures.build_synthetic_acceptance_bundle import build_bundle
except ModuleNotFoundError:
    # Direct execution (`python fixtures/build_synthetic_cloud_triplet.py`) puts
    # the fixtures directory, not the repository root, first on sys.path.
    from build_synthetic_acceptance_bundle import build_bundle


RELEASE_KEY = "BRIDGE_P09_RUN_99999999999"
BRIDGE_VERSION = "0.11.0-p0.9"
COMMIT_SHA = "a" * 40
WORKFLOW_RUN_ID = 99999999999
ACCEPTANCE_ID = "PHYSICAL_ACCEPTANCE_CI_SYNTHETIC"


def build_triplet(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"UKIE_PHYSICAL_ACCEPTANCE__{RELEASE_KEY}__{ACCEPTANCE_ID}.zip"
    bundle = output_dir / base_name
    sha = build_bundle(bundle)
    size = bundle.stat().st_size

    sha_sidecar = output_dir / f"{base_name}.sha256"
    sha_sidecar.write_text(f"{sha}  {base_name}\n", encoding="ascii")

    handoff = {
        "schema_version": "ukie_acceptance_handoff_v1",
        "status": "LOCAL_HANDOFF_COMPLETE",
        "created_at": "2026-09-10T00:00:02+00:00",
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_status": "CORE_PASS_GPU_PASS",
        "release_key": RELEASE_KEY,
        "bridge_version": BRIDGE_VERSION,
        "commit_sha": COMMIT_SHA,
        "workflow_run_id": WORKFLOW_RUN_ID,
        "file_name": base_name,
        "byte_size": size,
        "sha256": sha,
        "copy_status": "COPIED_AND_VERIFIED",
        "local_acceptance_verification": "ACCEPTANCE_EVIDENCE_VALID",
        "local_core_ready": True,
        "local_gpu_render_ready": True,
        "sync_folder_copy_proven": True,
        "drive_cloud_presence_proven": False,
        "drive_readback_proven": False,
        "ready_for_ai": False,
        "promotion_performed": False,
        "next_gate": "CLOUD_DISCOVERY_RAW_READBACK_AND_ACCEPTANCE_VERIFICATION",
        "synthetic_ci_only": True,
    }
    handoff_path = output_dir / f"{base_name}.handoff.json"
    handoff_path.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "bundle": str(bundle),
        "sha_sidecar": str(sha_sidecar),
        "handoff": str(handoff_path),
        "base_name": base_name,
        "sha256": sha,
        "byte_size": size,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = build_triplet(Path(args.output_dir))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
