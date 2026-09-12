"""Pinned Blender discovery for UKIE AI BRIDGE P0.15.

Enumerates only bounded, known locations and selects the exact BP3D production
pin when available. Older/newer Blender installations are reported but never
silently substituted for the pinned production binary.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Iterable

PIN = "4.2.23"
_VERSION_RE = re.compile(r"^Blender\s+([0-9]+(?:\.[0-9]+){1,3})")


def portable_root(version: str = PIN) -> Path:
    local = os.environ.get("LOCALAPPDATA")
    base = Path(local) if local else (Path.home() / ".ukie_ai_bridge")
    return base / "UKIE_AI_BRIDGE" / "tools" / f"blender-{version}-windows-x64"


def _candidate_paths() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.environ.get("UKIE_BLENDER_EXE")
    if env_path:
        candidates.append(Path(env_path))

    candidates.append(portable_root() / "blender.exe")

    if os.name == "nt":
        for root_value in (os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
            if not root_value:
                continue
            base = Path(root_value)
            bf = base / "Blender Foundation"
            candidates.extend([
                bf / "Blender 4.2" / "blender.exe",
                bf / "Blender 4.2 LTS" / "blender.exe",
                bf / "Blender 4.2.23" / "blender.exe",
            ])
            if bf.is_dir():
                try:
                    for child in bf.iterdir():
                        candidates.append(child / "blender.exe")
                except OSError:
                    pass

    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def _probe(path: Path) -> dict:
    if not path.is_file():
        return {"exists": False, "path": str(path)}
    try:
        proc = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
        output = (proc.stdout or proc.stderr or "").strip().splitlines()
        first = output[0] if output else ""
        match = _VERSION_RE.match(first)
        version = match.group(1) if match else None
        return {
            "exists": True,
            "path": str(path),
            "return_code": proc.returncode,
            "version_line": first,
            "version": version,
            "usable": proc.returncode == 0 and bool(version),
            "is_pinned": version == PIN,
        }
    except Exception as exc:
        return {"exists": True, "path": str(path), "usable": False, "error": str(exc), "is_pinned": False}


def discover_blenders() -> dict:
    probed = [_probe(path) for path in _candidate_paths()]
    installed = [row for row in probed if row.get("exists")]
    usable = [row for row in installed if row.get("usable")]
    pinned = next((row for row in usable if row.get("is_pinned")), None)
    return {
        "schema_version": "ukie_blender_discovery_v1",
        "required_version": PIN,
        "status": "PINNED_FOUND" if pinned else ("OTHER_VERSIONS_ONLY" if usable else "NOT_FOUND"),
        "selected": pinned,
        "installed": usable,
        "examined_count": len(probed),
        "ready_for_bp3d": pinned is not None,
    }


def select_pinned_blender() -> dict:
    report = discover_blenders()
    selected = report.get("selected")
    if isinstance(selected, dict):
        return {
            "found": True,
            "path": selected["path"],
            "version_line": selected["version_line"],
            "version": selected["version"],
            "return_code": selected["return_code"],
            "selection_policy": "EXACT_BP3D_PIN",
            "alternatives": [row for row in report["installed"] if row.get("path") != selected.get("path")],
        }
    alternatives = report.get("installed") or []
    return {
        "found": False,
        "path": None,
        "error": f"Blender {PIN} not found in bounded allowlisted locations",
        "required_version": PIN,
        "selection_policy": "EXACT_BP3D_PIN",
        "alternatives": alternatives,
    }
