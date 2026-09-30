import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from algorithm.config import AlgorithmConfig
from algorithm.io import build_algorithm_inputs, load_capture_package
from algorithm.kalman import run_fixed_beta_kalman
from algorithm.run import run
from paper_bridge_simulation import package_builder
from paper_bridge_simulation.response import REFERENCE_RATE_HZ, simulate_response


class AlgorithmPipelineTest(unittest.TestCase):
    def test_paper_bridge_package_uses_algorithm_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "capture"
            result = Path(temporary) / "result.npz"
            package_builder.generate(package, duration_s=1.0, seed=2026)
            output, summary = run(package, result)
            self.assertTrue(output.is_file())
            payload = json.loads(summary.read_text(encoding="utf-8"))
            metadata = json.loads((package / "paper_response_metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["source_type"], "paper_parameterized_synthetic")
            self.assertEqual(json.loads((package / "status.json").read_text(encoding="utf-8"))["source_type"], "paper_bridge_simulation")
            self.assertEqual(payload["method"], "fixed_geometry_beta_structural_kalman")
            arrays = np.load(output)
            self.assertEqual(arrays["q_hat_m"].shape, (100,))
            self.assertEqual(arrays["selected_target_indices"].size, 5)

    def test_chirp_mode_expands_the_saved_loop_cube(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "capture"
            result = Path(temporary) / "chirp_result.npz"
            package_builder.generate(package, duration_s=1.0, seed=2026)
            output, summary = run(package, result, radar_mode="chirp")
            payload = json.loads(summary.read_text(encoding="utf-8"))
            arrays = np.load(output)
            self.assertEqual(payload["radar_mode"], "chirp")
            self.assertEqual(payload["radar_frames"], 100)
            self.assertEqual(payload["radar_samples"], 1600)
            self.assertEqual(arrays["q_hat_m"].shape, (1600,))
            self.assertEqual(arrays["radar_time_ns"].shape, (1600,))
            chirp = np.load(package / "radar" / "algorithm_input" / "chirp_cube.npy")
            adc = np.load(package / "radar" / "algorithm_input" / "adc_cube.npy")
            self.assertGreater(float(np.std(chirp[:, 1] - chirp[:, 0])), 0.0)
            self.assertTrue(np.allclose(adc, np.mean(chirp, axis=1)))

    def test_paper_response_has_consistent_acceleration_and_sampling_margin(self):
        time_s, displacement, acceleration, _ = simulate_response()
        self.assertEqual(time_s.size, round(4.0 * REFERENCE_RATE_HZ))
        self.assertAlmostEqual(float(np.max(np.abs(displacement))), 1.712e-3, places=9)
        dt = 1.0 / REFERENCE_RATE_HZ
        numerical_acceleration = np.gradient(np.gradient(displacement, dt), dt)
        interior = slice(10, -10)
        relative_error = np.linalg.norm(numerical_acceleration[interior] - acceleration[interior]) / np.linalg.norm(acceleration[interior])
        self.assertLess(relative_error, 2.0e-3)

    def test_cold_start_initializes_target_measurement_variances(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "capture"
            package_builder.generate(package, duration_s=1.0, seed=2026)
            capture = load_capture_package(package)
            radar, acceleration, _, radar_rate = build_algorithm_inputs(capture)
            residual = run_fixed_beta_kalman(
                radar,
                acceleration,
                AlgorithmConfig(sample_rate_hz=radar_rate, min_measurement_variance=1.0e-8),
            )
            self.assertGreater(np.ptp(residual.extra["initial_r"][radar.selected_indices]), 0.0)

            fixed = run_fixed_beta_kalman(
                radar,
                acceleration,
                AlgorithmConfig(sample_rate_hz=radar_rate, cold_start_r_mode="fixed"),
            )
            self.assertTrue(np.allclose(fixed.extra["initial_r"], radar.initial_r))


if __name__ == "__main__":
    unittest.main()
