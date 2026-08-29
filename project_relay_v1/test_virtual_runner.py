import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JOB = ROOT / "testdata" / "missing_output_job.json"
ART = ROOT / ".ci_artifacts"


def main():
    if ART.exists():
        import shutil
        shutil.rmtree(ART)
    cmd = [sys.executable, str(ROOT / "virtual_runner.py"), str(JOB), "--root", str(ART)]
    cp = subprocess.run(cmd, text=True, capture_output=True)
    print(cp.stdout)
    print(cp.stderr, file=sys.stderr)
    if cp.returncode != 0:
        raise SystemExit(f"virtual runner failed with {cp.returncode}")

    result = ART / "virtual-selfrepair-ci" / "final" / "result.json"
    data = json.loads(result.read_text(encoding="utf-8"))
    assert data["final_status"] == "SUCCESS", data
    assert data["successful_attempt"] == 2, data
    assert len(data["attempts"]) == 2, data
    assert data["attempts"][0]["status"] == "FAILED", data
    assert data["attempts"][0]["error_class"] == "OUTPUT", data
    assert data["attempts"][1]["status"] == "SUCCESS", data
    assert len(data["repair_plans"]) == 1, data
    assert data["repair_plans"][0]["created_by"] == "RULE_ENGINE", data
    assert (ART / "virtual-selfrepair-ci" / "attempt_02" / "RESULTS.zip").exists()
    assert (ART / "virtual-selfrepair-ci" / "final" / "SUCCESS").exists()
    assert (ART / "virtual-selfrepair-ci" / "final" / "artifact_manifest.json").exists()
    print("PROJECT RELAY VIRTUAL SELF-REPAIR PASS")


if __name__ == "__main__":
    main()
