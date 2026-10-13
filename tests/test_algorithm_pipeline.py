import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from paper_bridge_simulation import package_builder
from paper_bridge_simulation.response import REFERENCE_RATE_HZ, simulate_response
from system.algorithm.config import AlgorithmConfig
from system.algorithm.frontend import extract_dbf_targets_streaming, range_angle_process
from system.algorithm.io import build_algorithm_inputs, load_capture_package
from system.algorithm.kalman import run_fixed_beta_kalman
from system.algorithm.run import run
from system.algorithm.selection import detect_target_bins


class AlgorithmPipelineTest(unittest.TestCase):
    def test_streaming_dbf_extraction_is_block_equivalent(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "capture"
            package_builder.generate(package, duration_s=1.0, seed=2026)
            capture = load_capture_package(package)
            first = range_angle_process(capture.adc_cube[:1], capture.frontend)
            ranges, angles, _ = detect_target_bins(first.cube, first.angle_axis_deg, max_candidates=5)
            streamed = extract_dbf_targets_streaming(
                capture.adc_cube, ranges, angles, capture.frontend, block_size=32
            )

            blocks = []
            for start in range(0, capture.adc_cube.shape[0], 32):
                end = min(capture.adc_cube.shape[0], start + 32)
                processed = range_angle_process(capture.adc_cube[start:end], capture.frontend)
                blocks.append(processed.cube[:, ranges, angles].T)
            expected = np.concatenate(blocks, axis=1)
            np.testing.assert_allclose(streamed.slow_time, expected)
            self.assertEqual(streamed.wrapped_phase_rad.shape, (5, 500))
            self.assertTrue(np.all(streamed.available_mask))

    def test_paper_bridge_package_uses_base_algorithm_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "capture"
            result = Path(temporary) / "result.npz"
            package_builder.generate(package, duration_s=1.0, seed=2026)
            output, summary = run(package, result)
            self.assertTrue(output.is_file())
            payload = json.loads(summary.read_text(encoding="utf-8"))
            metadata = json.loads((package / "paper_response_metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["source_type"], "paper_parameterized_synthetic")
            self.assertEqual(
                json.loads((package / "status.json").read_text(encoding="utf-8"))["source_type"],
                "paper_bridge_simulation",
            )
            self.assertEqual(payload["method"], "base_iq_circle_structural_kalman")
            self.assertNotIn("radar_mode", payload)
            arrays = np.load(output)
            self.assertEqual(arrays["q_hat_m"].shape, (500,))
            self.assertEqual(arrays["selected_target_indices"].size, 5)
            frame_ns = np.load(package / "sync" / "radar_frame_monotonic_ns.npy")
            np.testing.assert_array_equal(np.diff(frame_ns), np.full(499, 2_000_000))

    def test_paper_response_has_consistent_acceleration_and_sampling_margin(self):
        time_s, displacement, acceleration, _ = simulate_response()
        self.assertEqual(time_s.size, round(13.0 * REFERENCE_RATE_HZ))
        self.assertAlmostEqual(float(np.max(np.abs(displacement))), 1.712e-3, places=9)
        dt = 1.0 / REFERENCE_RATE_HZ
        numerical_acceleration = np.gradient(np.gradient(displacement, dt), dt)
        interior = slice(10, -10)
        relative_error = np.linalg.norm(
            numerical_acceleration[interior] - acceleration[interior]
        ) / np.linalg.norm(acceleration[interior])
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
