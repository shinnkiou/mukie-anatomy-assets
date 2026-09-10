import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.gpu_probe import verify_gpu_report


def report(**overrides):
    value = {
        "schema_version": "ukie_blender_gpu_probe_v1",
        "status": "GPU_RENDER_ROUTE_PASS",
        "blender_version": "4.2.23 LTS",
        "chosen_backend": "CUDA",
        "selected_devices": [{"name": "Synthetic GPU", "type": "CUDA", "id": "CUDA_0", "use": True}],
        "cpu_devices_disabled": True,
        "scene_cycles_device": "GPU",
        "render": {"attempted": True, "completed": True, "byte_size": 4096},
        "hardware_utilization_sampled": False,
        "ready_for_gpu_render": True,
    }
    value.update(overrides)
    return value


def write_png_like(path: pathlib.Path):
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + (b"P" * 2048))


class GPUProbeTests(unittest.TestCase):
    def test_valid_non_cpu_render_route_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            png = pathlib.Path(temp) / "probe.png"
            write_png_like(png)
            result = verify_gpu_report(report(), png)
            self.assertEqual(result["status"], "GPU_RENDER_ROUTE_VERIFIED")
            self.assertTrue(result["ready_for_gpu_render"])
            self.assertFalse(result["hardware_utilization_sampled"])

    def test_cpu_fallback_blocks(self):
        value = report(cpu_devices_disabled=False)
        result = verify_gpu_report(value)
        self.assertEqual(result["status"], "GPU_RENDER_ROUTE_BLOCKED")
        self.assertFalse(result["ready_for_gpu_render"])

    def test_cpu_only_selection_blocks(self):
        value = report(selected_devices=[{"name": "CPU", "type": "CPU", "use": True}])
        result = verify_gpu_report(value)
        self.assertEqual(result["status"], "GPU_RENDER_ROUTE_BLOCKED")
        self.assertFalse(result["checks"]["non_cpu_selected"])

    def test_missing_render_png_blocks_when_path_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = pathlib.Path(temp) / "missing.png"
            result = verify_gpu_report(report(), missing)
            self.assertEqual(result["status"], "GPU_RENDER_ROUTE_BLOCKED")
            self.assertFalse(result["checks"]["render_png_present"])

    def test_hardware_utilization_cannot_be_overclaimed(self):
        value = report(hardware_utilization_sampled=True)
        result = verify_gpu_report(value)
        self.assertEqual(result["status"], "GPU_RENDER_ROUTE_BLOCKED")
        self.assertFalse(result["checks"]["hardware_utilization_not_overclaimed"])


if __name__ == "__main__":
    unittest.main()
