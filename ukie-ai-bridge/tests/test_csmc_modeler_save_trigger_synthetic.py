from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge.csmc_modeler_save_trigger_action import (
    CsmcModelerSaveTriggerError,
    ModelerWindow,
    _run_with_backend,
)


class FakeBackend:
    def __init__(self, *, title="Target Model - CLIP STUDIO MODELER", windows=1, previous=99, modal=False):
        self.target = ModelerWindow(hwnd=10, pid=1234, title=title, exe_name="CLIPStudioModeler.exe")
        self.window_count = windows
        self.previous = previous
        self.current = previous
        self.modal = modal
        self.ctrl_s_count = 0
        self.escape_count = 0
        self.focus_calls = []

    def modeler_windows(self):
        if self.window_count == 0:
            return []
        if self.window_count == 1:
            return [self.target]
        return [self.target, ModelerWindow(hwnd=11, pid=5678, title="Other", exe_name="CLIPStudioModeler.exe")]

    def foreground(self):
        if self.modal and self.ctrl_s_count:
            return 20
        return self.current

    def set_foreground(self, hwnd):
        self.focus_calls.append(hwnd)
        self.current = hwnd
        return True

    def pid_for_window(self, hwnd):
        return self.target.pid if hwnd in (10, 20) else 9999

    def send_ctrl_s(self):
        self.ctrl_s_count += 1
        self.current = 10

    def send_escape(self):
        self.escape_count += 1


def no_sleep(_seconds):
    return None


def expect_code(fn, code):
    try:
        fn()
    except CsmcModelerSaveTriggerError as exc:
        assert exc.code == code, (exc.code, code)
        return
    raise AssertionError(f"expected {code}")


def test_success_restores_foreground():
    b = FakeBackend()
    out = _run_with_backend(b, sleep_fn=no_sleep)
    assert out["status"] == "SAVE_TRIGGER_SENT"
    assert out["fixed_key_chord"] == "CTRL+S"
    assert out["cloud_parameters_accepted"] is False
    assert out["existing_modeler_session_used"] is True
    assert out["modeler_launch_performed"] is False
    assert out["model_load_performed"] is False
    assert out["writes_current_document_possible"] is True
    assert b.ctrl_s_count == 1
    assert b.escape_count == 0
    assert b.focus_calls == [10, 99]


def test_already_foreground_needs_no_focus_change():
    b = FakeBackend(previous=10)
    out = _run_with_backend(b, sleep_fn=no_sleep)
    assert out["focus_change_performed"] is False
    assert b.focus_calls == []
    assert b.ctrl_s_count == 1


def test_dirty_title_rejected_before_input():
    b = FakeBackend(title="*Target Model - CLIP STUDIO MODELER")
    expect_code(lambda: _run_with_backend(b, sleep_fn=no_sleep), "CSMC_SAVE_TRIGGER_DIRTY_DOCUMENT_REJECTED")
    assert b.ctrl_s_count == 0


def test_ambiguous_target_rejected_before_input():
    b = FakeBackend(windows=2)
    expect_code(lambda: _run_with_backend(b, sleep_fn=no_sleep), "CSMC_SAVE_TRIGGER_TARGET_AMBIGUOUS")
    assert b.ctrl_s_count == 0


def test_modal_is_cancelled_and_previous_foreground_restored():
    b = FakeBackend(modal=True)
    expect_code(lambda: _run_with_backend(b, sleep_fn=no_sleep), "CSMC_SAVE_TRIGGER_MODAL_DETECTED")
    assert b.ctrl_s_count == 1
    assert b.escape_count == 1
    assert b.focus_calls[-1] == 99


if __name__ == "__main__":
    test_success_restores_foreground()
    test_already_foreground_needs_no_focus_change()
    test_dirty_title_rejected_before_input()
    test_ambiguous_target_rejected_before_input()
    test_modal_is_cancelled_and_previous_foreground_restored()
    print("CSMC MODELER save trigger synthetic tests PASS")
