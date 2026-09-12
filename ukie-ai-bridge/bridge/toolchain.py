"""Bounded, non-recursive toolchain discovery for UKIE AI BRIDGE.

This module never scans an entire drive and never installs anything. It checks
PATH plus a small set of known Windows locations. Discovery records are evidence
for the Toolchain Resolver, not permission to execute arbitrary software.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ToolSpec:
    tool_key: str
    commands: tuple[str, ...]
    relative_candidates: tuple[str, ...]


TOOL_SPECS = (
    ToolSpec(
        "blender_bp3d_4_2_23",
        ("blender.exe", "blender"),
        (
            r"Blender Foundation\Blender 4.2\blender.exe",
            r"Blender Foundation\Blender 4.2 LTS\blender.exe",
        ),
    ),
    ToolSpec("python_research", ("python.exe", "python3.exe", "python"), (r"Python312\python.exe", r"Python313\python.exe")),
    ToolSpec("git", ("git.exe", "git"), (r"Git\cmd\git.exe", r"Git\bin\git.exe")),
    ToolSpec("sevenzip", ("7z.exe", "7z"), (r"7-Zip\7z.exe",)),
    ToolSpec("everything", ("Everything.exe",), (r"Everything\Everything.exe",)),
    ToolSpec("ffmpeg", ("ffmpeg.exe", "ffmpeg"), (r"ffmpeg\bin\ffmpeg.exe",)),
    ToolSpec("sqlite_tools", ("sqlite3.exe", "sqlite3"), (r"SQLite\sqlite3.exe",)),
    ToolSpec("x64dbg", ("x64dbg.exe",), (r"x64dbg\release\x64\x64dbg.exe", r"x64dbg\x64dbg.exe")),
    ToolSpec("ghidra", ("ghidraRun.bat", "ghidraRun"), (r"ghidra\ghidraRun.bat",)),
    ToolSpec("sysinternals", ("procmon.exe", "Procmon.exe"), (r"SysinternalsSuite\Procmon.exe", r"Sysinternals\Procmon.exe")),
    ToolSpec("renderdoc", ("qrenderdoc.exe",), (r"RenderDoc\qrenderdoc.exe",)),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _windows_roots() -> list[Path]:
    names = ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA", "USERPROFILE")
    roots: list[Path] = []
    seen: set[str] = set()
    for name in names:
        raw = os.environ.get(name)
        if not raw:
            continue
        path = Path(raw)
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            roots.append(path)

    research_root = os.environ.get("UKIE_RESEARCH_DRIVE")
    if research_root:
        root = Path(research_root)
        key = str(root).lower()
        if key not in seen:
            roots.append(root)
    return roots


def _candidate_paths(spec: ToolSpec) -> Iterable[Path]:
    # PATH resolution first. shutil.which does not recursively search a drive.
    for command in spec.commands:
        found = shutil.which(command)
        if found:
            yield Path(found)

    for root in _windows_roots():
        for relative in spec.relative_candidates:
            yield root / relative

        # Research-drive convention: <root>/01_SOFTWARE/<tool_key>/...
        software = root / "01_SOFTWARE" / spec.tool_key
        if software.is_dir():
            try:
                # Bounded depth: direct children and one nested directory only.
                for child in software.iterdir():
                    if child.is_file() and child.name.lower() in {c.lower() for c in spec.commands}:
                        yield child
                    elif child.is_dir():
                        for command in spec.commands:
                            candidate = child / command
                            if candidate.is_file():
                                yield candidate
            except OSError:
                pass


def discover_tool(spec: ToolSpec, include_hash: bool = False) -> dict:
    seen: set[str] = set()
    for candidate in _candidate_paths(spec):
        try:
            resolved = candidate.expanduser().resolve(strict=False)
        except OSError:
            resolved = candidate
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            if not resolved.is_file():
                continue
            stat = resolved.stat()
            result = {
                "tool_key": spec.tool_key,
                "status": "FOUND",
                "path": str(resolved),
                "byte_size": int(stat.st_size),
                "modified_ns": int(stat.st_mtime_ns),
            }
            if include_hash:
                result["sha256"] = sha256_file(resolved)
            return result
        except (OSError, PermissionError) as exc:
            return {
                "tool_key": spec.tool_key,
                "status": "ERROR",
                "path": str(resolved),
                "error": str(exc),
            }
    return {"tool_key": spec.tool_key, "status": "NOT_FOUND", "path": None}


def discover_toolchain(include_hash: bool = False) -> dict:
    tools = [discover_tool(spec, include_hash=include_hash) for spec in TOOL_SPECS]
    return {
        "schema_version": "ukie_tool_discovery_v1",
        "generated_at": utc_now(),
        "strategy": "PATH_AND_KNOWN_LOCATIONS_ONLY",
        "recursive_drive_scan": False,
        "include_hash": include_hash,
        "tools": tools,
        "summary": {
            "found": sum(1 for t in tools if t["status"] == "FOUND"),
            "not_found": sum(1 for t in tools if t["status"] == "NOT_FOUND"),
            "error": sum(1 for t in tools if t["status"] == "ERROR"),
        },
    }
