"""Bounded local discovery for UKIE AI BRIDGE handoff destinations.

This module never crawls the whole disk and never claims cloud sync. It only checks
an explicit UKIE override plus common Google Drive for desktop mount/mirror layouts.
"""

from __future__ import annotations

import os
import string
from pathlib import Path
from typing import Iterable


def _unique_existing_directories(candidates: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for raw in candidates:
        try:
            path = raw.expanduser().resolve()
        except OSError:
            continue
        key = os.path.normcase(str(path))
        if key in seen or not path.is_dir():
            continue
        seen.add(key)
        result.append(path)
    return result


def drive_sync_candidates() -> list[Path]:
    candidates: list[Path] = []
    for env_name in ("UKIE_DRIVE_SYNC_ROOT", "GOOGLE_DRIVE"):
        value = os.environ.get(env_name)
        if value:
            candidates.append(Path(value))

    home = Path.home()
    candidates.extend([
        home / "Google Drive",
        home / "My Drive",
        home / "マイドライブ",
        home / "Documents" / "Google Drive",
    ])

    if os.name == "nt":
        for letter in string.ascii_uppercase[3:]:
            root = Path(f"{letter}:\\")
            candidates.extend([
                root / "My Drive",
                root / "マイドライブ",
                root / "Google Drive",
            ])

    return _unique_existing_directories(candidates)


def discover_drive_sync_root() -> dict:
    candidates = drive_sync_candidates()
    if not candidates:
        return {
            "status": "NOT_FOUND",
            "selected": None,
            "candidates": [],
            "confidence": "NONE",
        }

    override = os.environ.get("UKIE_DRIVE_SYNC_ROOT")
    if override:
        try:
            resolved = Path(override).expanduser().resolve()
            for candidate in candidates:
                if os.path.normcase(str(candidate)) == os.path.normcase(str(resolved)):
                    return {
                        "status": "FOUND",
                        "selected": str(candidate),
                        "candidates": [str(x) for x in candidates],
                        "confidence": "EXPLICIT_OVERRIDE",
                    }
        except OSError:
            pass

    preferred_names = {"my drive", "google drive", "マイドライブ"}
    ranked = sorted(
        candidates,
        key=lambda p: (0 if p.name.casefold() in preferred_names else 1, len(str(p)), str(p).casefold()),
    )
    return {
        "status": "FOUND",
        "selected": str(ranked[0]),
        "candidates": [str(x) for x in ranked],
        "confidence": "COMMON_LAYOUT",
    }
