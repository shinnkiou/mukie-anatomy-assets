#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

RULES_PATH = Path(__file__).with_name("memory_rules_v1.json")
RULES = json.loads(RULES_PATH.read_text(encoding="utf-8"))
VERSION = f"memory-context-{RULES['version']}"
DEFAULT_MAX_DOCS = int(RULES.get("defaults", {}).get("max_docs", 8))
DEFAULT_CHAR_BUDGET = int(RULES.get("defaults", {}).get("char_budget", 24000))
TASK_RULES = RULES["task_rules"]
DOMAIN_RULES = RULES["domain_rules"]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _split_csv(value: Any) -> Set[str]:
    if not value:
        return set()
    if isinstance(value, list):
        return {str(x).strip() for x in value if str(x).strip()}
    return {x.strip() for x in str(value).split(",") if x.strip()}


def _canonicalize_source(term: str) -> str:
    cleaned = term.strip().strip("『』「」【】[]()（）\"'` ")
    if not cleaned:
        return ""
    aliases = RULES.get("source_exclusion", {}).get("source_aliases", {})
    for canonical, names in aliases.items():
        candidates = [canonical, *names]
        for alias in candidates:
            alias_norm = _norm(str(alias))
            if cleaned == alias_norm or alias_norm in cleaned:
                return str(canonical)
    return cleaned


def _source_exclusion_parse(text: str) -> Dict[str, Any]:
    cfg = RULES.get("source_exclusion", {})
    markers = sorted({_norm(str(x)) for x in cfg.get("markers", []) if str(x).strip()}, key=len, reverse=True)
    marker_hits: List[Tuple[int, str]] = []
    for marker in markers:
        start = 0
        while True:
            idx = text.find(marker, start)
            if idx < 0:
                break
            marker_hits.append((idx, marker))
            start = idx + max(1, len(marker))
    marker_hits.sort(key=lambda x: (x[0], -len(x[1])))
    if not marker_hits:
        return {"sources": [], "parse_status": "NONE", "clauses": [], "markers": []}

    generic = cfg.get("generic_clause_extraction", {})
    enabled = bool(generic.get("enabled", False))
    separators = str(generic.get("clause_separators", "。.!?！？\n;；"))
    qualifiers = [str(x) for x in generic.get("leading_qualifiers", ["ただし", "但し", "ただ", "なお"])]
    source_separators = sorted(
        [str(x) for x in generic.get("source_separators", ["および", "及び", "ならびに", "並びに", "と", "、", ",", "／", "/"]) if str(x)],
        key=len,
        reverse=True,
    )
    trailing_patterns = sorted(
        [str(x) for x in generic.get("trailing_context_patterns", []) if str(x)],
        key=len,
        reverse=True,
    )
    min_chars = int(generic.get("min_source_chars", 2))

    clauses: List[str] = []
    raw_terms: List[str] = []
    seen_hit_positions: Set[Tuple[int, int]] = set()
    for idx, marker in marker_hits:
        # Avoid duplicate parsing for overlapping markers such as 参照しない and 参照しないで.
        hit_span = (idx, idx + len(marker))
        if any(a == hit_span[0] and b >= hit_span[1] for a, b in seen_hit_positions):
            continue
        seen_hit_positions.add(hit_span)
        if not enabled:
            continue

        prefix = text[:idx]
        if separators:
            clause_parts = re.split(f"[{re.escape(separators)}]+", prefix)
            clause = clause_parts[-1].strip() if clause_parts else prefix.strip()
        else:
            clause = prefix.strip()

        # Remove discourse markers that are not part of the source name.
        changed = True
        while changed and clause:
            changed = False
            for qualifier in qualifiers:
                q = _norm(qualifier)
                if clause.startswith(q):
                    clause = clause[len(q):].lstrip(" 、,:：")
                    changed = True
                    break

        # Remove context words immediately before the exclusion marker.
        changed = True
        while changed and clause:
            changed = False
            for suffix in trailing_patterns:
                s = _norm(suffix)
                if clause.endswith(s):
                    clause = clause[: -len(s)].rstrip(" 、,:：")
                    changed = True
                    break

        clause = clause.strip().strip("『』「」【】[]()（）\"'` ")
        if not clause:
            continue
        clauses.append(clause)

        if source_separators:
            splitter = "(?:" + "|".join(re.escape(x) for x in source_separators) + ")"
            pieces = re.split(splitter, clause)
        else:
            pieces = [clause]
        for piece in pieces:
            term = piece.strip().strip("『』「」【】[]()（）\"'` ")
            if len(term) >= min_chars:
                raw_terms.append(term)

    sources: List[str] = []
    for term in raw_terms:
        canonical = _canonicalize_source(term)
        if canonical and canonical not in sources:
            sources.append(canonical)

    # If generic extraction could not resolve a name, do not silently downgrade the constraint.
    status = "RESOLVED" if sources else "UNRESOLVED"
    return {
        "sources": sorted(sources),
        "parse_status": status,
        "clauses": clauses,
        "markers": sorted({marker for _, marker in marker_hits}),
    }


def classify_task(instruction: str) -> Dict[str, Any]:
    text = _norm(instruction)
    scored: List[Tuple[int, str, List[str]]] = []
    for rule in TASK_RULES:
        hits = [kw for kw in rule["keywords"] if kw.lower() in text]
        if hits:
            score = len(hits) * int(rule["weight"])
            scored.append((score, rule["task_kind"], hits))

    if not scored:
        task_kind = "GENERAL"
        task_hits: List[str] = []
        confidence = 0.35
    else:
        scored.sort(reverse=True)
        _, task_kind, task_hits = scored[0]
        if task_kind == "RESEARCH_SUMMARY" and any(k in text for k in ["歴史", "変遷", "起源", "発展", "完成まで", "完成するまで", "紆余曲折", "開発史", "開発経緯", "成立まで", "系譜"]):
            task_kind = "HISTORICAL_RESEARCH"
        confidence = min(0.99, 0.60 + 0.08 * len(task_hits))

    domains: List[str] = []
    for domain, keywords in DOMAIN_RULES.items():
        if any(k.lower() in text for k in keywords):
            domains.append(domain)

    exclusion = _source_exclusion_parse(text)
    excluded_sources = exclusion["sources"]
    if exclusion["parse_status"] == "RESOLVED":
        constraint_mode = "EXPLICIT_SOURCE_EXCLUSION"
    elif exclusion["parse_status"] == "UNRESOLVED":
        constraint_mode = "EXPLICIT_SOURCE_EXCLUSION_UNRESOLVED"
    else:
        constraint_mode = "NONE"
    if exclusion["parse_status"] != "NONE":
        domains.append("source_exclusion")

    if task_kind in {"HISTORICAL_RESEARCH", "RESEARCH_SUMMARY"}:
        domains.append("research")
        if task_kind == "HISTORICAL_RESEARCH":
            domains.append("history")

    domains = sorted(set(domains))
    return {
        "classifier_version": VERSION,
        "rules_version": RULES["version"],
        "task_focus": instruction.strip(),
        "task_kind": task_kind,
        "domains": domains,
        "confidence": confidence,
        "matched_keywords": task_hits,
        "constraint_mode": constraint_mode,
        "excluded_sources": excluded_sources,
        "exclusion_parse_status": exclusion["parse_status"],
        "exclusion_clauses": exclusion["clauses"],
        "exclusion_markers": exclusion["markers"],
    }


def _relevance(doc: Dict[str, Any], task_kind: str, domains: Set[str], mission_key: str) -> Tuple[int, List[str]]:
    if doc.get("status") != "ACTIVE":
        return (-1, ["inactive"])
    policy = doc.get("load_policy", "WHEN_DOMAIN")
    reasons: List[str] = []
    score = 0

    if policy == "MANUAL_ONLY":
        return (-1, ["manual-only"])
    if policy == "ALWAYS":
        score += 10000
        reasons.append("ALWAYS")

    doc_mission = str(doc.get("mission_key") or "")
    if mission_key and doc_mission == mission_key:
        score += 9000
        reasons.append("mission-exact")
    elif policy == "WHEN_MISSION" and doc_mission:
        return (-1, ["other-mission"])

    task_kinds = _split_csv(doc.get("task_kinds"))
    if "ALL" in task_kinds:
        score += 500
        reasons.append("task-all")
    elif task_kind in task_kinds:
        score += 6000
        reasons.append("task-kind")
    elif policy == "WHEN_TASK_KIND":
        return (-1, ["task-mismatch"])

    doc_domains = _split_csv(doc.get("domains"))
    if "ALL" in doc_domains:
        score += 300
        reasons.append("domain-all")
    else:
        overlap = sorted(domains & doc_domains)
        if overlap:
            score += 2500 + 200 * len(overlap)
            reasons.append("domain:" + ",".join(overlap))
        elif policy == "WHEN_DOMAIN":
            return (-1, ["domain-mismatch"])

    priority = int(doc.get("priority", 50))
    score += max(0, 200 - priority)
    if doc.get("required"):
        score += 500
        reasons.append("required")
    return score, reasons


def select_context(
    instruction: str,
    catalog: Iterable[Dict[str, Any]],
    *,
    project_key: str = "project_relay",
    mission_key: str = "",
    max_docs: int = DEFAULT_MAX_DOCS,
    char_budget: int = DEFAULT_CHAR_BUDGET,
) -> Dict[str, Any]:
    task = classify_task(instruction)
    domains = set(task["domains"])
    candidates: List[Tuple[int, Dict[str, Any], List[str]]] = []
    excluded: List[Dict[str, str]] = []

    for doc in catalog:
        if doc.get("project_key") not in {project_key, "*"}:
            excluded.append({"memory_key": doc.get("memory_key", "?"), "reason": "project-mismatch"})
            continue
        score, reasons = _relevance(doc, task["task_kind"], domains, mission_key)
        if score < 0:
            excluded.append({"memory_key": doc.get("memory_key", "?"), "reason": ";".join(reasons)})
            continue
        candidates.append((score, doc, reasons))

    candidates.sort(key=lambda x: (-x[0], int(x[1].get("priority", 50)), x[1].get("memory_key", "")))
    selected: List[Dict[str, Any]] = []
    used_chars = 0
    for score, doc, reasons in candidates:
        if len(selected) >= max_docs:
            excluded.append({"memory_key": doc["memory_key"], "reason": "max-docs-budget"})
            continue
        size = int(doc.get("estimated_chars") or 0)
        if selected and used_chars + size > char_budget:
            excluded.append({"memory_key": doc["memory_key"], "reason": "char-budget"})
            continue
        selected.append({
            "memory_key": doc["memory_key"],
            "title": doc.get("title", ""),
            "drive_file_id": doc.get("drive_file_id", ""),
            "drive_file_url": doc.get("drive_file_url", ""),
            "estimated_chars": size,
            "score": score,
            "reasons": reasons,
        })
        used_chars += size

    selected_keys = [d["memory_key"] for d in selected]
    return {
        **task,
        "project_key": project_key,
        "mission_key": mission_key,
        "max_docs": max_docs,
        "char_budget": char_budget,
        "selected_doc_count": len(selected),
        "estimated_chars": used_chars,
        "selected": selected,
        "selected_memory_keys": selected_keys,
        "excluded": excluded,
        "status": "SELECTED",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("instruction")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--mission-key", default="")
    ap.add_argument("--project-key", default="project_relay")
    ap.add_argument("--max-docs", type=int, default=DEFAULT_MAX_DOCS)
    ap.add_argument("--char-budget", type=int, default=DEFAULT_CHAR_BUDGET)
    ap.add_argument("--out")
    args = ap.parse_args()
    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    result = select_context(
        args.instruction,
        catalog,
        mission_key=args.mission_key,
        project_key=args.project_key,
        max_docs=args.max_docs,
        char_budget=args.char_budget,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
