"""Bounded serialization trigger candidate for the isolated CSMC canary.

This module is deliberately narrow:
- exactly one already-running CLIPStudioModeler.exe window must exist;
- no process launch, model load, path selection, dialog navigation, or cloud args;
- the only generated UI input is one fixed Ctrl+S chord (and Escape only to
  cancel an unexpected modal owned by the same MODELER process);
- the prior foreground window is restored on exit when possible;
- a title containing '*' is treated as a dirty-document signal and rejected;
- no registry/admin/service changes and no Production Worker mutation.

The action is a V4.4 *candidate*. Merely shipping this module does not add it to
the live canary allowlist or queue schema. Live invocation must remain gated by
separate CI/packaging/release promotion.
"""
from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ACTION_NAME = "csmc_modeler_save_no_change_v1"
TARGET_EXE = "CLIPStudioModeler.exe"
SETTLE_SECONDS = 1.25

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_ESCAPE = 0x1B
VK_S = 0x53


class CsmcModelerSaveTriggerError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ModelerWindow:
    hwnd: int
    pid: int
    title: str
    exe_name: str


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT)]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


class WinUiBackend:
    """Fixed Win32 surface; no caller-supplied command/path/key material."""

    def __init__(self) -> None:
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    def _pid_for_window(self, hwnd: int) -> int:
        pid = wintypes.DWORD(0)
        self.user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        return int(pid.value)

    def _exe_name(self, pid: int) -> str:
        handle = self.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return ""
        try:
            size = wintypes.DWORD(32768)
            buf = ctypes.create_unicode_buffer(size.value)
            if not self.kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return ""
            return Path(buf.value).name
        finally:
            self.kernel32.CloseHandle(handle)

    def _title(self, hwnd: int) -> str:
        length = int(self.user32.GetWindowTextLengthW(wintypes.HWND(hwnd)))
        buf = ctypes.create_unicode_buffer(max(2, length + 1))
        self.user32.GetWindowTextW(wintypes.HWND(hwnd), buf, len(buf))
        return buf.value

    def modeler_windows(self) -> list[ModelerWindow]:
        rows: list[ModelerWindow] = []
        enum_proc_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        @enum_proc_type
        def callback(hwnd: int, _lparam: int) -> bool:
            if not self.user32.IsWindowVisible(hwnd):
                return True
            pid = self._pid_for_window(hwnd)
            if pid <= 0:
                return True
            exe = self._exe_name(pid)
            if exe.lower() != TARGET_EXE.lower():
                return True
            title = self._title(hwnd)
            rows.append(ModelerWindow(int(hwnd), pid, title, exe))
            return True

        if not self.user32.EnumWindows(callback, 0):
            raise CsmcModelerSaveTriggerError("CSMC_SAVE_TRIGGER_ENUM_FAILED", "EnumWindows failed")
        return rows

    def foreground(self) -> int:
        return int(self.user32.GetForegroundWindow() or 0)

    def set_foreground(self, hwnd: int) -> bool:
        return bool(self.user32.SetForegroundWindow(wintypes.HWND(hwnd)))

    def pid_for_window(self, hwnd: int) -> int:
        return self._pid_for_window(hwnd)

    def _send_key(self, vk: int, *, keyup: bool) -> None:
        extra = ctypes.c_ulong(0)
        inp = _INPUT(type=INPUT_KEYBOARD)
        inp.ki = _KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP if keyup else 0, 0, ctypes.pointer(extra))
        sent = int(self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT)))
        if sent != 1:
            raise CsmcModelerSaveTriggerError("CSMC_SAVE_TRIGGER_SENDINPUT_FAILED", f"SendInput failed for VK={vk}")

    def send_ctrl_s(self) -> None:
        self._send_key(VK_CONTROL, keyup=False)
        try:
            self._send_key(VK_S, keyup=False)
            self._send_key(VK_S, keyup=True)
        finally:
            self._send_key(VK_CONTROL, keyup=True)

    def send_escape(self) -> None:
        self._send_key(VK_ESCAPE, keyup=False)
        self._send_key(VK_ESCAPE, keyup=True)


def _run_with_backend(backend: object, *, sleep_fn: Callable[[float], None] = time.sleep) -> dict[str, object]:
    windows = list(backend.modeler_windows())
    if len(windows) != 1:
        raise CsmcModelerSaveTriggerError(
            "CSMC_SAVE_TRIGGER_TARGET_AMBIGUOUS",
            f"expected exactly one visible {TARGET_EXE} window, got {len(windows)}",
        )
    target = windows[0]
    title = str(target.title or "")
    if not title:
        raise CsmcModelerSaveTriggerError("CSMC_SAVE_TRIGGER_TITLE_EMPTY", "MODELER window title is empty")
    if "*" in title:
        raise CsmcModelerSaveTriggerError(
            "CSMC_SAVE_TRIGGER_DIRTY_DOCUMENT_REJECTED",
            "MODELER title contains '*'; refusing to overwrite a potentially modified document",
        )

    previous = int(backend.foreground())
    focus_changed = previous != int(target.hwnd)
    chord_sent = False
    unexpected_modal_cancelled = False
    restore_attempted = False
    restore_succeeded = False
    started = time.monotonic()
    try:
        if focus_changed and not backend.set_foreground(int(target.hwnd)):
            raise CsmcModelerSaveTriggerError("CSMC_SAVE_TRIGGER_FOCUS_FAILED", "could not focus MODELER")
        sleep_fn(0.15)
        backend.send_ctrl_s()
        chord_sent = True
        sleep_fn(SETTLE_SECONDS)

        after = int(backend.foreground())
        if after not in (0, int(target.hwnd)) and int(backend.pid_for_window(after)) == int(target.pid):
            # Fail closed: do not navigate or confirm dialogs. Escape is the
            # only permitted recovery input and is scoped to a MODELER-owned
            # foreground window.
            backend.send_escape()
            unexpected_modal_cancelled = True
            raise CsmcModelerSaveTriggerError(
                "CSMC_SAVE_TRIGGER_MODAL_DETECTED",
                "MODELER opened an unexpected modal during fixed Ctrl+S; Escape sent and trigger rejected",
            )

        return {
            "schema_version": "csmc_modeler_save_trigger_result_v1",
            "action": ACTION_NAME,
            "status": "SAVE_TRIGGER_SENT",
            "target": TARGET_EXE,
            "target_pid": int(target.pid),
            "existing_modeler_session_used": True,
            "modeler_launch_performed": False,
            "model_load_performed": False,
            "cloud_parameters_accepted": False,
            "fixed_key_chord": "CTRL+S",
            "chord_sent": chord_sent,
            "dirty_title_guard_passed": True,
            "unexpected_modal_cancelled": unexpected_modal_cancelled,
            "focus_change_performed": focus_changed,
            "writes_current_document_possible": True,
            "production_worker_changed": False,
            "elapsed_seconds": max(0.0, time.monotonic() - started),
        }
    finally:
        if focus_changed and previous:
            restore_attempted = True
            try:
                restore_succeeded = bool(backend.set_foreground(previous))
            except Exception:
                restore_succeeded = False
        # Intentionally not returned on exceptions; callers log the failure
        # code. These locals exist so future telemetry can add restore status
        # without widening the action surface.
        _ = (restore_attempted, restore_succeeded)


def run_save_no_change() -> dict[str, object]:
    if os.name != "nt":
        raise CsmcModelerSaveTriggerError("CSMC_SAVE_TRIGGER_WINDOWS_ONLY", "fixed MODELER trigger requires Windows")
    return _run_with_backend(WinUiBackend())
