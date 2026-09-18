import frida
import hashlib
import os
import time
from pathlib import Path

MODELER = r"C:\Program Files\CELSYS\CLIP STUDIO 1.5\CLIP STUDIO MODELER\CLIPStudioModeler.exe"
BODY_SIZE = 1160128
EBO_SIZE = 751056

base = Path(os.environ.get("USERPROFILE", ".")) / "CSMC_ANALYSIS"
out = base / ("RUNTIME_VBO_PROBE_" + time.strftime("%Y%m%d_%H%M%S"))
out.mkdir(parents=True, exist_ok=True)

js = Path(__file__).with_name("05_MODELER_GL_PROBE.js").read_text(encoding="utf-8")
device = frida.get_local_device()

running = [p for p in device.enumerate_processes() if p.name.lower() == "clipstudiomodeler.exe"]
if running:
    raise SystemExit("MODELER is already running. Close it and run again.")
if not os.path.exists(MODELER):
    raise SystemExit("MODELER not found: " + MODELER)

events_file = out / "RUNTIME_UPLOADS.tsv"
bt_file = out / "BACKTRACES.txt"
events_file.write_text("event\tapi\tthread\ttarget\tbound_buffer\toffset\tsize\tdata_ptr\tsha256\tfile\n", encoding="utf-8")

events = 0
body_events = 0
ebo_events = 0
seen = {}

def on_message(message, data):
    global events, body_events, ebo_events
    if message.get("type") == "error":
        with bt_file.open("a", encoding="utf-8") as f:
            f.write("\nFRIDA ERROR\n" + str(message) + "\n")
        return

    p = message.get("payload")
    if not isinstance(p, dict) or p.get("type") != "upload":
        return

    events += 1
    size = int(p.get("size", 0))
    prefix = "OTHER"
    if size == BODY_SIZE:
        body_events += 1
        prefix = "BODY"
    elif size == EBO_SIZE:
        ebo_events += 1
        prefix = "EBO"

    sha = ""
    filename = ""
    if data:
        raw = bytes(data)
        sha = hashlib.sha256(raw).hexdigest()
        if sha not in seen:
            filename = prefix + "_" + sha[:16] + ".bin"
            (out / filename).write_bytes(raw)
            seen[sha] = filename
        else:
            filename = seen[sha]

    with events_file.open("a", encoding="utf-8", newline="") as f:
        f.write(
            str(events) + "\t" + str(p.get("api","")) + "\t" + str(p.get("thread","")) + "\t" +
            str(p.get("target","")) + "\t" + str(p.get("bound","")) + "\t" + str(p.get("offset","")) + "\t" +
            str(size) + "\t" + str(p.get("data","")) + "\t" + sha + "\t" + filename + "\n"
        )

    with bt_file.open("a", encoding="utf-8") as f:
        f.write("\n" + "=" * 72 + "\n")
        f.write("EVENT " + str(events) + "\n")
        f.write("API=" + str(p.get("api")) + "\n")
        f.write("SIZE=" + str(size) + "\n")
        f.write("DATA=" + str(p.get("data")) + "\n")
        f.write("SHA256=" + sha + "\nBACKTRACE:\n")
        for line in p.get("backtrace", []):
            f.write("  " + str(line) + "\n")

print("Spawning MODELER under Frida...")
pid = device.spawn([MODELER])
session = device.attach(pid)
script = session.create_script(js)
script.on("message", on_message)
script.load()
device.resume(pid)

print("RUNTIME PROBE ACTIVE")
print("Load the model, keep camera fixed, then do BASE -> L_ELBOW_FLEX -> BASE.")
print("Do not save or overwrite the CSMC.")
input("When finished, press Enter here... ")

try:
    session.detach()
except Exception:
    pass

summary = "\n".join([
    "CSMC RUNTIME VBO PROBE V1",
    "=========================",
    "",
    "events=" + str(events),
    "body_upload_events=" + str(body_events),
    "ebo_upload_events=" + str(ebo_events),
    "unique_payloads=" + str(len(seen)),
    "",
    "Known body VBO: 1160128 bytes",
    "Known EBO: 751056 bytes",
    "Inspect RUNTIME_UPLOADS.tsv and BACKTRACES.txt",
    "semantic_promotion=false",
    ""
])
(out / "SUMMARY.txt").write_text(summary, encoding="utf-8")
print(summary)
print("Saved:", out)
