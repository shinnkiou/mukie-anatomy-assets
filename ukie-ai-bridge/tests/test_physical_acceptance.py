import pathlib
import tempfile
import unittest
from unittest import mock

from bridge import physical_acceptance as pa


DEVICE = {
    "schema_version": "ukie_device_status_v1",
    "platform": {"system": "Windows", "machine": "AMD64"},
    "memory": {"supported": True, "total_bytes": 16 * 1024**3},
    "blender": {"found": True, "version_line": "Blender 4.2.23 LTS", "path": "C:/Blender/blender.exe"},
}


class PhysicalAcceptanceTests(unittest.TestCase):
    def test_core_pass_gpu_blocked_is_preserved_as_partial_capability_result(self):
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(pa.bridge_main, "device_status", return_value=DEVICE), \
                 mock.patch.object(pa, "run_blender_canary", return_value={"status": "CANARY_LOCAL_PASS"}), \
                 mock.patch.object(pa, "run_gpu_probe", side_effect=pa.GPUProbeError("no non-CPU device")):
                result = pa.run_physical_acceptance(pathlib.Path(temp))

            self.assertEqual(result["status"], "CORE_PASS_GPU_BLOCKED")
            self.assertTrue(result["local_core_ready"])
            self.assertFalse(result["local_gpu_render_ready"])
            self.assertFalse(result["ready_for_ai"])
            self.assertFalse(result["upload_performed"])
            self.assertTrue(pathlib.Path(result["acceptance_bundle"]["path"]).is_file())

    def test_core_failure_skips_gpu_probe(self):
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(pa.bridge_main, "device_status", return_value=DEVICE), \
                 mock.patch.object(pa, "run_blender_canary", side_effect=RuntimeError("Blender pin mismatch")), \
                 mock.patch.object(pa, "run_gpu_probe") as gpu:
                result = pa.run_physical_acceptance(pathlib.Path(temp))

            self.assertEqual(result["status"], "CORE_FAILED")
            self.assertEqual(result["gpu"]["status"], "SKIPPED_CORE_FAILED")
            self.assertFalse(result["local_core_ready"])
            gpu.assert_not_called()

    def test_core_and_gpu_pass_remains_local_only(self):
        with tempfile.TemporaryDirectory() as temp:
            gpu_result = {"ready_for_gpu_render": True, "status": "GPU_RENDER_ROUTE_VERIFIED", "artifacts": {}}
            with mock.patch.object(pa.bridge_main, "device_status", return_value=DEVICE), \
                 mock.patch.object(pa, "run_blender_canary", return_value={"status": "CANARY_LOCAL_PASS"}), \
                 mock.patch.object(pa, "run_gpu_probe", return_value=gpu_result):
                result = pa.run_physical_acceptance(pathlib.Path(temp))

            self.assertEqual(result["status"], "CORE_PASS_GPU_PASS")
            self.assertTrue(result["local_core_ready"])
            self.assertTrue(result["local_gpu_render_ready"])
            self.assertFalse(result["ready_for_ai"])
            self.assertFalse(result["promotion_performed"])


if __name__ == "__main__":
    unittest.main()
