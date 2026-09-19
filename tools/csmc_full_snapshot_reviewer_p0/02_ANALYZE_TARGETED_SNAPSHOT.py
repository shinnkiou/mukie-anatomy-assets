from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

TEXT_EXTS = {
    ".txt", ".md", ".json", ".jsonl", ".tsv", ".csv", ".log",
    ".xml", ".yaml", ".yml", ".ini", ".cfg", ".ps1", ".bat", ".cmd",
    ".py", ".java", ".c", ".cc", ".cpp", ".h", ".hpp", ".asm", ".s",
}
MAX_FILE_BYTES = 24 * 1024 * 1024
CONTEXT_RADIUS = 420
RVA_RE = re.compile(r"0x1[0-9a-fA-F]{7,15}")
FUNC_RE = re.compile(r"\bFUN_1[0-9a-fA-F]{7,15}\b")

def func_token_to_addr(token: str) -> str:
    # Ghidra function tokens are executable-code evidence.  The earlier P0
    # only promoted literal 0x... strings, which caused a false zero-candidate
    # result because snapshot exports mostly use FUN_140... and bare hex.
    if token.startswith("FUN_"):
        return "0x" + token[4:].lower()
    return ""

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--known", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--input", action="append", default=[])
    return ap.parse_args()

def safe_read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return ""
        data = path.read_bytes()
    except Exception:
        return ""
    for enc in ("utf-8", "utf-8-sig", "utf-16", "cp932", "latin1"):
        try:
            return data.decode(enc)
        except Exception:
            pass
    return ""

def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def excerpt(text: str, start: int, end: int, radius: int = CONTEXT_RADIUS) -> str:
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    return normalize_space(text[a:b])

def term_positions(text_lower: str, terms: list[str]):
    for term in terms:
        t = term.lower()
        start = 0
        while True:
            i = text_lower.find(t, start)
            if i < 0:
                break
            yield term, i, i + len(t)
            start = i + max(1, len(t))

def score_context(ctx: str, groups: dict[str, list[str]], known_rvas: set[str]):
    low = ctx.lower()
    scores = {"consumer": 0, "bridge": 0, "transform": 0}
    for category, terms in groups.items():
        for term in terms:
            if term.lower() in low:
                scores[category] += 1
    rvas = sorted(set(x.lower() for x in RVA_RE.findall(ctx)))
    funcs = sorted(set(FUNC_RE.findall(ctx)))
    new_rvas = [r for r in rvas if r not in known_rvas]
    known_hits = [r for r in rvas if r in known_rvas]
    bonus = 0
    if scores["consumer"] >= 2:
        bonus += 4
    if scores["consumer"] >= 1 and scores["bridge"] >= 1:
        bonus += 5
    if scores["consumer"] >= 1 and scores["transform"] >= 1:
        bonus += 5
    if scores["bridge"] >= 1 and scores["transform"] >= 1:
        bonus += 3
    if new_rvas:
        bonus += min(6, len(new_rvas) * 2)
    if funcs:
        bonus += min(4, len(funcs))
    return sum(scores.values()) + bonus, scores, rvas, new_rvas, known_hits, funcs

def classify_file_name(name: str) -> str:
    low = name.lower()
    if any(k in low for k in ("ghidra", "decomp", "pcode", "xref", "callgraph", "function")):
        return "static-analysis"
    if any(k in low for k in ("handoff", "summary", "report", "checkpoint", "evidence")):
        return "summary-report"
    if any(k in low for k in ("trace", "frida", "opengl", "vbo", "upload")):
        return "runtime-trace"
    if any(k in low for k in ("character", "payload", "loader", "reader", "consumer", "modeldata")):
        return "consumer-lane"
    return "other"

WEAK_CANDIDATE_SOURCES = {
    "call_edges.tsv",
    "functions.tsv",
    "namespaces.tsv",
    "strings.tsv",
    "targeted_decompile_index.tsv",
    "focused_decompile_index.tsv",
}

def candidate_functions_for_hit(rel: str, text: str, start: int, end: int):
    """
    P0.7 anti-noise rule:
    - decompile files: promote only the function owned by the filename
    - broad graph/index files: never originate a candidate
    - other structured evidence: promote only FUN_ tokens very near the hit
    This prevents one call_edges context from promoting dozens of unrelated helpers.
    """
    name = Path(rel).name.lower()
    path_funcs = sorted(set(FUNC_RE.findall(rel)))
    if path_funcs and ("decompile" in rel.lower() or rel.lower().endswith(".c.txt")):
        return path_funcs, "direct_decompile"

    if name in WEAK_CANDIDATE_SOURCES:
        return [], "context_only"

    a = max(0, start - 140)
    b = min(len(text), end + 140)
    near = text[a:b]
    near_funcs = sorted(set(FUNC_RE.findall(near)))
    if near_funcs:
        return near_funcs, "direct_near"
    return [], "context_only"

def write_tsv(path: Path, rows: list[dict], fields: list[str]):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)

def main():
    args = parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    known = json.loads(Path(args.known).read_text(encoding="utf-8"))
    known_rvas = {x.lower() for x in known.get("known_rvas", [])}
    groups = known.get("positive_terms", {})

    inputs = []
    for item in args.input:
        if "=" not in item:
            raise SystemExit("Bad --input: " + item)
        label, p = item.split("=", 1)
        inputs.append((label.strip(), Path(p)))

    hits = []
    files_summary = []
    evidence_by_rva = defaultdict(list)
    category_counts = Counter()
    scanned_files = 0
    skipped_large = 0
    empty_decode = 0

    seed_terms = []
    for terms in groups.values():
        seed_terms.extend(terms)
    seed_terms += [
        "CLIP_STUDIO_3D_DATA2", "character", "payload",
        "ModelData", "ExternalChunk"
    ]

    for label, root in inputs:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
                continue
            try:
                size = path.stat().st_size
            except Exception:
                continue
            if size > MAX_FILE_BYTES:
                skipped_large += 1
                continue
            text = safe_read_text(path)
            if not text:
                empty_decode += 1
                continue

            scanned_files += 1
            rel = str(path.relative_to(root))
            low = text.lower()
            fname_class = classify_file_name(rel)
            file_hits = 0
            file_score = 0
            seen_context_keys = set()

            for term, start, end in term_positions(low, seed_terms):
                ctx = excerpt(text, start, end)
                total, scores, rvas, new_rvas, known_hits, funcs = score_context(
                    ctx, groups, known_rvas
                )

                # P0.7: literal 0x... values remain context only.
                # Candidate promotion is restricted to a decompile owner or a
                # FUN_ token close to the exact keyword hit.
                literal_new_rvas = list(new_rvas)
                promoted_funcs, candidate_source = candidate_functions_for_hit(
                    rel, text, start, end
                )
                promoted_addrs = sorted(set(
                    func_token_to_addr(x) for x in promoted_funcs
                    if func_token_to_addr(x)
                ))
                candidate_new = [x for x in promoted_addrs if x not in known_rvas]
                candidate_known = [x for x in promoted_addrs if x in known_rvas]

                all_funcs = sorted(set(funcs + promoted_funcs))
                if candidate_new:
                    total += min(8, 4 * len(candidate_new))
                known_hits = sorted(set(known_hits + candidate_known))
                new_rvas = candidate_new
                funcs = all_funcs

                if total < 4:
                    continue
                key = (rel, ctx[:240])
                if key in seen_context_keys:
                    continue
                seen_context_keys.add(key)
                categories = [cat for cat, s in scores.items() if s > 0] or ["context-only"]
                row = {
                    "snapshot": label,
                    "file": rel,
                    "file_class": fname_class,
                    "seed_term": term,
                    "score": total,
                    "categories": ",".join(categories),
                    "consumer_score": scores["consumer"],
                    "bridge_score": scores["bridge"],
                    "transform_score": scores["transform"],
                    "new_rvas": ",".join(new_rvas),
                    "known_rvas": ",".join(known_hits),
                    "functions": ",".join(funcs),
                    "code_source": candidate_source,
                    "context_literal_rvas": ",".join(literal_new_rvas),
                    "excerpt": ctx,
                }
                hits.append(row)
                file_hits += 1
                file_score += total
                for cat in categories:
                    category_counts[cat] += 1
                for rva in new_rvas:
                    evidence_by_rva[rva].append(row)

            files_summary.append({
                "snapshot": label,
                "file": rel,
                "bytes": size,
                "file_class": fname_class,
                "targeted_hit_count": file_hits,
                "targeted_score": file_score,
            })

    hits.sort(key=lambda r: (-int(r["score"]), r["snapshot"], r["file"]))
    files_summary.sort(
        key=lambda r: (-int(r["targeted_score"]), -int(r["targeted_hit_count"]), r["file"])
    )

    candidate_rows = []
    for rva, raw_evs in evidence_by_rva.items():
        # Repeated keyword windows in the same file must not dominate ranking.
        best_by_file = {}
        for e in raw_evs:
            k = (e["snapshot"], e["file"])
            old = best_by_file.get(k)
            if old is None or int(e["score"]) > int(old["score"]):
                best_by_file[k] = e
        evs = list(best_by_file.values())

        snapshots = sorted(set(e["snapshot"] for e in evs))
        files = sorted(set(e["file"] for e in evs))
        cats = Counter()
        total_score = 0
        max_score = 0
        consumer = bridge = transform = 0
        code_evidence_count = 0
        direct_decompile_count = 0
        direct_near_count = 0
        for e in evs:
            total_score += int(e["score"])
            max_score = max(max_score, int(e["score"]))
            consumer += int(e["consumer_score"])
            bridge += int(e["bridge_score"])
            transform += int(e["transform_score"])
            if e.get("code_source") in ("direct_decompile", "direct_near"):
                code_evidence_count += 1
            if e.get("code_source") == "direct_decompile":
                direct_decompile_count += 1
            if e.get("code_source") == "direct_near":
                direct_near_count += 1
            for cat in e["categories"].split(","):
                if cat:
                    cats[cat] += 1
        aggregate = total_score
        if len(snapshots) >= 2:
            aggregate += 10
        if sum(1 for x in (consumer, bridge, transform) if x > 0) >= 2:
            aggregate += 8
        if len(files) >= 2:
            aggregate += min(8, len(files) * 2)
        candidate_rows.append({
            "rva": rva,
            "aggregate_score": aggregate,
            "max_context_score": max_score,
            "evidence_count": len(evs),
            "snapshot_count": len(snapshots),
            "snapshots": ",".join(snapshots),
            "file_count": len(files),
            "consumer_score": consumer,
            "bridge_score": bridge,
            "transform_score": transform,
            "code_evidence_count": code_evidence_count,
            "direct_decompile_count": direct_decompile_count,
            "direct_near_count": direct_near_count,
            "categories": ",".join(k for k, _ in cats.most_common()),
            "files": " | ".join(files[:12]),
            "best_excerpt": max(evs, key=lambda e: int(e["score"]))["excerpt"],
        })

    candidate_rows.sort(
        key=lambda r: (-int(r["aggregate_score"]), -int(r["evidence_count"]), r["rva"])
    )

    novel_rows = [
        r for r in hits
        if int(r["score"]) >= 8 and (
            r["new_rvas"] or (
                int(r["consumer_score"]) >= 2 and
                (int(r["bridge_score"]) >= 1 or int(r["transform_score"]) >= 1)
            )
        )
    ][:300]

    write_tsv(
        out / "targeted_hits.tsv", hits,
        ["snapshot", "file", "file_class", "seed_term", "score", "categories",
         "consumer_score", "bridge_score", "transform_score", "new_rvas",
         "known_rvas", "functions", "code_source", "context_literal_rvas", "excerpt"]
    )
    write_tsv(
        out / "candidate_files.tsv", files_summary,
        ["snapshot", "file", "bytes", "file_class", "targeted_hit_count", "targeted_score"]
    )
    write_tsv(
        out / "consumer_candidates.tsv", candidate_rows,
        ["rva", "aggregate_score", "max_context_score", "evidence_count",
         "snapshot_count", "snapshots", "file_count", "consumer_score",
         "bridge_score", "transform_score", "code_evidence_count", "direct_decompile_count", "direct_near_count", "categories", "files", "best_excerpt"]
    )
    write_tsv(
        out / "novel_evidence.tsv", novel_rows,
        ["snapshot", "file", "score", "categories", "consumer_score",
         "bridge_score", "transform_score", "new_rvas", "known_rvas",
         "functions", "code_source", "excerpt"]
    )

    ghidra_targets = [
        r for r in candidate_rows
        if int(r["aggregate_score"]) >= 12
        and int(r.get("code_evidence_count", 0)) >= 1
        and (
            int(r["consumer_score"]) >= 1
            or int(r["bridge_score"]) >= 1
            or int(r["transform_score"]) >= 2
        )
    ][:8]
    with (out / "ghidra_targets.txt").open("w", encoding="utf-8") as f:
        f.write("# CSMC FULL SNAPSHOT REVIEWER P0.7\n")
        f.write("# reviewer_build=P0.7_direct_evidence\n")
        f.write("# New RVA candidates only. Known/closed RVAs are excluded.\n")
        f.write("# Do not broad-scan around these targets.\n\n")
        for i, r in enumerate(ghidra_targets, 1):
            f.write(
                f"{i}\t{r['rva']}\tscore={r['aggregate_score']}"
                f"\tevidence={r['evidence_count']}"
                f"\tconsumer={r['consumer_score']}"
                f"\tbridge={r['bridge_score']}"
                f"\ttransform={r['transform_score']}\n"
            )

    evidence = {
        "schema": "csmc_full_snapshot_reviewer_p0_evidence_v3_direct_evidence",
        "inputs": [{"label": label, "path": str(path)} for label, path in inputs],
        "scanned_text_files": scanned_files,
        "skipped_large_files": skipped_large,
        "empty_or_undecodable_files": empty_decode,
        "targeted_hit_count": len(hits),
        "novel_evidence_count": len(novel_rows),
        "new_rva_candidate_count": len(candidate_rows),
        "ghidra_target_count": len(ghidra_targets),
        "category_counts": dict(category_counts),
        "top_candidates": candidate_rows[:20],
        "anti_loop": {
            "known_rvas_excluded_from_ghidra_targets": sorted(known_rvas),
            "known_facts_not_counted_as_new": known.get("do_not_count_as_new", []),
        },
        "semantic_promotion": False,
    }
    (out / "evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    lines = [
        "# CSMC FULL SNAPSHOT REVIEWER P0 — SUMMARY",
        "",
        "Targeted review of existing snapshot evidence; broad rediscovery is excluded.",
        "",
        "P0.7 direct-evidence extraction: only decompile owners or FUN_ tokens near the exact keyword hit can originate candidates; call_edges/functions/strings are corroboration only.",
        "",
        f"- Scanned text files: **{scanned_files}**",
        f"- Targeted evidence contexts: **{len(hits)}**",
        f"- Novel/high-value contexts: **{len(novel_rows)}**",
        f"- New RVA candidates: **{len(candidate_rows)}**",
        f"- Ghidra-targeted candidates: **{len(ghidra_targets)}**",
        "",
        "## Top new candidates",
        "",
    ]
    if candidate_rows:
        for r in candidate_rows[:10]:
            lines.append(
                f"- {r['rva']} — aggregate={r['aggregate_score']}, "
                f"evidence={r['evidence_count']}, snapshots={r['snapshot_count']}, "
                f"consumer={r['consumer_score']}, bridge={r['bridge_score']}, "
                f"transform={r['transform_score']}, direct_decompile={r['direct_decompile_count']}, "
                f"direct_near={r['direct_near_count']}"
            )
    else:
        lines.append("- No new RVA passed the current evidence threshold.")
    lines += [
        "",
        "## Anti-loop rule",
        "",
        "- SQLite / DATA2 header / generic ModelData / known VBO facts are not discoveries.",
        "- Known 0x140f... corridor RVAs are excluded from ghidra_targets.txt.",
        "- Extend a branch only when new function/RVA/object-construction evidence appears.",
        "",
        "## Next action",
        "",
        "If ghidra_targets.txt is non-empty, run a targeted Ghidra pass only for those RVAs.",
        "If it is empty, inspect novel_evidence.tsv before changing strategy.",
    ]
    (out / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (out / "TO_SEND_TO_CHATGPT.txt").write_text(
        "Preferred: upload CHATGPT_PACKET.md\n"
        "\nFallback individual files:\n"
        "  SUMMARY.md\n"
        "  consumer_candidates.tsv\n"
        "  novel_evidence.tsv\n"
        "  ghidra_targets.txt\n"
        "  evidence.json\n"
        "\nIf requested later:\n"
        "  targeted_hits.tsv\n"
        "  candidate_files.tsv\n",
        encoding="utf-8"
    )

    # One plain-text handoff file so ChatGPT does not need to unpack a ZIP.
    packet_parts = []
    packet_parts.append("# CSMC FULL SNAPSHOT REVIEWER P0 — CHATGPT PACKET\n")
    packet_parts.append("Generated from the local Windows reviewer. Original snapshot ZIPs are not included.\n")

    for title, filename in [
        ("SUMMARY", "SUMMARY.md"),
        ("GHIDRA TARGETS", "ghidra_targets.txt"),
        ("TOP CONSUMER CANDIDATES", "consumer_candidates.tsv"),
        ("NOVEL EVIDENCE", "novel_evidence.tsv"),
        ("EVIDENCE JSON", "evidence.json"),
    ]:
        p = out / filename
        packet_parts.append("\n\n--- " + title + " ---\n")
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            # Keep the handoff bounded even if a table becomes unexpectedly large.
            if len(text) > 350000:
                text = text[:350000] + "\n[TRUNCATED BY REVIEWER P0 PACKET LIMIT]\n"
            packet_parts.append(text)
        else:
            packet_parts.append("[MISSING] " + filename + "\n")

    (out / "CHATGPT_PACKET.md").write_text(
        "".join(packet_parts),
        encoding="utf-8"
    )

    print("SUMMARY=" + str(out / "SUMMARY.md"))
    print("CHATGPT_PACKET=" + str(out / "CHATGPT_PACKET.md"))
    print("NEW_RVA_CANDIDATES=" + str(len(candidate_rows)))
    print("GHIDRA_TARGETS=" + str(len(ghidra_targets)))

if __name__ == "__main__":
    main()
