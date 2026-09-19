from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

RVA_RE = re.compile(r"^0x[0-9a-f]+$")

def read_tsv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def write_tsv(path: Path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)

def safe_text(path: Path) -> str:
    try:
        data = path.read_bytes()
    except Exception:
        return ""
    for enc in ("utf-8", "utf-8-sig", "utf-16", "cp932", "latin1"):
        try:
            return data.decode(enc)
        except Exception:
            pass
    return ""

def load_manifest(path: Path):
    by = defaultdict(list)
    for r in read_tsv(path):
        rva = (r.get("rva") or "").lower()
        if RVA_RE.match(rva):
            by[rva].append(r)
    return by

def body_for(rva: str, manifest, roots, new_dir: Path) -> tuple[str, str]:
    # Existing snapshot decompile always wins; do not replace it with a fresh Ghidra result.
    parts = []
    sources = []
    seen_sha = set()
    for m in manifest.get(rva, []):
        sha = m.get("sha256", "")
        if sha and sha in seen_sha:
            continue
        if sha:
            seen_sha.add(sha)
        root = roots.get(m.get("snapshot", ""))
        if root is None:
            continue
        p = root / m.get("file", "")
        t = safe_text(p)
        if t:
            parts.append(t)
            sources.append(f"{m.get('snapshot')}:{m.get('file')}")
        if len(parts) >= 3:
            break
    if parts:
        return "\n\n".join(parts), "EXISTING:" + " | ".join(sources)

    suffix = rva[2:]
    matches = sorted(new_dir.glob(f"*_{suffix}.c.txt"))
    if matches:
        return safe_text(matches[0]), "NEW_GHIDRA:" + matches[0].name
    return "", "MISSING"

def count_calls(body: str) -> int:
    return len(set(re.findall(r"\bFUN_1[0-9a-fA-F]{8,15}\b", body)))

def bool01(v: bool) -> int:
    return 1 if v else 0

def classify(body: str):
    low = body.lower()
    notes = []
    score = 0

    string_init = ("pwstring::vftable" in low or "fun_1408b3b20" in low) and "atexit" in low
    string_dtor = "pwstring::vftable" in low and "lock()" in low and "unlock()" in low and "atexit" not in low

    has_read_words = any(x in low for x in ("read(", "stream", "cursor", "input", "fread", "readfile"))
    has_buffer_word = "buffer" in low
    has_copy = any(x in low for x in ("memcpy", "memmove", "copy", "fun_1408c27c0"))
    has_alloc = any(x in low for x in ("operator new", "malloc", "calloc", "realloc", "fun_140a98310"))
    has_decode = any(x in low for x in ("decode", "decompress", "inflate", "uncompress", "zlib", "codec"))
    has_virtual = "(**(code **)" in body or "(*(" in body and "code **" in body
    has_loop = any(x in low for x in ("for (", "while (", "do {"))
    has_length = any(x in low for x in ("length", "size", "count", "offset"))
    uiish = any(x in low for x in ("qwidget", "qobject", "palette", "dialog", "ui_", "cpalette", "action"))

    # Approximate writes to this/param_1.
    writes_this = bool(
        re.search(r"\*\s*\([^\n;]*param_1[^\n;]*\)\s*=", body)
        or re.search(r"param_1\s*\[[^\]]+\]\s*=", body)
        or re.search(r"\*param_1\s*=", body)
    )
    reads_buffer = has_read_words or has_buffer_word or has_copy

    line_count = max(1, body.count("\n") + 1)
    direct_calls = count_calls(body)

    # Fast terminal classes first.
    if string_init:
        cls = "UI / NAME"
        score -= 6
        notes.append("PWString/global-name initializer")
    elif string_dtor:
        cls = "CTOR / DTOR"
        score -= 4
        notes.append("PWString/reference-count cleanup")
    elif has_decode:
        cls = "DECODE"
        score += 6
    elif has_copy and writes_this and has_loop:
        cls = "DESERIALIZER"
        score += 8
    elif reads_buffer and writes_this:
        cls = "DESERIALIZER"
        score += 7
    elif has_read_words:
        cls = "STREAM"
        score += 5
    elif has_buffer_word and writes_this:
        cls = "BUFFER"
        score += 5
    elif has_copy:
        cls = "COPY"
        score += 4
    elif has_buffer_word:
        cls = "BUFFER"
        score += 3
    elif has_alloc:
        cls = "ALLOCATOR"
        score += 3
    elif line_count < 30 and direct_calls <= 1 and not has_loop:
        cls = "GETTER / SETTER"
        score -= 2
    else:
        cls = "UNKNOWN"

    if reads_buffer:
        score += 3
        notes.append("buffer/stream read indicators")
    if writes_this:
        score += 3
        notes.append("writes param_1/this")
    if has_loop:
        score += 2
        notes.append("loop")
    if has_alloc:
        score += 2
        notes.append("allocation")
    if has_virtual:
        score += 2
        notes.append("virtual call")
    if has_length:
        score += 1
        notes.append("length/count/offset")
    if uiish:
        score -= 3
        notes.append("UI-like symbols")
    if string_init:
        score = min(score, -4)

    return {
        "classification": cls,
        "reads_buffer": bool01(reads_buffer),
        "writes_this": bool01(writes_this),
        "interesting_score": score,
        "notes": "; ".join(notes),
        "direct_call_tokens": direct_calls,
        "line_count": line_count,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--full-root", required=True)
    ap.add_argument("--focused-root", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    roots = {"FULL": Path(args.full_root), "FOCUSED": Path(args.focused_root)}
    new_dir = out / "NEW_DECOMPILE"

    slots = read_tsv(out / "P1_SLOT_RAW.tsv")
    edges = read_tsv(out / "P1_CALL_CHAIN_RAW.tsv")

    calls_from = defaultdict(list)
    node_depth = {}
    for e in edges:
        fr = (e.get("from_rva") or "").lower()
        to = (e.get("to_rva") or "").lower()
        if fr and to:
            calls_from[fr].append(to)
        if to:
            try:
                d = int(e.get("depth") or 99)
            except Exception:
                d = 99
            node_depth[to] = min(node_depth.get(to, 99), d)

    map_rows = []
    interesting_chain = []

    for s in slots:
        target = (s.get("target") or "").lower()
        if not RVA_RE.match(target):
            continue
        body, source = body_for(target, manifest, roots, new_dir)
        info = classify(body) if body else {
            "classification": "UNKNOWN",
            "reads_buffer": 0,
            "writes_this": 0,
            "interesting_score": 0,
            "notes": "body unavailable",
            "direct_call_tokens": 0,
            "line_count": 0,
        }
        calls = []
        for x in calls_from.get(target, []):
            if x not in calls:
                calls.append(x)
        row = {
            "class": s.get("class", ""),
            "vtable": s.get("vtable", ""),
            "slot": s.get("slot", ""),
            "target": target,
            "has_existing_decompile": s.get("has_existing_decompile", "0"),
            "classification": info["classification"],
            "calls": ",".join(calls[:12]),
            "reads_buffer": info["reads_buffer"],
            "writes_this": info["writes_this"],
            "interesting_score": info["interesting_score"],
            "notes": (info["notes"] + ("; " if info["notes"] else "") + source),
        }
        map_rows.append(row)

    # Classify bounded downstream nodes so thin wrappers can point to the real reader.
    unique_nodes = {}
    for e in edges:
        rva = (e.get("to_rva") or "").lower()
        if not RVA_RE.match(rva):
            continue
        key = (e.get("class",""), e.get("vtable",""), e.get("slot",""), rva)
        if key in unique_nodes:
            continue
        unique_nodes[key] = e

    for key, e in unique_nodes.items():
        rva = key[3]
        body, source = body_for(rva, manifest, roots, new_dir)
        info = classify(body) if body else {
            "classification": "UNKNOWN", "reads_buffer":0, "writes_this":0,
            "interesting_score":0, "notes":"body unavailable", "direct_call_tokens":0, "line_count":0
        }
        if info["interesting_score"] >= 4 or info["classification"] in ("STREAM","BUFFER","DESERIALIZER","COPY","DECODE"):
            interesting_chain.append({
                "class": e.get("class",""),
                "vtable": e.get("vtable",""),
                "slot": e.get("slot",""),
                "depth": e.get("depth",""),
                "from_rva": e.get("from_rva",""),
                "target": rva,
                "classification": info["classification"],
                "reads_buffer": info["reads_buffer"],
                "writes_this": info["writes_this"],
                "interesting_score": info["interesting_score"],
                "calls": ",".join(calls_from.get(rva, [])[:12]),
                "notes": info["notes"] + ("; " if info["notes"] else "") + source,
            })

    map_rows.sort(key=lambda r: (r["class"], int(r["slot"])))
    interesting_chain.sort(key=lambda r: (-int(r["interesting_score"]), r["class"], int(r["slot"]), int(r["depth"] or 99)))

    write_tsv(out / "VTABLE_DISPATCH_MAP.tsv", map_rows, [
        "class","vtable","slot","target","has_existing_decompile","classification","calls",
        "reads_buffer","writes_this","interesting_score","notes"
    ])
    write_tsv(out / "P1_INTERESTING_CHAIN.tsv", interesting_chain, [
        "class","vtable","slot","depth","from_rva","target","classification","reads_buffer",
        "writes_this","interesting_score","calls","notes"
    ])

    precheck = safe_text(out / "P1_PRECHECK_1400452b0.txt")
    pre_body = ""
    if "decompile_begin" in precheck and "decompile_end" in precheck:
        pre_body = precheck.split("decompile_begin",1)[1].split("decompile_end",1)[0]
    pre_info = classify(pre_body) if pre_body else None

    summary = [
        "# CSMC P1 — VTABLE DISPATCH MAP",
        "",
        "Scope: two known loader vtables (18 slots) plus one-time 0x1400452b0 precheck.",
        "Existing snapshot decompiles are reused and are not re-decompiled.",
        "Call-chain expansion is bounded to depth 3 and wrapper-biased.",
        "semantic_promotion=false",
        "",
        f"- slot rows: **{len(map_rows)}**",
        f"- interesting downstream rows: **{len(interesting_chain)}**",
        "",
        "## 0x1400452b0 precheck",
        "",
    ]
    if pre_info:
        summary += [
            f"- classification: **{pre_info['classification']}**",
            f"- interesting_score: **{pre_info['interesting_score']}**",
            f"- notes: {pre_info['notes']}",
        ]
    else:
        summary += ["- classification: see P1_PRECHECK_1400452b0.txt"]

    summary += ["", "## Slot map", ""]
    for r in map_rows:
        summary.append(
            f"- {r['class']} slot {r['slot']} -> {r['target']} "
            f"[{r['classification']}] score={r['interesting_score']} "
            f"existing={r['has_existing_decompile']}"
        )

    summary += ["", "## Highest-interest downstream nodes", ""]
    for r in interesting_chain[:24]:
        summary.append(
            f"- {r['class']} slot {r['slot']} depth {r['depth']}: "
            f"{r['from_rva']} -> {r['target']} [{r['classification']}] "
            f"score={r['interesting_score']}"
        )

    summary += [
        "",
        "## Success condition",
        "",
        "A proof-grade result requires one bounded path from a factory-created loader object / vtable slot",
        "to a concrete function that consumes stream/buffer data into internal object state.",
        "Static naming or FBX capability alone is not semantic promotion.",
    ]

    (out / "P1_SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    packet = [
        "# CSMC P1 CHATGPT PACKET",
        "",
        (out / "P1_SUMMARY.md").read_text(encoding="utf-8"),
        "",
        "--- VTABLE_DISPATCH_MAP.tsv ---",
        (out / "VTABLE_DISPATCH_MAP.tsv").read_text(encoding="utf-8", errors="replace"),
        "",
        "--- P1_INTERESTING_CHAIN.tsv ---",
        (out / "P1_INTERESTING_CHAIN.tsv").read_text(encoding="utf-8", errors="replace")[:200000],
        "",
        "--- PRECHECK ---",
        precheck[:40000],
    ]
    (out / "P1_CHATGPT_PACKET.md").write_text("\n".join(packet) + "\n", encoding="utf-8")

    print("P1_SLOT_ROWS=" + str(len(map_rows)))
    print("P1_INTERESTING_CHAIN_ROWS=" + str(len(interesting_chain)))
    print("P1_PACKET=" + str(out / "P1_CHATGPT_PACKET.md"))

if __name__ == "__main__":
    main()
