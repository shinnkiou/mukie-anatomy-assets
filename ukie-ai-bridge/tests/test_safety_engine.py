import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

from bridge.artifact_validation import analyze_only_contract, validate_artifact_contract
from bridge.known_failures import (
    classify_debugger_line,
    classify_memory_hit,
    validate_batch_bytes,
    validate_target_identity,
)
from bridge.preflight import check_input, inspect_python_script, run_foundation_preflight


class KnownFailureTests(unittest.TestCase):
    def test_cpp_exception_is_known_noise(self):
        match = classify_debugger_line("first chance exception E06D7363")
        self.assertIsNotNone(match)
        self.assertEqual(match.status, "NOISE")
        self.assertEqual(match.error_code, "NOISE_X64_CPP_FIRST_CHANCE")

    def test_self_attach_is_rejected(self):
        result = validate_target_identity(
            observer_pid=42,
            target_pid=42,
            target_exe_name="CLIPStudioModeler.exe",
            target_path=r"C:\\Program Files\\CELSYS\\CLIPStudioModeler.exe",
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("ERROR_X64_001", result["error_codes"])

    def test_loose_target_name_is_rejected(self):
        result = validate_target_identity(
            observer_pid=1,
            target_pid=2,
            target_exe_name="my_modeler_observer.exe",
            target_path=r"C:\\Tools\\my_modeler_observer.exe",
        )
        self.assertEqual(result["status"], "FAIL")

    def test_batch_bom_and_non_ascii_rejected(self):
        result = validate_batch_bytes(b"\xef\xbb\xbf@echo off\r\n\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e\r\n")
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("ERROR_CMD_001", result["error_codes"])

    def test_static_mem_image_is_not_confirmed(self):
        result = classify_memory_hit(memory_type="MEM_IMAGE", writable=False, changed_across_phases=False)
        self.assertFalse(result["confirmed"])
        self.assertEqual(result["error_code"], "ERROR_X64_002")


class PreflightTests(unittest.TestCase):
    def test_unicode_input_is_hashable_and_staged_ascii(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "大学用女性data.blend"
            p.write_bytes(b"x" * 256)
            result = check_input(p)
            self.assertEqual(result.status, "PASS")
            self.assertTrue(result.auto_fixed)
            self.assertEqual(result.observed["staging_basename"], "input.blend")

    def test_script_guard_rejects_subprocess(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "bad.py"
            p.write_text("import subprocess\nsubprocess.run(['cmd'])\n", encoding="utf-8")
            result = inspect_python_script(p, mode="ANALYZE_ONLY")
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("subprocess", result["dangerous_imports"])

    def test_script_guard_rejects_blender_save_in_analyze_only(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "bad_blender.py"
            p.write_text("import bpy\nbpy.ops.wm.save_as_mainfile(filepath='x.blend')\n", encoding="utf-8")
            result = inspect_python_script(p, mode="ANALYZE_ONLY")
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("bpy.ops.wm.save_as_mainfile", result["dangerous_calls"])

    def test_foundation_preflight_passes_safe_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            input_file = root / "入力.blend"
            input_file.write_bytes(b"a" * 256)
            script = root / "safe.py"
            script.write_text("import json\nprint(json.dumps({'ok': True}))\n", encoding="utf-8")
            report = run_foundation_preflight(
                workspace=root / "workspace",
                input_file=input_file,
                script_file=script,
                python_role="BLENDER_INTERNAL",
            )
            self.assertEqual(report["status"], "PASS")


class ArtifactValidationTests(unittest.TestCase):
    def test_empty_artifact_fails_even_if_files_exist(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            for name in ("scene_before.json", "stdout.log", "working.blend", "input.blend"):
                (root / name).write_bytes(b"")
            result = validate_artifact_contract(root, analyze_only_contract())
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["error_code"], "ERROR_ARTIFACT_001")

    def test_analyze_contract_passes_semantic_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            scene = {
                "schema_version": "ukie_scene_report_v1",
                "mode": "ANALYZE_ONLY",
                "blender_version": "4.2.23",
                "python_version": "3.11",
                "objects": [],
            }
            (root / "scene_before.json").write_text(json.dumps(scene), encoding="utf-8")
            (root / "stdout.log").write_text("UKIE_ANALYZE_OK\n", encoding="utf-8")
            (root / "working.blend").write_bytes(b"B" * 128)
            (root / "input.blend").write_bytes(b"B" * 128)
            result = validate_artifact_contract(root, analyze_only_contract())
            self.assertEqual(result["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
