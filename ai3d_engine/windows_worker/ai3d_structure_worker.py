# SPDX-License-Identifier: MIT
"""Isolated NEVER TEAR AI3D-013 Structure capability companion.

This companion reuses the proven AI3D worker transport primitives but advertises
only ai3d_structure_module_v1 and talks only to the separate Structure CANARY
endpoint. It cannot claim the MVP queue or the full Central Corridor plan.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any

import ai3d_worker as core

WORKER_VERSION = "0.2.0-ai3d-structure-canary"
PROTOCOL = "never-tear-ai3d-worker-v1"
EDGE_URL = "https://vbuokbwglauibabinaqs.supabase.co/functions/v1/ai3d-worker-transport-structure-canary"
ACTION = "ai3d_structure_module_v1"
TASK_ID = "AI3D-013"
RUN_ID = "AI3D-013-PHYSICAL-STRUCTURE-CANARY-001"
MODULE_ID = "ai3d_structure_capability_canary_v1"
PLAN_SCHEMA = "never-tear-ai3d-structure-capability-canary-plan-v1"
RESULT_SCHEMA = "never-tear-ai3d-structure-capability-canary-result-v1"
ALLOWED_ACTIONS = frozenset({ACTION})
SAFE_QA = frozenset({"wall_count_exact", "opening_boolean_exact", "cutter_removed", "mesh_nonempty", "floor_contact", "render_evidence"})


def _number(value: object, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise core.WorkerError("numeric value required")
    n = float(value)
    if not math.isfinite(n) or n < low or n > high:
        raise core.WorkerError("numeric value out of range")
    return n


def _vec3(value: object, low: float, high: float) -> list[float]:
    if not isinstance(value, list) or len(value) != 3:
        raise core.WorkerError("vec3 required")
    return [_number(v, low, high) for v in value]


def sanitize_plan(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise core.WorkerError("cloud plan must be object")
    allowed = {"schema", "project_key", "task_id", "run_id", "module_id", "coordinate_contract", "commands", "policy"}
    if set(value) != allowed:
        raise core.WorkerError("plan top-level contract mismatch")
    if value.get("schema") != PLAN_SCHEMA or value.get("project_key") != "never_tear_ai3d_engine":
        raise core.WorkerError("plan identity rejected")
    if value.get("task_id") != TASK_ID or value.get("run_id") != RUN_ID or value.get("module_id") != MODULE_ID:
        raise core.WorkerError("task/run/module rejected")
    if value.get("coordinate_contract") != "PLAN_XY_EAST_NORTH_TO_THREE_XZ_YUP_V1":
        raise core.WorkerError("coordinate contract rejected")
    expected_policy = {"synthetic_canary": True, "geometry_authority_mutated": False, "production_plan_mutated": False, "allow_arbitrary_script": False, "allow_network": False, "max_commands": 6, "max_attempts": 1, "physical_concurrency": 1, "semantic_promotion": False}
    if value.get("policy") != expected_policy:
        raise core.WorkerError("policy rejected")
    commands = value.get("commands")
    if not isinstance(commands, list) or len(commands) != 6:
        raise core.WorkerError("command count rejected")
    counts = {op: 0 for op in ("CREATE_PRIMITIVE", "TRANSFORM_SET", "BOOLEAN", "QA_RUN")}
    names: set[str] = set()
    for command in commands:
        if not isinstance(command, dict) or set(command) != {"command_id", "op", "params", "lineage", "routes"}:
            raise core.WorkerError("command contract rejected")
        op = str(command.get("op") or "")
        if op not in counts:
            raise core.WorkerError("op rejected")
        counts[op] += 1
        if command.get("routes") != ["WINDOWS_WORKER"]:
            raise core.WorkerError("route rejected")
        lineage = command.get("lineage")
        if not isinstance(lineage, dict) or lineage != {"module_id": MODULE_ID, "source": "AI3D-013_SYNTHETIC_CANARY"}:
            raise core.WorkerError("lineage rejected")
        params = command.get("params")
        if not isinstance(params, dict):
            raise core.WorkerError("params missing")
        if op == "CREATE_PRIMITIVE":
            if set(params) != {"name", "kind", "position", "size"} or params.get("kind") != "box":
                raise core.WorkerError("primitive params rejected")
            name = str(params.get("name") or "")
            if name not in {"wall_001", "opening_cutter_001"} or name in names:
                raise core.WorkerError("primitive name rejected")
            names.add(name); _vec3(params.get("position"), -10, 10); _vec3(params.get("size"), 0.01, 10)
        elif op == "TRANSFORM_SET":
            if set(params) != {"name", "rotation"} or str(params.get("name") or "") not in {"wall_001", "opening_cutter_001"}:
                raise core.WorkerError("transform params rejected")
            rotation = _vec3(params.get("rotation"), -2 * math.pi, 2 * math.pi)
            if abs(rotation[0]) > 1e-9 or abs(rotation[2]) > 1e-9:
                raise core.WorkerError("rotation contract rejected")
        elif op == "BOOLEAN":
            if params != {"target": "wall_001", "tool": "opening_cutter_001", "mode": "subtract", "keep_tool": False}:
                raise core.WorkerError("boolean params rejected")
        elif op == "QA_RUN":
            if set(params) != {"checks"} or not isinstance(params.get("checks"), list) or set(map(str, params["checks"])) != SAFE_QA:
                raise core.WorkerError("QA params rejected")
    if counts != {"CREATE_PRIMITIVE": 2, "TRANSFORM_SET": 2, "BOOLEAN": 1, "QA_RUN": 1}:
        raise core.WorkerError("operation counts rejected")
    return json.loads(json.dumps(value))


def validate_result(job_dir: Path) -> tuple[dict[str, Any], Path]:
    result_path = job_dir / "result.json"; png_path = job_dir / "ai3d_structure_capability_canary.png"
    if not result_path.is_file() or not png_path.is_file():
        raise core.WorkerError("Structure CANARY evidence files missing")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict) or result.get("schema_version") != RESULT_SCHEMA:
        raise core.WorkerError("Structure result schema rejected")
    if result.get("task_id") != TASK_ID or result.get("run_id") != RUN_ID or result.get("action") != ACTION or result.get("status") != "PASS":
        raise core.WorkerError("Structure automated QA did not pass")
    if result.get("wall_count") != 1 or result.get("opening_boolean_count") != 1 or result.get("command_count") != 6:
        raise core.WorkerError("Structure result counts rejected")
    if result.get("visual_qa") != "PENDING" or result.get("canary_promoted") is not False or result.get("promotion_allowed") is not False:
        raise core.WorkerError("Structure CANARY promotion boundary violated")
    for key in ("png_sha256", "raw_pixel_sha256", "checkpoint_sha256", "blend_sha256"):
        if not core.is_hex64(str(result.get(key, ""))):
            raise core.WorkerError(f"invalid {key}")
    if core.sha256_file(png_path) != result["png_sha256"]:
        raise core.WorkerError("local PNG SHA mismatch")
    if png_path.stat().st_size > core.MAX_PNG_BYTES:
        raise core.WorkerError("local PNG exceeds upload contract")
    return result, png_path


def _bounded_log_tail(path: Path, limit: int = 3500) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    text = text.replace("\x00", "").strip()
    return text[-limit:]


def run_blender_job(credential: dict[str, str], job: dict[str, Any], job_dir: Path) -> tuple[dict[str, Any], Path]:
    existing_result = job_dir / "result.json"; existing_png = job_dir / "ai3d_structure_capability_canary.png"
    if existing_result.is_file() and existing_png.is_file():
        try: return validate_result(job_dir)
        except Exception: pass
    job_dir.mkdir(parents=True, exist_ok=True)
    plan_path = job_dir / "plan.json"
    plan_path.write_text(json.dumps(sanitize_plan(job["plan"]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    blender = core.discover_blender(); script = core.bundled_file("blender_structure_module_canary.py")
    command = [str(blender), "--factory-startup", "--background", "--python-exit-code", "31", "--python", str(script), "--", "--plan", str(plan_path), "--output", str(job_dir)]
    stdout_path = job_dir / "blender.stdout.log"; stderr_path = job_dir / "blender.stderr.log"
    started = time.monotonic(); next_heartbeat = started + core.HEARTBEAT_SECONDS
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        proc = subprocess.Popen(command, stdout=stdout, stderr=stderr, shell=False, cwd=str(job_dir))
        while proc.poll() is None:
            now = time.monotonic()
            if now - started > core.RENDER_TIMEOUT_SECONDS:
                proc.kill(); proc.wait(timeout=10); raise core.WorkerError("Structure Blender timeout")
            if now >= next_heartbeat:
                core.heartbeat(credential, job); next_heartbeat = now + core.HEARTBEAT_SECONDS
            time.sleep(1.0)
    if proc.returncode != 0:
        stderr_tail = _bounded_log_tail(stderr_path)
        stdout_tail = _bounded_log_tail(stdout_path, 1200)
        diagnostic = stderr_tail or stdout_tail or "no Blender diagnostic output"
        raise core.WorkerError(f"Structure Blender exited with code {proc.returncode}; diagnostic_tail={diagnostic}")
    core.heartbeat(credential, job)
    return validate_result(job_dir)


def complete_pass(credential: dict[str, str], job: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return core.request_json(credential, {"action": "complete", "job_id": job["id"], "lease_owner": job["lease_owner"], "outcome": "PASS", "result": {"raw_pixel_sha256": result["raw_pixel_sha256"], "png_sha256": result["png_sha256"], "checkpoint_id": result["checkpoint_id"], "checkpoint_sha256": result["checkpoint_sha256"], "renderer": result["renderer"], "blender_version": result["blender_version"], "render_engine": result["render_engine"], "boolean_solver": result["boolean_solver"], "width": result["width"], "height": result["height"], "wall_count": result["wall_count"], "opening_boolean_count": result["opening_boolean_count"], "command_count": result["command_count"], "automated_qa": "PASS", "visual_qa": "PENDING"}})


def process_job(credential: dict[str, str], job: dict[str, Any]) -> None:
    command_id = str(job.get("command_id") or "")
    if job.get("action") != ACTION or job.get("task_id") != TASK_ID or job.get("job_key") != "AI3D-013-PHYSICAL-STRUCTURE-CANARY-001":
        raise core.WorkerError("Structure CANARY job identity rejected")
    if len(command_id) < 8: raise core.WorkerError("command_id invalid")
    job_dir = core.command_dir(command_id); result, png_path = run_blender_job(credential, job, job_dir)
    upload = core.upload_png(credential, job, png_path, result["png_sha256"]); response = complete_pass(credential, job, result)
    if response.get("status") != "STRUCTURE_CANARY_AUTOMATED_PASS_VISUAL_PENDING": raise core.WorkerError(f"unexpected completion status: {response.get('status')}")
    receipt = {"schema_version":"never-tear-ai3d-structure-worker-receipt-v1","command_id":command_id,"job_key":job.get("job_key"),"status":response.get("status"),"artifact_id":upload.get("artifact_id"),"png_sha256":result["png_sha256"],"checkpoint_id":result["checkpoint_id"],"local_job_dir":str(job_dir)}
    core.receipt_path(command_id).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); print(json.dumps(receipt, ensure_ascii=False), flush=True)


def _valid_plan() -> dict[str, Any]:
    def cmd(cid: str, op: str, params: dict[str, Any]) -> dict[str, Any]: return {"command_id":cid,"op":op,"params":params,"lineage":{"module_id":MODULE_ID,"source":"AI3D-013_SYNTHETIC_CANARY"},"routes":["WINDOWS_WORKER"]}
    return {"schema":PLAN_SCHEMA,"project_key":"never_tear_ai3d_engine","task_id":TASK_ID,"run_id":RUN_ID,"module_id":MODULE_ID,"coordinate_contract":"PLAN_XY_EAST_NORTH_TO_THREE_XZ_YUP_V1","commands":[cmd("ai3d-013-canary-create-wall","CREATE_PRIMITIVE",{"name":"wall_001","kind":"box","position":[0.0,1.7,0.0],"size":[4.0,3.4,0.2]}),cmd("ai3d-013-canary-transform-wall","TRANSFORM_SET",{"name":"wall_001","rotation":[0.0,0.0,0.0]}),cmd("ai3d-013-canary-create-opening","CREATE_PRIMITIVE",{"name":"opening_cutter_001","kind":"box","position":[0.0,1.1,0.0],"size":[1.0,2.2,0.6]}),cmd("ai3d-013-canary-transform-opening","TRANSFORM_SET",{"name":"opening_cutter_001","rotation":[0.0,0.0,0.0]}),cmd("ai3d-013-canary-boolean","BOOLEAN",{"target":"wall_001","tool":"opening_cutter_001","mode":"subtract","keep_tool":False}),cmd("ai3d-013-canary-qa","QA_RUN",{"checks":sorted(SAFE_QA)})],"policy":{"synthetic_canary":True,"geometry_authority_mutated":False,"production_plan_mutated":False,"allow_arbitrary_script":False,"allow_network":False,"max_commands":6,"max_attempts":1,"physical_concurrency":1,"semantic_promotion":False}}


def self_test() -> int:
    failures=[]
    try: sanitize_plan(_valid_plan())
    except Exception as exc: failures.append(f"valid plan rejected: {exc}")
    for field in ("command","script","path","url","executable"):
        bad=_valid_plan(); bad[field]="forbidden"
        try: sanitize_plan(bad); failures.append(f"dangerous field accepted: {field}")
        except core.WorkerError: pass
    if ALLOWED_ACTIONS != frozenset({ACTION}): failures.append("allowlist widened")
    if not EDGE_URL.endswith("/ai3d-worker-transport-structure-canary"): failures.append("endpoint mismatch")
    result={"schema_version":"never-tear-ai3d-structure-worker-selftest-v1","worker_version":WORKER_VERSION,"protocol":PROTOCOL,"allowed_actions":sorted(ALLOWED_ACTIONS),"arbitrary_shell":False,"production_plan_claim":False,"status":"PASS" if not failures else "FAIL","failures":failures}; print(json.dumps(result,indent=2,sort_keys=True)); return 0 if not failures else 23


core.WORKER_VERSION=WORKER_VERSION; core.PROTOCOL=PROTOCOL; core.EDGE_URL=EDGE_URL; core.ALLOWED_ACTIONS=ALLOWED_ACTIONS; core.sanitize_plan=sanitize_plan; core.validate_result=validate_result; core.run_blender_job=run_blender_job; core.complete_pass=complete_pass; core.process_job=process_job; core.self_test=self_test
if __name__ == "__main__": raise SystemExit(core.main())