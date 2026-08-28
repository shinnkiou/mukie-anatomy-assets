from __future__ import annotations

import fnmatch
import hashlib
import os
import re
import time
import zipfile
from pathlib import Path
from typing import Iterable

_SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s]+)"),
    re.compile(r"(?i)((?:api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token|password)\s*[=:]\s*)([^\s'\"]+)"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def redact_secrets(text: str) -> str:
    out = text
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub(lambda m: m.group(1) + "<REDACTED_SECRET>", out)
    return out


def _depth_from(root: Path, path: Path) -> int:
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return 10**9


def bounded_find(
    roots: Iterable[Path],
    pattern: str,
    *,
    max_depth: int = 3,
    time_limit_seconds: float = 10.0,
    max_results: int = 200,
) -> list[Path]:
    """Bounded filename search. Does not recurse indefinitely."""
    started = time.monotonic()
    found: list[Path] = []
    seen: set[str] = set()

    for raw_root in roots:
        root = Path(raw_root).expanduser()
        if not root.exists() or not root.is_dir():
            continue
        root = root.resolve()
        for current, dirs, files in os.walk(root):
            if time.monotonic() - started > time_limit_seconds:
                return found
            current_path = Path(current)
            depth = _depth_from(root, current_path)
            if depth >= max_depth:
                dirs[:] = []
            for name in files:
                if fnmatch.fnmatch(name, pattern):
                    p = current_path / name
                    key = os.path.normcase(str(p.resolve()))
                    if key not in seen:
                        seen.add(key)
                        found.append(p)
                        if len(found) >= max_results:
                            return found
    return found


def validate_zip(path: Path, required_entries: Iterable[str] = ()) -> dict:
    result = {
        "path": str(path),
        "exists": path.exists(),
        "size": 0,
        "valid_zip": False,
        "crc_ok": False,
        "entry_count": 0,
        "missing_required": [],
    }
    if not path.exists() or not path.is_file():
        return result
    result["size"] = path.stat().st_size
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = set(zf.namelist())
            result["valid_zip"] = True
            result["entry_count"] = len(names)
            bad = zf.testzip()
            result["crc_ok"] = bad is None
            result["bad_entry"] = bad
            result["missing_required"] = [name for name in required_entries if name not in names]
    except (OSError, zipfile.BadZipFile) as exc:
        result["error"] = repr(exc)
    return result


def fresh_since(path: Path, epoch: float, tolerance_seconds: float = 1.0) -> bool:
    try:
        return path.exists() and path.stat().st_mtime >= epoch - tolerance_seconds
    except OSError:
        return False
