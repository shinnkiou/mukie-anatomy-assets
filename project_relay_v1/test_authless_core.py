import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JOB = ROOT / "testdata" / "authless_core_job.json"
ART = ROOT / ".authless_artifacts"


def main():
    if ART.exists():
        import shutil
        shutil.rmtree(ART)

    cp = subprocess.run(
        [sys.executable, str(ROOT / "virtual_runner.py"), str(JOB), "--root", str(ART)],
        text=True,
        capture_output=True,
    )
    print(cp.stdout)
    print(cp.stderr, file=sys.stderr)
    if cp.returncode != 0:
        raise SystemExit(f"authless core runner failed with {cp.returncode}")

    root = ART / "authless-core-ci"
    result = json.loads((root / "final" / "result.json").read_text(encoding="utf-8"))
    assert result["final_status"] == "SUCCESS", result
    assert result["successful_attempt"] == 1, result
    assert result["failures"] == [], result
    assert result["repair_plans"] == [], result

    control = json.loads((root / "attempt_01" / "result" / "control_plane.json").read_text(encoding="utf-8"))
    assert control["discord_oauth"] is False, control
    assert control["windows"] is False, control
    assert control["transport_dependency"] == "none", control
    assert control["worker"] == "github-actions-virtual", control

    assert (root / "attempt_01" / "result" / "authless_core.txt").stat().st_size > 0
    assert (root / "attempt_01" / "RESULTS.zip").stat().st_size > 0
    assert (root / "final" / "SUCCESS").exists()
    print("PROJECT RELAY AUTHLESS CLOUD CORE PASS")


if __name__ == "__main__":
    main()
