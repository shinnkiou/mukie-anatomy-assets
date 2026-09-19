from __future__ import annotations

import csv
import frida
import hashlib
import json
import math
import os
import struct
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

MODELER = r"C:\Program Files\CELSYS\CLIP STUDIO 1.5\CLIP STUDIO MODELER\CLIPStudioModeler.exe"
KNOWN_SHA256 = "2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150"

BODY_SIZE = 1_160_128
STRIDE = 32
VERTICES = BODY_SIZE // STRIDE

MAX_ABS_POSITION = 1_000_000.0
MAX_ABS_NORMAL = 100.0
MAX_ABS_UV = 1000.0
MAX_REASONABLE_DISPLACEMENT = 10_000.0
MIN_CHANGED_VERTICES = 100
MAX_CHANGED_VERTICES = 30_000
POSITION_EPS = 1e-5

root = Path(os.environ.get("USERPROFILE", ".")) / "CSMC_ANALYSIS"
stamp = time.strftime("%Y%m%d_%H%M%S")
out = root / ("VBO_CALLER_GATE_" + stamp)
out.mkdir(parents=True, exist_ok=True)

events_path = out / "EVENTS.jsonl"
validated_uploads_path = out / "VALIDATED_UPLOADS.tsv"
stack_frames_path = out / "STACK_FRAMES.tsv"
signatures_path = out / "STACK_SIGNATURES.tsv"
frame_freq_path = out / "MODELER_FRAME_FREQUENCY.tsv"
target_path = out / "TARGET_RVAS.txt"
summary_path = out / "SUMMARY.txt"
script_path = Path(__file__).with_name("02_VBO_CALLER_GATE_V1_6_3.js")

candidate_batches: dict[str, list[dict]] = {}
candidate_done: set[str] = set()
frida_errors: list[dict] = []
status_events: list[dict] = []

def log_event(obj):
    with events_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")

def on_message(message, data):
    if message.get("type") == "error":
        rec = {"kind": "frida_error", "message": message}
        frida_errors.append(rec)
        log_event(rec)
        return

    p = message.get("payload")
    if not isinstance(p, dict):
        return

    kind = p.get("kind", "status")

    if kind == "candidate":
        tag = str(p.get("tag", ""))
        raw = bytes(data or b"")
        rec = dict(p)
        rec["bytes"] = raw
        rec["length"] = len(raw)
        rec["sha256"] = hashlib.sha256(raw).hexdigest() if raw else ""
        candidate_batches.setdefault(tag, []).append(rec)
        evt = {k: v for k, v in rec.items() if k != "bytes"}
        log_event(evt)
        return

    if kind == "candidate_batch_done":
        candidate_done.add(str(p.get("tag", "")))
    elif kind == "status":
        status_events.append(dict(p))

    log_event(p)

def request_candidates(script, tag: str, timeout: float = 20.0) -> list[dict]:
    candidate_batches[tag] = []
    candidate_done.discard(tag)
    script.post({"type": "command", "payload": {"cmd": "dump_candidates", "tag": tag}})
    end = time.time() + timeout
    while time.time() < end:
        if tag in candidate_done:
            return candidate_batches.get(tag, [])
        time.sleep(0.05)
    raise RuntimeError(f"candidate dump timeout: {tag}")

def clear_candidates(script):
    script.post({"type": "command", "payload": {"cmd": "clear_candidates"}})
    time.sleep(0.2)

def uv_sha256(buf: bytes) -> str:
    h = hashlib.sha256()
    for i in range(VERTICES):
        off = i * STRIDE + 24
        h.update(buf[off:off + 8])
    return h.hexdigest()

def validate_body(buf: bytes) -> dict:
    result = {
        "valid": False,
        "reason": "",
        "max_abs_position": 0.0,
        "max_abs_normal": 0.0,
        "max_abs_uv": 0.0,
        "uv_sha256": "",
    }

    if len(buf) != BODY_SIZE:
        result["reason"] = f"bad_size:{len(buf)}"
        return result

    maxp = maxn = maxuv = 0.0

    try:
        for i in range(VERTICES):
            off = i * STRIDE
            px, py, pz, nx, ny, nz, u, v = struct.unpack_from("<8f", buf, off)

            vals = (px, py, pz, nx, ny, nz, u, v)
            if not all(math.isfinite(x) for x in vals):
                result["reason"] = "non_finite_float"
                return result

            maxp = max(maxp, abs(px), abs(py), abs(pz))
            maxn = max(maxn, abs(nx), abs(ny), abs(nz))
            maxuv = max(maxuv, abs(u), abs(v))

            if maxp > MAX_ABS_POSITION:
                result["reason"] = "position_out_of_bounds"
                return result
            if maxn > MAX_ABS_NORMAL:
                result["reason"] = "normal_out_of_bounds"
                return result
            if maxuv > MAX_ABS_UV:
                result["reason"] = "uv_out_of_bounds"
                return result

    except Exception as e:
        result["reason"] = "parse_error:" + repr(e)
        return result

    result["valid"] = True
    result["reason"] = "OK"
    result["max_abs_position"] = maxp
    result["max_abs_normal"] = maxn
    result["max_abs_uv"] = maxuv
    result["uv_sha256"] = uv_sha256(buf)
    return result

def compare_positions(base: bytes, other: bytes):
    changed = []
    maxdisp = 0.0

    for i in range(VERTICES):
        off = i * STRIDE
        ax, ay, az = struct.unpack_from("<3f", base, off)
        bx, by, bz = struct.unpack_from("<3f", other, off)

        dx = bx - ax
        dy = by - ay
        dz = bz - az
        d = math.sqrt(dx * dx + dy * dy + dz * dz)

        if d > POSITION_EPS:
            changed.append((i, d))
            maxdisp = max(maxdisp, d)

    return changed, maxdisp

def first_modeler_rva(rec: dict) -> str:
    for fr in rec.get("frames", []) or []:
        if str(fr.get("module", "")).lower() == "clipstudiomodeler.exe":
            rva = str(fr.get("rva", ""))
            if rva:
                return rva
    return ""

def modeler_signature(rec: dict, limit: int = 8) -> str:
    rvas = []
    for fr in rec.get("frames", []) or []:
        if str(fr.get("module", "")).lower() == "clipstudiomodeler.exe":
            rva = str(fr.get("rva", ""))
            if rva:
                rvas.append(rva)
        if len(rvas) >= limit:
            break
    return " > ".join(rvas)

def choose_baseline(cands: list[dict]):
    evaluated = []
    for c in cands:
        st = validate_body(c["bytes"])
        evaluated.append({**c, **st})

    valid = [r for r in evaluated if r["valid"]]
    if not valid:
        raise RuntimeError("BASELINE: valid BODY candidate not found.")

    counts = Counter(r["sha256"] for r in valid)
    valid.sort(
        key=lambda r: (counts[r["sha256"]], int(r.get("upload_seq", 0))),
        reverse=True,
    )
    chosen = valid[0]
    chosen_hash = chosen["sha256"]

    admitted = [r for r in valid if r["sha256"] == chosen_hash]
    return chosen, admitted, evaluated

def choose_flex(cands: list[dict], baseline: dict):
    evaluated = []
    admitted = []

    for c in cands:
        st = validate_body(c["bytes"])
        r = {**c, **st}
        r["changed_vertices"] = -1
        r["max_displacement"] = float("nan")
        r["uv_match_baseline"] = False

        if st["valid"]:
            r["uv_match_baseline"] = st["uv_sha256"] == baseline["uv_sha256"]

            if r["uv_match_baseline"]:
                diff, mx = compare_positions(baseline["bytes"], c["bytes"])
                r["changed_vertices"] = len(diff)
                r["max_displacement"] = mx

                if (
                    MIN_CHANGED_VERTICES <= len(diff) <= MAX_CHANGED_VERTICES
                    and mx <= MAX_REASONABLE_DISPLACEMENT
                ):
                    admitted.append(r)

        evaluated.append(r)

    if not admitted:
        raise RuntimeError("ELBOW_FLEX: validated changed BODY candidate not found.")

    counts = Counter(r["sha256"] for r in admitted)
    admitted.sort(
        key=lambda r: (counts[r["sha256"]], int(r.get("upload_seq", 0))),
        reverse=True,
    )
    chosen = admitted[0]
    chosen_hash = chosen["sha256"]

    same_pose = [r for r in admitted if r["sha256"] == chosen_hash]
    return chosen, same_pose, evaluated

def choose_return(cands: list[dict], baseline: dict):
    evaluated = []
    admitted = []

    for c in cands:
        st = validate_body(c["bytes"])
        r = {**c, **st}
        r["uv_match_baseline"] = False

        if st["valid"]:
            r["uv_match_baseline"] = st["uv_sha256"] == baseline["uv_sha256"]
            if r["uv_match_baseline"]:
                admitted.append(r)

        evaluated.append(r)

    if not admitted:
        raise RuntimeError("RETURN: validated BODY candidate not found.")

    exact = [r for r in admitted if r["sha256"] == baseline["sha256"]]
    if exact:
        exact.sort(key=lambda r: int(r.get("upload_seq", 0)), reverse=True)
        chosen = exact[0]
        admitted_group = exact
    else:
        admitted.sort(key=lambda r: int(r.get("upload_seq", 0)), reverse=True)
        chosen = admitted[0]
        chosen_hash = chosen["sha256"]
        admitted_group = [r for r in admitted if r["sha256"] == chosen_hash]

    return chosen, admitted_group, evaluated

def save_body(name: str, rec: dict):
    (out / name).write_bytes(rec["bytes"])

def normalize_records(phase: str, records: list[dict]):
    result = []
    for r in records:
        x = dict(r)
        x["phase"] = phase
        x["first_modeler_rva"] = first_modeler_rva(x)
        x["stack_signature"] = modeler_signature(x)
        result.append(x)
    return result

def write_outputs(records: list[dict]):
    upload_cols = [
        "phase", "upload_seq", "captured_ms", "thread", "api", "target",
        "bound", "offset", "size", "data_ptr", "sha256", "uv_sha256",
        "first_modeler_rva", "stack_signature"
    ]

    with validated_uploads_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=upload_cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in records:
            x = dict(r)
            x.pop("bytes", None)
            w.writerow(x)

    with stack_frames_path.open("w", encoding="utf-8", newline="") as f:
        cols = [
            "phase", "upload_seq", "frame_index", "address",
            "module", "module_base", "rva", "symbol"
        ]
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()

        for r in records:
            for fr in r.get("frames", []) or []:
                row = dict(fr)
                row["phase"] = r["phase"]
                row["upload_seq"] = r.get("upload_seq", "")
                w.writerow(row)

    phase_sig = defaultdict(Counter)
    phase_rva = defaultdict(Counter)

    for r in records:
        sig = r.get("stack_signature", "")
        if sig:
            phase_sig[r["phase"]][sig] += 1

        seen_rvas = set()
        for fr in r.get("frames", []) or []:
            if str(fr.get("module", "")).lower() != "clipstudiomodeler.exe":
                continue
            rva = str(fr.get("rva", ""))
            if rva and rva not in seen_rvas:
                phase_rva[r["phase"]][rva] += 1
                seen_rvas.add(rva)

    with signatures_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["phase", "count", "stack_signature"])
        for phase in ("BASELINE", "ELBOW_FLEX", "RETURN"):
            for sig, count in phase_sig[phase].most_common():
                w.writerow([phase, count, sig])

    with frame_freq_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["phase", "count", "modeler_rva"])
        for phase in ("BASELINE", "ELBOW_FLEX", "RETURN"):
            for rva, count in phase_rva[phase].most_common():
                w.writerow([phase, count, rva])

    phases = ("BASELINE", "ELBOW_FLEX", "RETURN")

    common_sigs = set(phase_sig[phases[0]])
    for p in phases[1:]:
        common_sigs &= set(phase_sig[p])

    common_rvas = set(phase_rva[phases[0]])
    for p in phases[1:]:
        common_rvas &= set(phase_rva[p])

    ranked_sigs = sorted(
        common_sigs,
        key=lambda s: sum(phase_sig[p][s] for p in phases),
        reverse=True,
    )
    ranked_rvas = sorted(
        common_rvas,
        key=lambda r: sum(phase_rva[p][r] for p in phases),
        reverse=True,
    )

    with target_path.open("w", encoding="utf-8") as f:
        f.write("CSMC VBO CALLER GATE V1.6.3 TARGETS\n")
        f.write("===================================\n\n")
        f.write("Do not broad-scan. Use only these ranked targets for the next Ghidra pass.\n\n")

        f.write("[COMMON STACK SIGNATURES]\n")
        if ranked_sigs:
            for i, sig in enumerate(ranked_sigs[:10], 1):
                total = sum(phase_sig[p][sig] for p in phases)
                f.write(f"{i}. total={total}  {sig}\n")
        else:
            f.write("NONE\n")

        f.write("\n[COMMON MODELER RVAS]\n")
        if ranked_rvas:
            for i, rva in enumerate(ranked_rvas[:20], 1):
                counts = ",".join(f"{p}={phase_rva[p][rva]}" for p in phases)
                f.write(f"{i}. {rva}  {counts}\n")
        else:
            f.write("NONE\n")

    return phase_sig, phase_rva, ranked_sigs, ranked_rvas

def package_outputs():
    zip_path = root / ("CSMC_VBO_CALLER_GATE_" + stamp + "_SEND.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob("*")):
            if p.is_file():
                z.write(p, arcname=p.relative_to(out).as_posix())

    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    zip_path.with_suffix(zip_path.suffix + ".sha256.txt").write_text(
        f"{sha}  {zip_path.name}\n",
        encoding="ascii",
    )

    print("")
    print("SEND ZIP:", zip_path)
    print("SHA256:", sha)
    os.system(f'explorer.exe /select,"{zip_path}"')

# ---------------- safety gates ----------------
modeler = Path(MODELER)

if not modeler.exists():
    raise SystemExit("MODELERが見つかりません: " + MODELER)

actual_sha = hashlib.sha256(modeler.read_bytes()).hexdigest().lower()

if actual_sha != KNOWN_SHA256:
    raise SystemExit(
        "MODELER SHA-256不一致のため停止します。\n"
        f"Expected: {KNOWN_SHA256}\n"
        f"Actual:   {actual_sha}"
    )

if (modeler.parent / "opengl32.dll").exists():
    raise SystemExit(
        "MODELER横にopengl32.dllがあります。\n"
        "V1.6.3はcleanupを行いません。既存wrapper状態を確認してください。"
    )

if (root / "MANUAL_WRAPPER_STATE.txt").exists():
    raise SystemExit(
        "MANUAL_WRAPPER_STATE.txtがあります。\n"
        "既存wrapper sessionを先に復旧してください。"
    )

device = frida.get_local_device()
running = [
    p for p in device.enumerate_processes()
    if p.name.lower() == "clipstudiomodeler.exe"
]

if running:
    raise SystemExit("MODELERが既に起動しています。完全に閉じてから再実行してください。")

js = script_path.read_text(encoding="utf-8")

print("MODELER SHA256:", actual_sha)
print("MODELERをFrida配下で起動します...")

pid = device.spawn([MODELER])
session = device.attach(pid)
script = session.create_script(js)
script.on("message", on_message)
script.load()
device.resume(pid)

all_validated = []
run_error = ""
baseline = flex = returned = None

try:
    print("")
    print("CSMC VBO CALLER GATE V1.6.3")
    print("===========================")
    print("この版はcaller/backtrace gateの決着用です。")
    print("MemoryAccessMonitorは使用しません。")
    print("日本語詳細手順: GUIDE_JA.txt")
    print("")

    print("【BASELINE】")
    print("1. POSE_00_BASE_TPOSE.csmc を開いてください。")
    print("2. Tポーズ完全表示後、約3秒待ってください。")
    input("3. 準備できたらEnterを押してください... ")

    base_cands = request_candidates(script, "baseline")
    baseline, base_group, _ = choose_baseline(base_cands)
    save_body("BASELINE_BODY.bin", baseline)

    base_group = normalize_records("BASELINE", base_group)
    all_validated.extend(base_group)

    print("BASELINE VALID")
    print("  sha256       :", baseline["sha256"])
    print("  uv_sha256    :", baseline["uv_sha256"])
    print("  validated uploads:", len(base_group))

    clear_candidates(script)

    print("")
    print("【ELBOW_FLEX】")
    print("4. MODELERへ戻り、左肘だけを大きく曲げてください。")
    print("5. 曲げたまま約3秒待ってください。")
    input("6. 準備できたらEnterを押してください... ")

    flex_cands = request_candidates(script, "flex")
    flex, flex_group, _ = choose_flex(flex_cands, baseline)
    save_body("ELBOW_FLEX_BODY.bin", flex)

    flex_group = normalize_records("ELBOW_FLEX", flex_group)
    all_validated.extend(flex_group)

    diff, mx = compare_positions(baseline["bytes"], flex["bytes"])

    print("ELBOW_FLEX VALID")
    print("  sha256           :", flex["sha256"])
    print("  changed_vertices :", len(diff))
    print("  max_displacement :", mx)
    print("  validated uploads:", len(flex_group))

    clear_candidates(script)

    print("")
    print("【RETURN】")
    print("7. MODELERへ戻り、左肘をTポーズ方向へ戻してください。")
    print("8. 戻したあと約3秒待ってください。")
    input("9. 準備できたらEnterを押してください... ")

    ret_cands = request_candidates(script, "return")
    returned, ret_group, _ = choose_return(ret_cands, baseline)
    save_body("RETURN_BODY.bin", returned)

    ret_group = normalize_records("RETURN", ret_group)
    all_validated.extend(ret_group)

    print("RETURN VALID")
    print("  sha256           :", returned["sha256"])
    print("  baseline exact   :", returned["sha256"] == baseline["sha256"])
    print("  validated uploads:", len(ret_group))

except Exception as e:
    run_error = f"{type(e).__name__}: {e}"
    print("")
    print("[ERROR]", run_error)
    log_event({"kind": "run_error", "error": run_error})

finally:
    try:
        session.detach()
    except Exception:
        pass

phase_sig = defaultdict(Counter)
phase_rva = defaultdict(Counter)
ranked_sigs = []
ranked_rvas = []

if all_validated:
    phase_sig, phase_rva, ranked_sigs, ranked_rvas = write_outputs(all_validated)
else:
    for p in (validated_uploads_path, stack_frames_path, signatures_path, frame_freq_path):
        p.write_text("", encoding="utf-8")
    target_path.write_text("NO VALIDATED UPLOADS\n", encoding="utf-8")

summary = [
    "CSMC VBO CALLER GATE V1.6.3",
    "===========================",
    "",
    f"modeler_sha256={actual_sha}",
    f"body_size={BODY_SIZE}",
    f"stride={STRIDE}",
    f"vertex_count={VERTICES}",
    f"validated_upload_events={len(all_validated)}",
    f"frida_errors={len(frida_errors)}",
    f"run_error={run_error}",
]

if baseline:
    summary += [
        f"baseline_sha256={baseline['sha256']}",
        f"baseline_uv_sha256={baseline['uv_sha256']}",
    ]

if flex:
    d, mx = compare_positions(baseline["bytes"], flex["bytes"])
    summary += [
        f"flex_sha256={flex['sha256']}",
        f"flex_changed_vertices={len(d)}",
        f"flex_max_displacement={mx}",
    ]

if returned:
    summary += [
        f"return_sha256={returned['sha256']}",
        f"return_exact_baseline={returned['sha256'] == baseline['sha256']}",
    ]

summary += [
    f"common_stack_signature_count={len(ranked_sigs)}",
    f"common_modeler_rva_count={len(ranked_rvas)}",
    f"top_common_stack_signature={(ranked_sigs[0] if ranked_sigs else '')}",
    f"top_common_modeler_rva={(ranked_rvas[0] if ranked_rvas else '')}",
    "",
    "completion_rule:",
    "  prefer common stack signature across BASELINE/ELBOW_FLEX/RETURN",
    "  otherwise use common MODELER RVA across all three phases",
    "  next step = targeted Ghidra pass only",
    "",
    "MemoryAccessMonitor_used=false",
    "Base44_used=false",
    "CSMC_saved=false",
    "semantic_promotion=false",
]

summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")

print("")
print(summary_path.read_text(encoding="utf-8"))

package_outputs()

if run_error:
    raise SystemExit(4)
