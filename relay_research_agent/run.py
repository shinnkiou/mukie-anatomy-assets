#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.json"
RESULTS = ROOT / "results"
HISTORY = RESULTS / "history"
LATEST = RESULTS / "latest.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def search_web(query: str, max_results: int = 8) -> Dict[str, Any]:
    errors: List[str] = []
    rows: List[Dict[str, str]] = []
    try:
        try:
            from ddgs import DDGS  # type: ignore
        except Exception:
            from duckduckgo_search import DDGS  # type: ignore
        with DDGS() as ddgs:
            for item in ddgs.text(query, region="jp-jp", safesearch="moderate", max_results=max_results):
                href = str(item.get("href") or item.get("url") or "")
                title = clean_text(str(item.get("title") or ""))
                body = clean_text(str(item.get("body") or item.get("snippet") or ""))
                if href:
                    rows.append({"title": title, "url": href, "snippet": body})
    except Exception as exc:
        errors.append(f"DDGS search failed: {type(exc).__name__}: {exc}")
    return {"query": query, "results": rows, "errors": errors}


def monitor_page(url: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"url": url, "checked_at": now_iso()}
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "PROJECT-RELAY-Research-Agent/1.0 (+public-info-only)"})
        out["status_code"] = r.status_code
        out["final_url"] = r.url
        out["content_bytes"] = len(r.content)
        out["sha256"] = hashlib.sha256(r.content).hexdigest()
        ctype = r.headers.get("content-type", "")
        out["content_type"] = ctype
        if "text/html" in ctype or "text/plain" in ctype or not ctype:
            text = r.text
            soup = BeautifulSoup(text, "html.parser")
            out["title"] = clean_text(soup.title.get_text(" ") if soup.title else "")[:300]
            body = clean_text(soup.get_text(" "))
            out["text_sample"] = body[:4000]
            for needle in ["ドラム", "電子ドラム", "V-Drums", "女性", "体験", "単発", "個人練習", "レンタル", "9/2", "9/3", "9/4", "9/5"]:
                out.setdefault("keyword_hits", {})[needle] = body.lower().count(needle.lower())
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def candidate_score(row: Dict[str, str]) -> int:
    text = (row.get("title", "") + " " + row.get("snippet", "") + " " + row.get("url", "")).lower()
    score = 0
    weights = {
        "豊橋": 4,
        "ドラム": 4,
        "電子ドラム": 8,
        "v-drums": 8,
        "レンタル": 5,
        "マンツーマン": 5,
        "個人": 2,
        "単発": 6,
        "1回": 3,
        "入会不要": 6,
        "女性": 5,
        "講師": 3,
        "体験": 2,
        "当日": 4,
    }
    for key, val in weights.items():
        if key in text:
            score += val
    return score


def main() -> int:
    cfg = load_json(CONFIG, {})
    RESULTS.mkdir(parents=True, exist_ok=True)
    HISTORY.mkdir(parents=True, exist_ok=True)
    previous = load_json(LATEST, {})

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report: Dict[str, Any] = {
        "schema_version": "relay-research-result-v1",
        "run_id": run_id,
        "mission_key": cfg.get("mission_key"),
        "started_at": now_iso(),
        "status": "RUNNING",
        "enabled": bool(cfg.get("enabled", False)),
        "worker": "github-actions",
        "safety": cfg.get("safety", {}),
        "searches": [],
        "monitors": [],
        "errors": [],
        "new_urls": [],
        "top_candidates": [],
    }

    if not report["enabled"]:
        report["status"] = "STOPPED"
        report["finished_at"] = now_iso()
        LATEST.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (HISTORY / f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    all_rows: List[Dict[str, str]] = []
    for query in cfg.get("queries", []):
        result = search_web(str(query))
        report["searches"].append(result)
        report["errors"].extend(result.get("errors", []))
        all_rows.extend(result.get("results", []))
        time.sleep(0.6)

    for url in cfg.get("monitor_urls", []):
        report["monitors"].append(monitor_page(str(url)))

    dedup: Dict[str, Dict[str, str]] = {}
    for row in all_rows:
        url = row.get("url", "")
        if url and url not in dedup:
            row = dict(row)
            row["score"] = candidate_score(row)  # type: ignore[index]
            dedup[url] = row

    ranked = sorted(dedup.values(), key=lambda r: int(r.get("score", 0)), reverse=True)
    report["top_candidates"] = ranked[:30]

    old_urls = set()
    for search in previous.get("searches", []) if isinstance(previous, dict) else []:
        for row in search.get("results", []):
            if row.get("url"):
                old_urls.add(row["url"])
    report["new_urls"] = [r["url"] for r in ranked if r.get("url") and r["url"] not in old_urls][:30]

    joined = " ".join((r.get("title", "") + " " + r.get("snippet", "")) for r in ranked).lower()
    report["unresolved"] = []
    if not any(k in joined for k in ["電子ドラム レンタル", "v-drums レンタル", "v-drums rental"]):
        report["unresolved"].append("electronic_drum_takehome_rental_not_confirmed")
    report["unresolved"].append("live_same_day_availability_requires_provider_confirmation")
    report["unresolved"].append("female_instructor_exact_slot_requires_provider_confirmation")

    report["status"] = "PARTIAL" if report["unresolved"] or report["errors"] else "SUCCESS"
    report["finished_at"] = now_iso()
    report["summary"] = {
        "queries": len(report["searches"]),
        "unique_urls": len(ranked),
        "new_urls": len(report["new_urls"]),
        "monitor_pages": len(report["monitors"]),
        "errors": len(report["errors"]),
    }

    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    LATEST.write_text(payload, encoding="utf-8")
    (HISTORY / f"{run_id}.json").write_text(payload, encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
