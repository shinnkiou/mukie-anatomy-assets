"""Deterministic build-time patch for CSMC canary V4.2.

Exactly one Observer behavior changes relative to V4.1: when ReadProcessMemory
returns ERROR_PARTIAL_COPY (or another false return) but reports non-zero
lpNumberOfBytesRead, the diagnostic scanner preserves/scans only those returned
bytes instead of discarding them. The scan region/type plan and every CELSYS
header predicate remain unchanged. No payload dump, process write, UI action, or
network surface is added.

This patch also exposes returned_bytes in diagnostic failure metadata so the
result can prove whether salvage actually occurred.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PS1 = ROOT / "BP3D_ModelerObserver_P4_1_DIAG_V1.ps1"
ACTION = ROOT / "bridge" / "csmc_observer_diagnose_action.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence, got {count}")
    return text.replace(old, new, 1)


def patch_ps1() -> None:
    text = PS1.read_text(encoding="utf-8-sig")
    text = replace_once(
        text,
        'public ulong RegionBase,RegionSize,Offset; public uint Protect,Type; public int RequestedBytes,Win32Error; public string TypeName;',
        'public ulong RegionBase,RegionSize,Offset; public uint Protect,Type; public int RequestedBytes,ReturnedBytes,Win32Error; public string TypeName;',
        "ReadFailure.ReturnedBytes",
    )
    old_read = 'bool ok=ReadProcessMemory(hp,new IntPtr(unchecked((long)(rb+off))),buf,new UIntPtr((uint)want),out g);int n=ok?(int)Math.Min((ulong)want,g.ToUInt64()):0;attempted+=(ulong)want;'
    new_read = 'bool ok=ReadProcessMemory(hp,new IntPtr(unchecked((long)(rb+off))),buf,new UIntPtr((uint)want),out g);ulong got=g.ToUInt64();int n=(int)Math.Min((ulong)want,got);attempted+=(ulong)want;if(!ok){fail++;if(failures.Count<MAX_FAILURE_DETAILS){failures.Add(new ReadFailure{RegionBase=rb,RegionSize=sz,Offset=off,Protect=m.Protect,Type=m.Type,TypeName=TN(m.Type),RequestedBytes=want,ReturnedBytes=n,Win32Error=Marshal.GetLastWin32Error()});}}'
    text = replace_once(text, old_read, new_read, "partial-copy read handling")
    old_else = 'else{fail++;if(failures.Count<MAX_FAILURE_DETAILS){failures.Add(new ReadFailure{RegionBase=rb,RegionSize=sz,Offset=off,Protect=m.Protect,Type=m.Type,TypeName=TN(m.Type),RequestedBytes=want,Win32Error=Marshal.GetLastWin32Error()});}carry=0;}'
    text = replace_once(text, old_else, 'else{carry=0;}', "legacy failed-read discard")
    old_row = "requested_bytes=$f.RequestedBytes;win32_error=$f.Win32Error"
    new_row = "requested_bytes=$f.RequestedBytes;returned_bytes=$f.ReturnedBytes;win32_error=$f.Win32Error"
    text = replace_once(text, old_row, new_row, "failure metadata")
    text = replace_once(text, "$ToolVersion='P4.1.1-diagnose-v1'", "$ToolVersion='P4.2.0-diagnose-partial-copy-salvage'", "tool version")
    text = replace_once(
        text,
        "scan_algorithm='P4.1 unchanged all-readable committed memory scan'",
        "scan_algorithm='P4.2 same all-readable committed scan; salvage nonzero bytes returned on failed ReadProcessMemory'",
        "scan algorithm label",
    )
    PS1.write_text(text, encoding="utf-8")


def patch_action() -> None:
    text = ACTION.read_text(encoding="utf-8")
    old = '("region_base", "region_size", "offset", "type", "type_raw", "protect", "requested_bytes", "win32_error")'
    new = '("region_base", "region_size", "offset", "type", "type_raw", "protect", "requested_bytes", "returned_bytes", "win32_error")'
    text = replace_once(text, old, new, "temporal returned_bytes propagation")
    text = replace_once(
        text,
        '"observer_change": "bounded_temporal_resampling_same_predicates",',
        '"observer_change": "error_partial_copy_returned_bytes_salvage_only",',
        "aggregate observer change",
    )
    # The manifest contains the same literal a second time after the aggregate
    # replacement above; replace exactly that remaining occurrence.
    text = replace_once(
        text,
        '"observer_change": "bounded_temporal_resampling_same_predicates",',
        '"observer_change": "error_partial_copy_returned_bytes_salvage_only",',
        "manifest observer change",
    )
    ACTION.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_ps1()
    patch_action()
    print("CSMC V4.2 partial-copy salvage patch applied")
