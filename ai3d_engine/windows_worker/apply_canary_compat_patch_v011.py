# SPDX-License-Identifier: MIT
"""Deterministic build-time patch for AI3D Windows Worker canary v0.1.1.

Keeps the cloud contract and action allowlist unchanged while adding:
- Blender 2.83 legacy EEVEE compatibility for the logical EEVEE_NEXT contract.
- compatible view-look fallback for pre-AgX Blender.
- --python-exit-code so Blender Python exceptions propagate to the worker.
- bounded stdout/stderr tail in worker error reporting.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKER = ROOT / "ai3d_worker.py"
BLENDER = ROOT / "blender_physical_mvp.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


worker = WORKER.read_text(encoding="utf-8")
worker = replace_once(
    worker,
    'WORKER_VERSION = "0.1.0-ai3d-canary"',
    'WORKER_VERSION = "0.1.1-ai3d-canary-compat"',
    "worker version",
)
worker = replace_once(
    worker,
    'def validate_result(job_dir: Path) -> tuple[dict[str, Any], Path]:\n',
    '''def _log_tail(path: Path, limit: int = 1800) -> str:\n    try:\n        if not path.is_file():\n            return ""\n        text = path.read_text(encoding="utf-8", errors="replace").strip()\n        return text[-limit:].replace("\\r", " ").replace("\\n", " | ")\n    except Exception:\n        return ""\n\n\ndef validate_result(job_dir: Path) -> tuple[dict[str, Any], Path]:\n''',
    "log tail helper",
)
worker = replace_once(
    worker,
    '        "--background",\n        "--python",',
    '        "--background",\n        "--python-exit-code",\n        "31",\n        "--python",',
    "python exit code",
)
worker = replace_once(
    worker,
    '        if proc.returncode != 0:\n            raise WorkerError(f"Blender exited with code {proc.returncode}")\n    heartbeat(credential, job)\n    return validate_result(job_dir)',
    '''        if proc.returncode != 0:\n            detail = _log_tail(stderr_path) or _log_tail(stdout_path)\n            suffix = f": {detail}" if detail else ""\n            raise WorkerError(f"Blender exited with code {proc.returncode}{suffix}")\n    heartbeat(credential, job)\n    try:\n        return validate_result(job_dir)\n    except WorkerError as exc:\n        detail = _log_tail(stderr_path) or _log_tail(stdout_path)\n        suffix = f"; blender_log_tail={detail}" if detail else ""\n        raise WorkerError(f"{exc}{suffix}") from exc''',
    "diagnostic propagation",
)
WORKER.write_text(worker, encoding="utf-8")

blender = BLENDER.read_text(encoding="utf-8")
blender = replace_once(
    blender,
    'def main() -> None:\n',
    '''def _select_render_engine(scene: bpy.types.Scene, logical_engine: str) -> str:\n    if logical_engine != "BLENDER_EEVEE_NEXT":\n        raise RuntimeError("logical render engine contract rejected")\n    try:\n        scene.render.engine = "BLENDER_EEVEE_NEXT"\n        return "BLENDER_EEVEE_NEXT"\n    except (TypeError, ValueError):\n        scene.render.engine = "BLENDER_EEVEE"\n        return "BLENDER_EEVEE"\n\n\ndef _set_compatible_view_look(scene: bpy.types.Scene) -> str:\n    for candidate in ("AgX - Medium High Contrast", "Medium High Contrast", "None"):\n        try:\n            scene.view_settings.look = candidate\n            return candidate\n        except (TypeError, ValueError):\n            continue\n    return str(scene.view_settings.look)\n\n\ndef main() -> None:\n''',
    "compat helpers",
)
blender = replace_once(
    blender,
    '    scene.render.engine = r["engine"]',
    '    actual_render_engine = _select_render_engine(scene, r["engine"])',
    "render engine compatibility",
)
blender = replace_once(
    blender,
    '    scene.view_settings.look = "AgX - Medium High Contrast"',
    '    actual_view_look = _set_compatible_view_look(scene)',
    "view look compatibility",
)
blender = blender.replace(
    'f"Blender {bpy.app.version_string} / EEVEE Next"',
    'f"Blender {bpy.app.version_string} / {actual_render_engine}"',
)
# Preserve the selected display look as diagnostic metadata without making it evidence.
blender = replace_once(
    blender,
    '            "height": r["height"],\n        },',
    '            "height": r["height"],\n            "view_look": actual_view_look,\n        },',
    "checkpoint view look",
)
BLENDER.write_text(blender, encoding="utf-8")

print("AI3D_CANARY_COMPAT_PATCH_V011=PASS")
