#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse

RULES_PATH = Path(__file__).with_name("memory_rules_v1.json")
RULES = json.loads(RULES_PATH.read_text(encoding="utf-8"))
VERSION = "source-exclusion-filter-v1.0"


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _aliases_for(canonical: str) -> list[str]:
    cfg = RULES.get("source_exclusion", {}).get("source_aliases", {})
    aliases = [canonical]
    aliases.extend(cfg.get(canonical, []))
    return sorted({_norm(x) for x in aliases if _norm(x)}, key=len, reverse=True)


def classify_candidate(candidate: Dict[str, Any], excluded_sources: Iterable[str]) -> Dict[str, Any]:
    """Conservatively classify one candidate before content ingestion.

    The candidate may contain url/title/source_name/source_family. URL and an explicit
    source_family are strongest signals. A title hit is also blocked because exclusion
    constraints favor false-negative prevention over recall; callers can route a blocked
    candidate to human review if it is important.
    """
    url = _norm(candidate.get("url"))
    title = _norm(candidate.get("title"))
    source_name = _norm(candidate.get("source_name"))
    source_family = _norm(candidate.get("source_family"))
    parsed_host = _norm(urlparse(candidate.get("url") or "").netloc)

    matched: List[Dict[str, str]] = []
    for canonical in excluded_sources:
        for alias in _aliases_for(str(canonical)):
            if not alias:
                continue
            # URL/path/host and explicit source-family are strongest.
            if alias.replace(" ", "-") in url or alias.replace(" ", "") in url or alias in url:
                matched.append({"source": str(canonical), "signal": "url", "alias": alias})
                break
            if alias in source_family:
                matched.append({"source": str(canonical), "signal": "source_family", "alias": alias})
                break
            if alias in source_name:
                matched.append({"source": str(canonical), "signal": "source_name", "alias": alias})
                break
            if alias in title:
                matched.append({"source": str(canonical), "signal": "title", "alias": alias})
                break

        # Domain-family shortcut for the current canonical source. Keep these mappings
        # explicit and auditable rather than using fuzzy web heuristics.
        if str(canonical) == "ジ・オリジン" and parsed_host in {"gundam-the-origin.net", "www.gundam-the-origin.net"}:
            if not any(m["source"] == canonical for m in matched):
                matched.append({"source": str(canonical), "signal": "host-family", "alias": parsed_host})

    blocked = bool(matched)
    return {
        **candidate,
        "filter_version": VERSION,
        "decision": "SOURCE_FILTERED" if blocked else "ALLOW",
        "blocked": blocked,
        "matched_exclusions": matched,
    }


def filter_candidates(candidates: Iterable[Dict[str, Any]], excluded_sources: Iterable[str]) -> Dict[str, Any]:
    reviewed = [classify_candidate(c, excluded_sources) for c in candidates]
    allowed = [x for x in reviewed if not x["blocked"]]
    blocked = [x for x in reviewed if x["blocked"]]
    return {
        "filter_version": VERSION,
        "excluded_sources": list(excluded_sources),
        "candidate_count": len(reviewed),
        "allowed_count": len(allowed),
        "blocked_count": len(blocked),
        "allowed": allowed,
        "blocked": blocked,
    }


def validate_adopted_sources(adopted: Iterable[Dict[str, Any]], excluded_sources: Iterable[str]) -> Dict[str, Any]:
    audit = filter_candidates(adopted, excluded_sources)
    valid = audit["blocked_count"] == 0
    return {
        "valid": valid,
        "result": "PASS" if valid else "FAIL_EXCLUDED_SOURCE_ADOPTED",
        "adopted_count": audit["candidate_count"],
        "excluded_adopted_count": audit["blocked_count"],
        "blocked": audit["blocked"],
        "filter_version": VERSION,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="JSON array of candidate source objects")
    ap.add_argument("--exclude", action="append", default=[])
    args = ap.parse_args()
    candidates = json.loads(Path(args.input).read_text(encoding="utf-8"))
    print(json.dumps(filter_candidates(candidates, args.exclude), ensure_ascii=False, indent=2))
