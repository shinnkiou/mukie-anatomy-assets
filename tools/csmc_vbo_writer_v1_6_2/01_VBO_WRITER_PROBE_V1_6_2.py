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
from collections import Counter
from pathlib import Path

MODELER = r"C:\Program Files\CELSYS\CLIP STUDIO 1.5\CLIP STUDIO MODELER\CLIPStudioModeler.exe"
KNOWN_SHA256 = "2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150"

BODY_SIZE = 1_160_128
STRIDE = 32
VERTICES = BODY_SIZE // STRIDE
MAX_CACHE = 16

MAX_ABS_POSITION = 1_000_000.0
MAX_ABS_NORMAL = 100.0
MAX_ABS_UV = 1000.0
MAX_REASONABLE_DISPLACEMENT = 10_000.0
MIN_CHANGED_VERTICES = 100
MAX_CHANGED_VERTICES = 30_000
POSITION_EPS = 1e-5

root = Path(os.environ.get("USERPROFILE", ".")) / "CSMC_ANALYSIS"
stamp = time.strftime("%Y%m%d_%H%M%S")
out = root / ("VBO_WRITER_VALIDATED_" + stamp)
out.mkdir(parents=True, exist_ok=True)

events_path = out / "EVENTS.jsonl"
candidate_path = out / "CANDIDATE_VALIDATION.tsv"
changed_path = out / "CHANGED_VERTICES.tsv"
writer_path = out / "WRITER_ACCESSES.tsv"
uploads_path = out / "UPLOADS.tsv"
summary_path = out / "SUMMARY.txt"
script_path = Path(__file__).with_name("02_VBO_WRITER_PROBE_V1_6_2.js")

candidate_batches: dict[str, list[dict]] = {}
candidate_done: set[str] = set()
writer_events: list[dict] = []
upload_events: list[dict] = []
status_events: list[dict] = []
frida_errors: list[dict] = []

baseline: dict | None = None
changed_choice: dict | None = None
changed_vertices: list[tuple] = []
watch_vertices: list[int] = []
run_error = ""

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
    elif kind == "writer_access":
        writer_events.append(dict(p))
    elif kind == "body_upload":
        upload_events.append(dict(p))
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
        "invalid_float_count": 0,
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
                result["invalid_float_count"] = 1
                result["reason"] = "non_finite_float"
                return result

            maxp = max(maxp, abs(px), abs(py), abs(pz))
            maxn = max(maxn, abs(nx), abs(ny), abs(nz))
            maxuv = max(maxuv, abs(u), abs(v))

            if maxp > MAX_ABS_POSITION:
                result["max_abs_position"] = maxp
                result["reason"] = "position_out_of_bounds"
                return result
            if maxn > MAX_ABS_NORMAL:
                result["max_abs_normal"] = maxn
                result["reason"] = "normal_out_of_bounds"
                return result
            if maxuv > MAX_ABS_UV:
                result["max_abs_uv"] = maxuv
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

def compare_positions(base: bytes, other: bytes) -> tuple[list[tuple], float]:
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
            changed.append((i, off, d, ax, ay, az, bx, by, bz))
            maxdisp = max(maxdisp, d)

    changed.sort(key=lambda row: row[2], reverse=True)
    return changed, maxdisp

def choose_baseline(cands: list[dict]) -> tuple[dict, list[dict]]:
    evaluated = []

    for c in cands:
        st = validate_body(c["bytes"])
        evaluated.append({**c, **st})

    valid = [r for r in evaluated if r["valid"]]
    if not valid:
        raise RuntimeError("No valid BODY candidate found for BASELINE.")

    counts = Counter(r["sha256"] for r in valid)
    valid.sort(
        key=lambda r: (counts[r["sha256"]], int(r.get("upload_seq", 0))),
        reverse=True
    )

    chosen = valid[0]
    chosen["plateau_count"] = counts[chosen["sha256"]]
    return chosen, evaluated

def choose_changed(
    cands: list[dict],
    baseline_rec: dict,
) -> tuple[dict, list[dict], list[tuple], list[str]]:
    evaluated = []
    qualifying = []
    qualifying_ptrs: list[str] = []

    basebuf = baseline_rec["bytes"]
    base_uv = baseline_rec["uv_sha256"]

    for c in cands:
        st = validate_body(c["bytes"])
        r = {**c, **st}
        r["uv_match_baseline"] = False
        r["changed_vertices"] = -1
        r["max_displacement"] = float("nan")

        if st["valid"]:
            r["uv_match_baseline"] = st["uv_sha256"] == base_uv

            if r["uv_match_baseline"]:
                diff, maxdisp = compare_positions(basebuf, c["bytes"])
                r["changed_vertices"] = len(diff)
                r["max_displacement"] = maxdisp

                if (
                    MIN_CHANGED_VERTICES <= len(diff) <= MAX_CHANGED_VERTICES
                    and maxdisp <= MAX_REASONABLE_DISPLACEMENT
                ):
                    qualifying.append((r, diff))
                    ptr = str(r.get("data_ptr", ""))
                    if ptr and ptr not in qualifying_ptrs:
                        qualifying_ptrs.append(ptr)

        evaluated.append(r)

    if not qualifying:
        raise RuntimeError(
            "No validated CHANGED candidate found. "
            "Required: plausible P/N/UV; UV identical to BASELINE; "
            f"{MIN_CHANGED_VERTICES}..{MAX_CHANGED_VERTICES} changed position vertices; "
            f"max displacement <= {MAX_REASONABLE_DISPLACEMENT}."
        )

    counts = Counter(r["sha256"] for r, _ in qualifying)
    qualifying.sort(
        key=lambda pair: (
            counts[pair[0]["sha256"]],
            int(pair[0].get("upload_seq", 0))
        ),
        reverse=True
    )

    chosen, diff = qualifying[0]
    chosen["plateau_count"] = counts[chosen["sha256"]]
    return chosen, evaluated, diff, qualifying_ptrs

def save_candidate_table(rows: list[dict], phase: str):
    header = [
        "phase", "upload_seq", "data_ptr", "api", "caller_rva",
        "sha256", "length", "valid", "reason",
        "max_abs_position", "max_abs_normal", "max_abs_uv",
        "uv_sha256", "uv_match_baseline", "changed_vertices",
        "max_displacement", "plateau_count"
    ]

    exists = candidate_path.exists()

    with candidate_path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, delimiter="\t", extrasaction="ignore")
        if not exists:
            w.writeheader()

        for r in rows:
            x = dict(r)
            x.pop("bytes", None)
            x["phase"] = phase
            w.writerow(x)

def save_changed(rows: list[tuple]):
    with changed_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow([
            "rank", "vertex_index", "byte_offset", "position_delta",
            "base_x", "base_y", "base_z",
            "changed_x", "changed_y", "changed_z"
        ])
        for rank, row in enumerate(rows, 1):
            w.writerow([rank, *row])

def choose_watch_vertices(rows: list[tuple], max_pages: int = 8) -> list[int]:
    selected = []
    used_pages = set()

    for row in rows:
        vertex = int(row[0])
        byte_off = int(row[1])
        page = byte_off // 4096

        if page in used_pages:
            continue

        used_pages.add(page)
        selected.append(vertex)

        if len(selected) >= max_pages:
            break

    return selected

def write_tables():
    with uploads_path.open("w", encoding="utf-8", newline="") as f:
        cols = [
            "seq", "api", "thread", "target", "bound", "offset",
            "size", "data_ptr", "caller", "caller_rva",
            "captured_ms", "cache_depth"
        ]
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for e in upload_events:
            w.writerow(e)

    with writer_path.open("w", encoding="utf-8", newline="") as f:
        cols = [
            "seq", "round", "operation", "thread", "address",
            "from", "from_rva", "from_symbol", "instruction",
            "range_index", "page_index", "watched_vertex", "watched_ptr"
        ]
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for e in writer_events:
            w.writerow(e)

def package_outputs():
    zip_path = root / ("CSMC_VBO_WRITER_VALIDATED_" + stamp + "_SEND.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob("*")):
            if p.is_file():
                z.write(p, arcname=p.relative_to(out).as_posix())

    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    sha_file = zip_path.with_suffix(zip_path.suffix + ".sha256.txt")
    sha_file.write_text(f"{sha}  {zip_path.name}\n", encoding="ascii")
    print("SEND ZIP:", zip_path)
    print("SHA256:", sha)
    os.system(f'explorer.exe /select,"{zip_path}"')

# ---------- Safety gates ----------
modeler = Path(MODELER)
if not modeler.exists():
    raise SystemExit("MODELER not found: " + MODELER)

actual_sha = hashlib.sha256(modeler.read_bytes()).hexdigest().lower()
if actual_sha != KNOWN_SHA256:
    raise SystemExit(
        "MODELER SHA mismatch. Probe aborted.\n"
        f"Expected: {KNOWN_SHA256}\nActual:   {actual_sha}"
    )

local_ogl = modeler.parent / "opengl32.dll"
manual_state = root / "MANUAL_WRAPPER_STATE.txt"

if manual_state.exists():
    raise SystemExit("MANUAL_WRAPPER_STATE.txt exists. Restore prior wrapper session first.")

if local_ogl.exists():
    raise SystemExit(
        f"Local opengl32.dll exists beside MODELER:\n{local_ogl}\n"
        "This probe does not perform cleanup."
    )

device = frida.get_local_device()
running = [
    p for p in device.enumerate_processes()
    if p.name.lower() == "clipstudiomodeler.exe"
]
if running:
    raise SystemExit("MODELER is already running. Close it and run again.")

js = script_path.read_text(encoding="utf-8")

print("MODELER SHA256:", actual_sha)
print("Spawning MODELER under Frida...")

pid = device.spawn([MODELER])
session = device.attach(pid)
script = session.create_script(js)
script.on("message", on_message)
script.load()
device.resume(pid)

monitor_ptrs: list[str] = []

try:
    print("")
    print("VBO WRITER PROBE V1.6.2 — VALIDATED PLATEAU")
    print("=============================================")
    print("")
    print("1. Open POSE_00_BASE_TPOSE.csmc.")
    print("2. Wait until T-pose is fully visible, then wait about 3 seconds.")
    input("3. Return here and press Enter to validate BASELINE candidates... ")

    base_cands = request_candidates(script, "baseline")
    print("Received BASELINE candidates:", len(base_cands))

    baseline, base_eval = choose_baseline(base_cands)
    save_candidate_table(base_eval, "baseline")
    (out / "BASELINE_BODY.bin").write_bytes(baseline["bytes"])

    print("")
    print("BASELINE VALID")
    print("  sha256       :", baseline["sha256"])
    print("  uv_sha256    :", baseline["uv_sha256"])
    print("  plateau_count:", baseline.get("plateau_count", 1))
    print("  data_ptr      :", baseline.get("data_ptr", ""))

    print("")
    print("4. Return to MODELER and bend ONLY the LEFT ELBOW clearly.")
    print("5. Wait about 3 seconds after the pose settles.")
    input("6. Return here and press Enter to validate CHANGED candidates... ")

    changed_cands = request_candidates(script, "changed")
    print("Received CHANGED candidates:", len(changed_cands))

    changed_choice, changed_eval, changed_vertices, qualifying_ptrs = choose_changed(
        changed_cands, baseline
    )
    save_candidate_table(changed_eval, "changed")
    (out / "CHANGED_BODY.bin").write_bytes(changed_choice["bytes"])
    save_changed(changed_vertices)

    watch_vertices = choose_watch_vertices(changed_vertices, 8)

    monitor_ptrs = []
    for c in reversed(changed_eval):
        if c.get("valid") and c.get("uv_match_baseline"):
            ptr = str(c.get("data_ptr", ""))
            if ptr and ptr not in monitor_ptrs:
                monitor_ptrs.append(ptr)
        if len(monitor_ptrs) >= 12:
            break

    bptr = str(baseline.get("data_ptr", ""))
    if bptr and bptr not in monitor_ptrs:
        monitor_ptrs.append(bptr)

    print("")
    print("CHANGED VALID")
    print("  sha256            :", changed_choice["sha256"])
    print("  uv_sha256         :", changed_choice["uv_sha256"])
    print("  plateau_count     :", changed_choice.get("plateau_count", 1))
    print("  changed_vertices  :", len(changed_vertices))
    print("  max_displacement  :", changed_vertices[0][2] if changed_vertices else 0.0)
    print("  data_ptr          :", changed_choice.get("data_ptr", ""))
    print("  watch_vertices    :", ",".join(map(str, watch_vertices)))
    print("  monitor_ptrs      :", len(monitor_ptrs))
    print("")
    print("Keep the LEFT ELBOW BENT.")
    print("Do NOT move it until AFTER the writer watch is ARMED.")

    previous_count = 0

    for round_no in range(1, 4):
        input(f"[Round {round_no}/3] Press Enter to ARM writer watch... ")

        script.post({
            "type": "command",
            "payload": {
                "cmd": "monitor",
                "vertices": watch_vertices,
                "pointers": monitor_ptrs,
                "round": round_no,
            },
        })
        time.sleep(0.6)

        if round_no % 2 == 1:
            print("ARMED. Now move LEFT ELBOW toward T-pose.")
        else:
            print("ARMED. Now bend LEFT ELBOW again.")

        print("Wait 2–3 seconds after movement.")
        input("Return here and press Enter to stop this round... ")

        script.post({"type": "command", "payload": {"cmd": "stop_monitor"}})
        time.sleep(0.5)

        current = writer_events[previous_count:]
        previous_count = len(writer_events)
        writes = [e for e in current if e.get("operation") == "write"]

        print("  memory_access_events:", len(current))
        print("  write_events        :", len(writes))

        if writes:
            print("WRITE captured.")
            break

        if round_no < 3:
            print("No write captured yet; one more controlled round.")

except Exception as e:
    run_error = f"{type(e).__name__}: {e}"
    print("")
    print("[RUN ERROR]", run_error)
    log_event({"kind": "run_error", "error": run_error})

finally:
    try:
        script.post({"type": "command", "payload": {"cmd": "stop_monitor"}})
        time.sleep(0.2)
    except Exception:
        pass

    try:
        session.detach()
    except Exception:
        pass

write_tables()

write_events = [e for e in writer_events if e.get("operation") == "write"]
modeler_writes = [
    e for e in write_events
    if str(e.get("from_rva", "")).startswith("0x")
]

ptr_counts = Counter(
    e.get("data_ptr", "")
    for e in upload_events
    if e.get("data_ptr")
)

with (out / "POINTER_REUSE.tsv").open("w", encoding="utf-8") as f:
    f.write("data_ptr\tcount\n")
    for ptr, count in ptr_counts.most_common(20):
        f.write(f"{ptr}\t{count}\n")

summary = [
    "CSMC VBO WRITER PROBE V1.6.2 — VALIDATED PLATEAU",
    "=================================================",
    "",
    f"modeler_sha256={actual_sha}",
    f"body_size={BODY_SIZE}",
    f"stride={STRIDE}",
    f"vertex_count={VERTICES}",
    f"body_upload_events={len(upload_events)}",
    f"frida_errors={len(frida_errors)}",
    f"run_error={run_error}",
]

if baseline:
    summary += [
        f"baseline_sha256={baseline['sha256']}",
        f"baseline_uv_sha256={baseline['uv_sha256']}",
        f"baseline_plateau_count={baseline.get('plateau_count', 1)}",
        f"baseline_ptr={baseline.get('data_ptr', '')}",
    ]

if changed_choice:
    summary += [
        f"changed_sha256={changed_choice['sha256']}",
        f"changed_uv_sha256={changed_choice['uv_sha256']}",
        f"changed_plateau_count={changed_choice.get('plateau_count', 1)}",
        f"changed_ptr={changed_choice.get('data_ptr', '')}",
        f"changed_position_vertices={len(changed_vertices)}",
        f"max_position_displacement={(changed_vertices[0][2] if changed_vertices else 0.0)}",
        f"watch_vertices={','.join(map(str, watch_vertices))}",
        f"monitor_ptr_count={len(monitor_ptrs)}",
    ]

summary += [
    f"writer_access_events={len(writer_events)}",
    f"writer_write_events={len(write_events)}",
    f"modeler_rva_write_events={len(modeler_writes)}",
    f"unique_upload_pointers={len(ptr_counts)}",
    "",
    "validation_rules:",
    "  finite_PNUV=true",
    f"  max_abs_position<={MAX_ABS_POSITION}",
    f"  max_abs_normal<={MAX_ABS_NORMAL}",
    f"  max_abs_uv<={MAX_ABS_UV}",
    "  changed_uv_equals_baseline=true",
    f"  changed_vertices={MIN_CHANGED_VERTICES}..{MAX_CHANGED_VERTICES}",
    f"  max_displacement<={MAX_REASONABLE_DISPLACEMENT}",
    "  stable_hash_plateau_preferred=true",
    "",
    "semantic_promotion=false",
    "Base44_used=false",
    "CSMC_saved=false",
]

summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")

print("")
print(summary_path.read_text(encoding="utf-8"))
package_outputs()

if run_error:
    raise SystemExit(4)
