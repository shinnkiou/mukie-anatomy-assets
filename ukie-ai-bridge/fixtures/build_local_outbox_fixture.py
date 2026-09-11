from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=True)
base = "UKIE_PHYSICAL_ACCEPTANCE__BRIDGE_P016_TEST__PHYSICAL_ACCEPTANCE_20260911T000000Z.zip"
zip_path = root / base
zip_path.write_bytes(b"PK\x03\x04UKIE_P016_TEST")
digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
(root / f"{base}.sha256").write_text(f"{digest}  {base}\n", encoding="ascii", newline="\n")
receipt = {
    "schema_version": "ukie_acceptance_handoff_v1",
    "status": "LOCAL_HANDOFF_COMPLETE",
    "acceptance_id": "PHYSICAL_ACCEPTANCE_20260911T000000Z",
    "release_key": "BRIDGE_P016_TEST",
    "bridge_version": "0.16.0-p0.16",
    "commit_sha": "a" * 40,
    "workflow_run_id": 1,
    "file_name": base,
    "byte_size": zip_path.stat().st_size,
    "sha256": digest,
    "sync_folder_copy_proven": False,
    "handoff_target_kind": "LOCAL_OUTBOX_ONLY",
    "local_outbox_copy_proven": True,
    "drive_cloud_presence_proven": False,
    "drive_readback_proven": False,
    "ready_for_ai": False,
    "promotion_performed": False,
}
(root / f"{base}.handoff.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(zip_path)
